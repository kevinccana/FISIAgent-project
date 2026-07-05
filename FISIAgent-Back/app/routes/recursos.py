from fastapi import APIRouter
from app.M04_GestorRecursos import ResourceManager

router = APIRouter()

manager = ResourceManager()

@router.get("/recursos")
def recursos(mensaje: str):

    data = manager.buscar_por_distrito(mensaje)

    return {
        "recursos": data if data else [],
        "found": data is not None
    }