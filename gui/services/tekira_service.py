import logging
from gui.models import DocumentJob, RepairResult, ReviewItem, DocumentSourceType
from language_engine.auditor import analyze_text_quality, analyze_raw_text

logger = logging.getLogger("studio.tekira_service")

class TekiraService:
    def __init__(self):
        logger.info("TekiraService init. Link to language_engine ready.")

    def analyze_document(self, job: DocumentJob) -> RepairResult:
        logger.info(f"TekiraService run: {job.id}")
        
        try:
            if job.source_type == DocumentSourceType.PDF:
                if not job.filepath: raise ValueError("PDF needs filepath")
                data = analyze_text_quality(job.filepath)
            elif job.source_type == DocumentSourceType.TXT:
                if not job.filepath: raise ValueError("TXT needs filepath")
                with open(job.filepath, 'r', encoding='utf-8') as f:
                    text = f.read()
                if not text.strip(): raise ValueError("TXT file is empty")
                data = analyze_raw_text(text)
            elif job.source_type == DocumentSourceType.CLIPBOARD:
                if not job.content or not job.content.strip():
                    raise ValueError("Clipboard content empty")
                data = analyze_raw_text(job.content)
            else:
                raise ValueError("Unknown source type")

            # Map to RepairResult
            items = []
            for m in data.get("missing_esperanto_analysis", []):
                if m.get("detection_type") in ["Jugxanto_ManualReview", "UNRESOLVED_CORRUPTION", "AMBIGUOUS_CANDIDATES", "NO_VALID_CANDIDATE"]:
                    items.append(ReviewItem(
                        original_word=m.get("word", ""),
                        context=m.get("snippet", ""),
                        candidates=[{"word": c, "score": 1.0} for c in m.get("ambiguous_candidates", [])]
                    ))

            success = True
            mr_req = len(items)
            return RepairResult(success=success, manual_reviews_required=mr_req, items=items)

        except Exception as e:
            logger.error(f"Tekira engine fail: {e}", exc_info=True)
            raise e
