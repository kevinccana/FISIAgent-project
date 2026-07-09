"""
ChatRouter - Inbound Adapter (Arquitectura Hexagonal)

Expone el caso de uso ProcessConversationUseCase a través de FastAPI.
Este adapter NO contiene lógica de negocio, solo traduce entre HTTP y el dominio.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from app.core.domain.models import Message
from app.core.domain.exceptions import DomainException
from app.ports.inbound.chat_service import ChatServicePort

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Modelos Pydantic (DTOs) ───────────────────────────────────────────────────
class ChatMessageDTO(BaseModel):
    """DTO para mensajes de chat (capa de presentación)"""
    role: str
    text: str


class ChatRequestDTO(BaseModel):
    """DTO para peticiones de chat"""
    history: List[ChatMessageDTO]


class VideoDTO(BaseModel):
    """DTO para videos de apoyo"""
    tipo: str
    titulo: str
    descripcion: str
    url: str
    duracion: str


class ChatResponseDTO(BaseModel):
    """DTO para respuestas de chat"""
    respuesta: str
    nivel_riesgo: str
    video_sugerido: VideoDTO | None
    probabilidades: dict


# ── Inyección de dependencias ─────────────────────────────────────────────────
# Esta variable será configurada en main.py con el caso de uso inicializado
_chat_service: ChatServicePort | None = None


def set_chat_service(service: ChatServicePort):
    """Configura el servicio de chat (llamado desde main.py)"""
    global _chat_service
    _chat_service = service


def get_chat_service() -> ChatServicePort:
    """Dependency para inyectar el servicio en los endpoints"""
    if _chat_service is None:
        raise HTTPException(
            status_code=500,
            detail="Chat service no inicializado"
        )
    return _chat_service


# ── Endpoints ──────────────────────────────────────────────────────────────────
@router.post("/chatai", response_model=ChatResponseDTO)
async def chat_endpoint(
    request: ChatRequestDTO,
    chat_service: ChatServicePort = Depends(get_chat_service)
):
    """
    Endpoint principal de chat con IA.
    
    Arquitectura Hexagonal:
    - Este adapter traduce de HTTP (DTOs) a dominio (Message)
    - Llama al caso de uso (chat_service.process_conversation)
    - Traduce la respuesta del dominio a HTTP (DTOs)
    """
    try:
        # 1. Traducir DTOs → Dominio
        history_domain = [
            Message(role=msg.role, text=msg.text)
            for msg in request.history
        ]
        
        # 2. Llamar al caso de uso (lógica de negocio)
        response_domain = await chat_service.process_conversation(history_domain)
        
        # 3. Traducir Dominio → DTOs
        video_dto = None
        if response_domain.video_sugerido:
            v = response_domain.video_sugerido
            video_dto = VideoDTO(
                tipo=v.tipo,
                titulo=v.titulo,
                descripcion=v.descripcion,
                url=v.url,
                duracion=v.duracion
            )
        
        return ChatResponseDTO(
            respuesta=response_domain.respuesta,
            nivel_riesgo=response_domain.nivel_riesgo.value,
            video_sugerido=video_dto,
            probabilidades=response_domain.probabilidades
        )
    
    except DomainException as e:
        logger.error(f"Error de dominio: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )
