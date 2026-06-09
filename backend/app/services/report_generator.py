import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import os

font_path = os.path.join(os.path.dirname(__file__), '..', '..', 'NotoSans-Regular.ttf')
has_noto = os.path.exists(font_path)
if has_noto:
    try:
        pdfmetrics.registerFont(TTFont('NotoSans', font_path))
    except Exception as e:
        has_noto = False

# Nota: Si NotoSans falla, se usará Helvetica que no soporta UTF-8 completo.

def generate_pdf_report(document) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    
    font_name = 'NotoSans' if has_noto else 'Helvetica'
    font_bold = 'NotoSans' if has_noto else 'Helvetica-Bold'
    
    title_style = styles['Heading1']
    if has_noto: title_style.fontName = font_bold
    
    h2_style = styles['Heading2']
    if has_noto: h2_style.fontName = font_bold
    
    normal_style = styles['Normal']
    if has_noto: normal_style.fontName = font_name
    
    mono_style = ParagraphStyle('Mono', parent=styles['Normal'], fontName='NotoSans' if has_noto else 'Courier', fontSize=9)
    
    story = []
    
    # 1. Header
    story.append(Paragraph(f"Esperanto PDF Repair - Audit Report", title_style))
    story.append(Spacer(1, 12))
    
    info_data = [
        ["Nombre del PDF:", document.filename],
        ["Document ID:", document.id],
        ["Fecha de Análisis:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ["Esperanto Integrity Score:", f"{document.overall_score or 0}%"]
    ]
    t_info = Table(info_data, colWidths=[150, 350])
    t_info.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), font_bold),
        ('TEXTCOLOR', (1,0), (1,-1), colors.darkblue),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 20))
    
    debug_info = document.debug_info or {}
    
    # 2. Fuentes
    story.append(Paragraph("1. Fuentes Detectadas", h2_style))
    fonts_data = [["Fuente", "Páginas", "Unicode OK", "Esperanto OK"]]
    for f in document.fonts:
        fonts_data.append([
            f.font_name, 
            str(f.page_count), 
            "Sí" if f.unicode_support else "No", 
            "Sí" if f.esperanto_support else "No"
        ])
    if len(fonts_data) > 1:
        t_fonts = Table(fonts_data, colWidths=[200, 100, 100, 100])
        t_fonts.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,-1), font_name),
            ('FONTNAME', (0,0), (-1,0), font_bold),
            ('GRID', (0,0), (-1,-1), 1, colors.lightgrey),
        ]))
        story.append(t_fonts)
    else:
        story.append(Paragraph("No se encontraron fuentes.", normal_style))
    story.append(Spacer(1, 20))
    
    # 3. Unicode & Esperanto Stats
    story.append(Paragraph("2. Estadísticas de Caracteres", h2_style))
    ud = debug_info.get("unicode_debug", {})
    stats_data = [
        ["Total Caracteres ASCII:", str(ud.get("total_ascii", 0))],
        ["Total Caracteres No-ASCII:", str(ud.get("total_no_ascii", 0))]
    ]
    t_stats = Table(stats_data, colWidths=[200, 300])
    t_stats.setStyle(TableStyle([('FONTNAME', (0,0), (-1,-1), font_name)]))
    story.append(t_stats)
    story.append(Spacer(1, 10))
    
    # Esperanto found
    esp_audit = debug_info.get("esperanto_audit", [])
    found_esp = [e for e in esp_audit if e.get("count", 0) > 0]
    if found_esp:
        story.append(Paragraph("Caracteres Esperanto válidos encontrados:", normal_style))
        esp_data = [["Carácter", "Frecuencia"]]
        for e in found_esp:
            esp_data.append([e["char"], str(e["count"])])
        t_esp = Table(esp_data, colWidths=[100, 100])
        t_esp.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), font_name),
            ('GRID', (0,0), (-1,-1), 1, colors.lightgrey)
        ]))
        story.append(t_esp)
    else:
        story.append(Paragraph("No se encontraron caracteres Esperanto válidos (posible daño de codificación).", normal_style))
    story.append(Spacer(1, 20))
    
    # 4. Problemas y Correcciones
    story.append(Paragraph("3. Problemas Detectados y Correcciones Sugeridas", h2_style))
    missing = debug_info.get("missing_esperanto_analysis", [])
    if missing:
        missing_data = [["Original", "Sugerencia", "Unicode Generado", "Tipo", "Confianza"]]
        for m in missing[:30]: # Limit to 30 for PDF brevity
            missing_data.append([
                m["word"], 
                m["suggestion"], 
                m.get("unicode_breakdown", "-"),
                m.get("detection_type", ""), 
                f"{m['confidence']*100:.0f}%"
            ])
        t_miss = Table(missing_data, colWidths=[80, 80, 150, 70, 50])
        t_miss.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,-1), font_name),
            ('FONTNAME', (0,0), (-1,0), font_bold),
            ('GRID', (0,0), (-1,-1), 1, colors.lightgrey),
        ]))
        story.append(t_miss)
        if len(missing) > 30:
            story.append(Paragraph(f"... y {len(missing)-30} más.", normal_style))
    else:
        story.append(Paragraph("No se detectaron problemas de Esperanto.", normal_style))
    story.append(Spacer(1, 20))
    
    # 5. Repair Preview
    story.append(Paragraph("4. Repair Preview (Contexto)", h2_style))
    preview = debug_info.get("repair_preview", {})
    paragraphs = preview.get("paragraphs", [])
    if paragraphs:
        for p in paragraphs:
            story.append(Paragraph(f"<b>Original:</b> {p['original']}", mono_style))
            story.append(Spacer(1, 4))
            story.append(Paragraph(f"<b>Sugerido:</b> {p['corrected']}", mono_style))
            story.append(Spacer(1, 10))
    else:
        story.append(Paragraph("No hay vistas previas de contexto.", normal_style))
        
    doc.build(story)
    buffer.seek(0)
    return buffer
