from fastapi import APIRouter

router = APIRouter()

@router.get("/{word}")
def lookup_word(word: str):
    return {"status": "not_implemented", "module": "Radiko", "query": word}
