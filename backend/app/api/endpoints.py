from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.models import database_models, schemas
from app.services.auditor import analyze_pdf_fonts, analyze_text_quality
from app.services.report_generator import generate_pdf_report
from app.services.pdf_preservation import repair_pdf
from typing import Dict, List, Any
import logging
import os
import csv
import io
import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

def process_pdf_task(document_id: str, filepath: str):
    logger.info(f"=== INICIO DE AUDITORÍA === Documento: {document_id} | Archivo: {filepath}")
    db = SessionLocal()
    try:
        fonts_info = analyze_pdf_fonts(filepath)
        quality_info = analyze_text_quality(filepath)
        
        document = db.query(database_models.Document).filter(database_models.Document.id == document_id).first()
        if document:
            document.unicode_score = quality_info["unicode_score"]
            document.text_validity_score = quality_info["text_validity_score"]
            
            supported_fonts = sum(1 for f in fonts_info if f["esperanto_support"])
            font_score = (supported_fonts / len(fonts_info) * 100) if fonts_info else 100.0
            document.font_score = round(font_score, 2)
            
            document.overall_score = round((document.unicode_score + document.text_validity_score + document.font_score) / 3, 2)
            
            document.debug_info = {
                "page_count": quality_info["page_count"],
                "damaged_chars_count": quality_info["damaged_chars_count"],
                "esperanto_chars_count": quality_info["esperanto_chars_count"],
                "x_system_count": quality_info["x_system_count"],
                "text_length": quality_info["text_length"],
                "total_words": quality_info["total_words"],
                "first_50_words": quality_info["first_50_words"],
                "error_snippets": quality_info["error_snippets"],
                "damaged_instances_detailed": quality_info["damaged_instances_detailed"],
                "valid_chars_count": quality_info["valid_chars_count"],
                "classification": quality_info["classification"],
                "unicode_inventory": quality_info.get("unicode_inventory", []),
                "esperanto_audit": quality_info.get("esperanto_audit", []),
                "spanish_audit": quality_info.get("spanish_audit", []),
                "missing_esperanto_analysis": quality_info.get("missing_esperanto_analysis", []),
                "repair_preview": quality_info.get("repair_preview", {}),
                "unicode_debug": quality_info.get("unicode_debug", {}),
                "fonts_count": len(fonts_info),
                "glyph_corruption_metrics": {
                    "corrections_by_dictionary": sum(1 for item in quality_info.get("missing_esperanto_analysis", []) if item.get("detection_type") == "GLYPH_CORRUPTION_RECOVERY"),
                    "corrections_by_morphology": sum(1 for item in quality_info.get("missing_esperanto_analysis", []) if item.get("detection_type") == "MORPHOLOGICAL_RECOVERY"),
                    "corrections_by_similarity": sum(1 for item in quality_info.get("missing_esperanto_analysis", []) if item.get("detection_type") == "Similitud"),
                    "spanish_false_positives_discarded": sum(1 for item in quality_info.get("missing_esperanto_analysis", []) if item.get("detection_type") == "NO_VALID_CANDIDATE"),
                    "hunspell_resolved_unique": sum(1 for item in quality_info.get("missing_esperanto_analysis", []) if item.get("detection_type") == "HUNSPELL_RECOVERY"),
                    "hunspell_ambiguous": sum(1 for item in quality_info.get("missing_esperanto_analysis", []) if item.get("detection_type") == "HUNSPELL_AMBIGUOUS_CANDIDATES"),
                    "hunspell_no_candidates": sum(1 for item in quality_info.get("missing_esperanto_analysis", []) if item.get("detection_type") == "NO_VALID_CANDIDATE"),
                    "frequency_resolved": sum(1 for item in quality_info.get("missing_esperanto_analysis", []) if item.get("detection_type") == "FREQUENCY_RECOVERY"),
                    "frequency_low_confidence_warnings": sum(1 for item in quality_info.get("missing_esperanto_analysis", []) if item.get("detection_type") == "FREQUENCY_RECOVERY" and item.get("confidence", 0) == 0.60),
                    "unresolved_ambiguous": sum(1 for item in quality_info.get("missing_esperanto_analysis", []) if item.get("detection_type") in ["AMBIGUOUS_CANDIDATES", "HUNSPELL_AMBIGUOUS_CANDIDATES"]),
                    "unresolved_no_candidate": sum(1 for item in quality_info.get("missing_esperanto_analysis", []) if item.get("detection_type") == "NO_VALID_CANDIDATE"),
                    "unresolved_words": sum(1 for item in quality_info.get("missing_esperanto_analysis", []) if not item.get("suggestion")),
                    "variant_i_detected": sum(1 for item in quality_info.get("missing_esperanto_analysis", []) if "I" in item.get("word", "")),
                    "corrections_approved": sum(1 for item in quality_info.get("missing_esperanto_analysis", []) if item.get("confidence", 0) >= 0.85),
                    "suggestions": {item["word"]: item["suggestion"] for item in quality_info.get("missing_esperanto_analysis", []) if item.get("suggestion") and item.get("confidence", 0) >= 0.85},
                    "ambiguity_catalogue": [{"word": item["word"], "candidates": item["ambiguous_candidates"], "count": len(item["ambiguous_candidates"])} for item in quality_info.get("missing_esperanto_analysis", []) if item.get("detection_type") == "FREQUENCY_RECOVERY"],
                    "corrections_injected": 0
                }
            }
            
            for f_info in fonts_info:
                db_font = database_models.FontAudit(
                    document_id=document.id,
                    font_name=f_info["font_name"],
                    page_count=f_info["page_count"],
                    unicode_support=f_info["unicode_support"],
                    esperanto_support=f_info["esperanto_support"]
                )
                db.add(db_font)
                
            document.status = "audited"
            db.commit()
            logger.info(f"=== FIN DE AUDITORÍA === Documento {document_id} auditado exitosamente.")
    except Exception as e:
        logger.error(f"Error procesando documento {document_id}: {e}", exc_info=True)
        document = db.query(database_models.Document).filter(database_models.Document.id == document_id).first()
        if document:
            document.status = "error"
            db.commit()
    finally:
        db.close()

