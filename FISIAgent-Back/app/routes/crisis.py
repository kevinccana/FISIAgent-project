from fastapi import APIRouter
from pydantic import BaseModel
from app.services.nlp import detectar_crisis

router = APIRouter()

class CrisisRequest(BaseModel):
    message: str

@router.post("/crisis")
def crisis(req: CrisisRequest):

    es_crisis = detectar_crisis(req.message)

    if es_crisis:
        return {
            "crisis": True,
            "mensaje": "Llama a la Línea 113 opción 5 o busca ayuda inmediata."
        }

    return {"crisis": False}