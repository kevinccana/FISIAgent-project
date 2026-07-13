"""
GeminiAdapter - Outbound Adapter (Arquitectura Hexagonal)

Implementa el port LLMServicePort usando Google Gemini 2.5 Flash.
"""
import os
import logging
from typing import List
from app.core.domain.models import Message
from app.core.domain.exceptions import LLMServiceError
from app.ports.outbound.llm_service import LLMServicePort

logger = logging.getLogger(__name__)


class GeminiAdapter(LLMServicePort):
    """
    Adapter que implementa generación de texto usando Gemini.
    """
    
    def __init__(self, api_key: str):
        """
        Args:
            api_key: API key de Google Gemini
        """
        if not api_key:
            raise LLMServiceError("API key de Gemini no proporcionada")
        
        self.api_key = api_key
        self._client = None
    
    def _get_client(self):
        """Lazy initialization del cliente"""
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except ImportError:
                raise LLMServiceError("google-genai no está instalado")
            except Exception as e:
                raise LLMServiceError(f"Error al crear cliente Gemini: {str(e)}")
        return self._client
    
    async def generate_response(
        self,
        history: List[Message],
        system_instruction: str
    ) -> str:
        """
        Genera una respuesta usando Gemini.
        
        Implementación del port LLMServicePort.
        """
        try:
            from google.genai import types
            
            client = self._get_client()
            
            # Convertir historial al formato de Gemini
            contents = [
                types.Content(
                    role=msg.role,
                    parts=[types.Part.from_text(text=msg.text)],
                )
                for msg in history
            ]
            
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
            )
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=config,
            )
            
            return response.text
        
        except Exception as e:
            logger.error(f"[Gemini] Error al generar respuesta: {e}")
            raise LLMServiceError(f"Error al generar respuesta: {str(e)}")
    
    def is_available(self) -> bool:
        """Verifica si el servicio está disponible"""
        try:
            self._get_client()
            return True
        except:
            return False

    def check_connection(self) -> dict:
        """
        Verifica que la API key funcione de verdad contra los servidores de Gemini
        (a diferencia de `is_available()`, que solo construye el cliente localmente
        y no detecta una key inválida o sin cupo).

        Usa `count_tokens`, la llamada más liviana disponible -- no genera texto,
        solo confirma que la key es válida y que el modelo responde.

        Returns:
            {"ok": True} si la key funciona, o
            {"ok": False, "detail": "..."} con el motivo (401, 429 sin cupo, etc.)
        """
        try:
            client = self._get_client()
            client.models.count_tokens(model="gemini-2.5-flash", contents="ping")
            return {"ok": True, "detail": None}
        except Exception as e:
            logger.warning(f"[Gemini] check_connection falló: {e}")
            return {"ok": False, "detail": str(e)}