@router.post("/projects/{project_id}/documents", response_model=schemas.DocumentSchema)
def upload_document(
    project_id: str, 
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    logger.info(f"=== RECIBIENDO ARCHIVO === Proyecto: {project_id} | Nombre: {file.filename}")
    os.makedirs("uploads", exist_ok=True)
    filepath = f"uploads/{file.filename}"
    
    file_bytes = file.file.read()
    file_size = len(file_bytes)
    logger.info(f"Archivo leído en memoria. Tamaño: {file_size} bytes")
    
    with open(filepath, "wb") as buffer:
        buffer.write(file_bytes)
        
    logger.info(f"Archivo guardado exitosamente en: {filepath}")
    document = database_models.Document(
        project_id=project_id,
        filename=file.filename,
        original_file_path=filepath,
        status="processing"
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    background_tasks.add_task(process_pdf_task, document.id, filepath)
    
    return document

@router.get("/documents/{document_id}", response_model=schemas.DocumentSchema)
def get_document(document_id: str, db: Session = Depends(get_db)):
    return db.query(database_models.Document).filter(database_models.Document.id == document_id).first()

@router.get("/documents/{document_id}/report/pdf")
def get_document_report_pdf(document_id: str, db: Session = Depends(get_db)):
    document = db.query(database_models.Document).filter(database_models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
        
    pdf_buffer = generate_pdf_report(document)
    return StreamingResponse(
        pdf_buffer, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"attachment; filename=repair_report_{document.filename}.pdf"}
    )

class RepairRequest(BaseModel):
    approved_corrections: Dict[str, str]

@router.post("/documents/{document_id}/repair")
def run_repair_engine(document_id: str, request: RepairRequest, db: Session = Depends(get_db)):
    document = db.query(database_models.Document).filter(database_models.Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not document.debug_info:
        raise HTTPException(status_code=400, detail="Document has no debug info to repair from")
        
    try:
        repaired_path, metrics = repair_pdf(document.original_file_path, request.approved_corrections)
        document.corrected_file_path = repaired_path
        if metrics.get("semantic_validation_passed"):
            document.status = "repaired"
            success = True
            msg = "PDF reparado y validado exitosamente"
        else:
            document.status = "repair_failed_validation"
            success = False
            msg = "PDF reparado pero falló validación semántica"
        # Guardar métricas en debug_info
        debug_info = dict(document.debug_info) if document.debug_info else {}
        debug_info["preservation_metrics"] = metrics
        
        # Calculate injected for GLYPH_CORRUPTION_RECOVERY
        if "glyph_corruption_metrics" in debug_info:
            # How to know how many were injected?
            # We injected request.approved_corrections
            # How many of those were variant I?
            injected_variant_i = sum(1 for word in request.approved_corrections.keys() if "I" in word)
            debug_info["glyph_corruption_metrics"]["corrections_injected"] = injected_variant_i
            
        document.debug_info = debug_info
        
        db.commit()
        return {"success": success, "message": msg, "metrics": metrics}
    except Exception as e:
        logger.error(f"Error repairing document {document_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error repairing PDF: {str(e)}")

@router.get("/documents/{document_id}/download-repaired")
def download_repaired_pdf(document_id: str, db: Session = Depends(get_db)):
    document = db.query(database_models.Document).filter(database_models.Document.id == document_id).first()
    if not document or not document.corrected_file_path:
        raise HTTPException(status_code=404, detail="Repaired PDF not found")
        
    if not os.path.exists(document.corrected_file_path):
        raise HTTPException(status_code=404, detail="Repaired PDF file is missing on disk")
        
    def iterfile():
        with open(document.corrected_file_path, mode="rb") as file_like:
            yield from file_like

    # Formatear el nombre usando la convención del usuario
    original_basename, original_ext = os.path.splitext(document.filename)
    download_filename = f"{original_basename}_repaired{original_ext}"

    return StreamingResponse(
        iterfile(), 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"attachment; filename={download_filename}"}
    )

@router.get("/documents/{document_id}/download-reviewed")
def download_reviewed_pdf(document_id: str, db: Session = Depends(get_db)):
    document = db.query(database_models.Document).filter(database_models.Document.id == document_id).first()
    if not document or not document.reviewed_file_path:
        raise HTTPException(status_code=404, detail="Reviewed PDF not found")
        
    if not os.path.exists(document.reviewed_file_path):
        raise HTTPException(status_code=404, detail="Reviewed PDF file is missing on disk")
        
    def iterfile():
        with open(document.reviewed_file_path, mode="rb") as file_like:
            yield from file_like

    # Formatear el nombre usando la convención del usuario
    original_basename, original_ext = os.path.splitext(document.filename)
    download_filename = f"{original_basename}_repaired_reviewed{original_ext}"

    return StreamingResponse(
        iterfile(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={download_filename}"}
    )

@router.post("/projects/{project_id}/documents/batch", response_model=List[schemas.DocumentSchema])
def upload_document_batch(
    project_id: str,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    logger.info(f"=== INICIANDO BATCH UPLOAD === Proyecto: {project_id} | Archivos: {len(files)}")
    os.makedirs("uploads", exist_ok=True)
    docs = []
    for file in files:
        filepath = f"uploads/{file.filename}"
        file_bytes = file.file.read()
        with open(filepath, "wb") as buffer:
            buffer.write(file_bytes)
            
        document = database_models.Document(
            project_id=project_id,
            filename=file.filename,
            original_file_path=filepath,
            status="processing"
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        background_tasks.add_task(process_pdf_task, document.id, filepath)
        docs.append(document)
        
    return docs

@router.get("/projects/{project_id}/batch-report")
def get_batch_report(project_id: str, db: Session = Depends(get_db)):
    project = db.query(database_models.Project).filter(database_models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    documents = db.query(database_models.Document).filter(database_models.Document.project_id == project_id).all()
    
    total_docs = len(documents)
    processed_docs = sum(1 for d in documents if d.status in ["audited", "repaired", "repair_failed_validation", "error"])
    
    total_applied = 0
    total_high_conf = 0
    total_low_conf = 0
    total_false_positives = 0
    
    docs_report = []
    
    for d in documents:
        metrics = {}
        if d.debug_info and "glyph_corruption_metrics" in d.debug_info:
            metrics = d.debug_info["glyph_corruption_metrics"]
            total_applied += metrics.get("corrections_injected", 0)
            total_high_conf += metrics.get("corrections_approved", 0)
            total_low_conf += metrics.get("frequency_low_confidence_warnings", 0)
            total_false_positives += metrics.get("spanish_false_positives_discarded", 0)
            
        doc_info = {
            "id": d.id,
            "filename": d.filename,
            "status": d.status,
            "updated_at": d.updated_at.isoformat() if hasattr(d, 'updated_at') and d.updated_at else None,
            "has_repaired": bool(d.corrected_file_path and os.path.exists(d.corrected_file_path)),
            "has_reviewed": bool(d.reviewed_file_path and os.path.exists(d.reviewed_file_path)),
            "metrics": metrics
        }
        docs_report.append(doc_info)
        
    return {
        "project_id": project.id,
        "name": project.name,
        "total_documents": total_docs,
        "processed_documents": processed_docs,
        "total_corrections_applied": total_applied,
        "total_high_confidence": total_high_conf,
        "total_low_confidence_warnings": total_low_conf,
        "total_false_positives": total_false_positives,
        "documents": docs_report
    }

@router.get("/projects/{project_id}/export-csv")
def export_project_csv(project_id: str, db: Session = Depends(get_db)):
    project = db.query(database_models.Project).filter(database_models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    documents = db.query(database_models.Document).filter(database_models.Document.project_id == project_id).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["filename", "page", "original_word", "corrected_word", "confidence", "resolution_method", "injected", "low_confidence_warning"])
    
    for d in documents:
        if d.debug_info and "missing_esperanto_analysis" in d.debug_info:
            for item in d.debug_info["missing_esperanto_analysis"]:
                pages_str = "|".join(map(str, item.get("pages", [])))
                confidence = item.get("confidence", 0)
                injected = (d.status == "repaired" and confidence >= 0.85)
                low_conf = (confidence == 0.60)
                
                writer.writerow([
                    d.filename,
                    pages_str,
                    item.get("word", ""),
                    item.get("suggestion", ""),
                    confidence,
                    item.get("detection_type", ""),
                    injected,
                    low_conf
                ])
                
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=batch_report_{project_id}.csv"
    return response

@router.get("/projects/{project_id}/export-json")
def export_project_batch_json(project_id: str, db: Session = Depends(get_db)):
    # Reutilizamos el endpoint batch-report para obtener el objeto JSON
    report = get_batch_report(project_id, db)
    return report

def repair_single_document(document_id: str):
    db = SessionLocal()
    try:
        document = db.query(database_models.Document).filter(database_models.Document.id == document_id).first()
        if not document or document.status != "repairing":
            return
            
        approved_corrections = {}
        if document.debug_info and "missing_esperanto_analysis" in document.debug_info:
            for item in document.debug_info["missing_esperanto_analysis"]:
                if item.get("confidence", 0) >= 0.85 and item.get("suggestion"):
                    approved_corrections[item["word"]] = item["suggestion"]
                    
        repaired_path, metrics = repair_pdf(document.original_file_path, approved_corrections)
        document.corrected_file_path = repaired_path
        if metrics.get("semantic_validation_passed"):
            document.status = "repaired"
        else:
            document.status = "repair_failed_validation"
            
        debug_info = dict(document.debug_info) if document.debug_info else {}
        debug_info["preservation_metrics"] = metrics
        
        if "glyph_corruption_metrics" in debug_info:
            injected_variant_i = sum(1 for word in approved_corrections.keys() if "I" in word)
            debug_info["glyph_corruption_metrics"]["corrections_injected"] = injected_variant_i
            
        document.debug_info = debug_info
        db.commit()
    except Exception as e:
        logger.error(f"Error repairing batch doc {document_id}: {e}", exc_info=True)
        document = db.query(database_models.Document).filter(database_models.Document.id == document_id).first()
        if document:
            document.status = "error"
            db.commit()
    finally:
        db.close()

@router.post("/projects/{project_id}/repair-batch")
def repair_project_batch(project_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    project = db.query(database_models.Project).filter(database_models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    documents = db.query(database_models.Document).filter(database_models.Document.project_id == project_id, database_models.Document.status == "audited").all()
    
    for document in documents:
        document.status = "repairing"
        db.commit()
        background_tasks.add_task(repair_single_document, document.id)
        
    return {"message": f"Reparación encolada para {len(documents)} documentos"}

@router.get("/projects/{project_id}/low-confidence")
def get_low_confidence_warnings(project_id: str, db: Session = Depends(get_db)):
    project = db.query(database_models.Project).filter(database_models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    documents = db.query(database_models.Document).filter(database_models.Document.project_id == project_id).all()
    warnings = []
    
    for d in documents:
        if d.debug_info and "missing_esperanto_analysis" in d.debug_info:
            for item in d.debug_info["missing_esperanto_analysis"]:
                if item.get("confidence", 0) == 0.60:
                    warnings.append({
                        "document_id": d.id,
                        "filename": d.filename,
                        "word": item.get("word"),
                        "suggestion": item.get("suggestion"),
                        "candidates": item.get("ambiguous_candidates", []),
                        "pages": item.get("pages", []),
                        "snippet": item.get("snippet", "")
                    })
    return {"warnings": warnings}

class ReviewRequest(BaseModel):
    decisions: List[Dict[str, Any]] # [{"document_id": "...", "word": "...", "decision": "approved"|"rejected"|"edited", "final_word": "..."}]

def apply_reviewed_document(document_id: str, reviewed_decisions: List[Dict[str, Any]]):
    db = SessionLocal()
    try:
        document = db.query(database_models.Document).filter(database_models.Document.id == document_id).first()
        if not document:
            return
            
        approved_corrections = {}
        audit_log = []
        timestamp = datetime.datetime.utcnow().isoformat()
        
        if document.debug_info and "missing_esperanto_analysis" in document.debug_info:
            for item in document.debug_info["missing_esperanto_analysis"]:
                if item.get("confidence", 0) >= 0.85 and item.get("suggestion"):
                    approved_corrections[item["word"]] = item["suggestion"]
                    
        for dec in reviewed_decisions:
            audit_log.append({
                "original_word": dec["word"],
                "suggested_word": dec.get("suggestion", ""),
                "user_decision": dec["decision"],
                "final_word": dec.get("final_word", ""),
                "timestamp": timestamp
            })
            if dec["decision"] in ["approved", "edited"] and dec.get("final_word"):
                approved_corrections[dec["word"]] = dec["final_word"]
                
        # Generate reviewed file from ORIGINAL file (not the repaired one)
        repaired_path, metrics = repair_pdf(document.original_file_path, approved_corrections)
        
        # Rename to _repaired_reviewed.pdf
        original_basename, original_ext = os.path.splitext(document.original_file_path)
        reviewed_path = f"{original_basename}_repaired_reviewed{original_ext}"
        os.rename(repaired_path, reviewed_path)
        
        document.reviewed_file_path = reviewed_path
        
        debug_info = dict(document.debug_info) if document.debug_info else {}
        debug_info["manual_review_audit"] = debug_info.get("manual_review_audit", []) + audit_log
        
        document.debug_info = debug_info
        document.status = "reviewed"
        db.commit()
    except Exception as e:
        logger.error(f"Error applying review to doc {document_id}: {e}", exc_info=True)
    finally:
        db.close()

@router.post("/projects/{project_id}/review-low-confidence")
def review_low_confidence(project_id: str, request: ReviewRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    project = db.query(database_models.Project).filter(database_models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    doc_groups = {}
    for dec in request.decisions:
        doc_groups.setdefault(dec["document_id"], []).append(dec)
        
    for doc_id, decisions in doc_groups.items():
        background_tasks.add_task(apply_reviewed_document, doc_id, decisions)
        
    return {"message": f"Revisión encolada para {len(doc_groups)} documentos."}
