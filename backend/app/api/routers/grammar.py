from fastapi import APIRouter

router = APIRouter()

@router.get("/rules")
def list_rules():
    return {"status": "not_implemented", "module": "Gramatiko"}
