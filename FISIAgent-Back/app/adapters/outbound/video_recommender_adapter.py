"""
VideoRecommenderAdapter - Outbound Adapter (Arquitectura Hexagonal)

Implementa el port VideoRecommenderPort usando Gemini para selección inteligente.
"""
import logging
from typing import Optional
from app.core.domain.models import VideoRecommendation, RiskLevel
from app.ports.outbound.video_recommender import VideoRecommenderPort

logger = logging.getLogger(__name__)

# ── Catálogo de videos ────────────────────────────────────────────────────────
VIDEOS_AYUDA = [
    {
        "tipo": "respiracion",
        "titulo": "Ejercicio de Respiración 4-7-8",
        "descripcion": "Técnica de respiración para calmar la ansiedad en minutos",
        "url": "https://www.youtube.com/watch?v=EGO5m_DBzF8&t=96s",
        "duracion": "5 min",
        "situacion": "ansiedad aguda, sensación de ahogo, falta de aire, taquicardia",
    },
    {
        "tipo": "mindfulness",
        "titulo": "Mindfulness para principiantes",
        "descripcion": "5 minutos de atención plena para reducir el estrés",
        "url": "https://www.youtube.com/watch?v=3oCC4NDgYrY&t=17s",
        "duracion": "5 min",
        "situacion": "estrés general, mente acelerada, pensamientos que no paran, preocupación",
    },
    {
        "tipo": "dormir",
        "titulo": "Meditación para dormir",
        "descripcion": "Relajación profunda para conciliar el sueño",
        "url": "https://www.youtube.com/watch?v=vFrHhwCOaW0",
        "duracion": "20 min",
        "situacion": "insomnio, dificultad para dormir, sueño, cansancio nocturno",
    },
    {
        "tipo": "relajacion",
        "titulo": "Sonidos de la naturaleza",
        "descripcion": "Ambientes relajantes para calmar la mente y el cuerpo",
        "url": "https://www.youtube.com/watch?v=7Ilu033ydSw",
        "duracion": "Libre",
        "situacion": "tensión, agobio, saturación, necesidad de calma y silencio",
    },
]


class VideoRecommenderAdapter(VideoRecommenderPort):
    """
    Adapter que recomienda videos de apoyo usando Gemini.
    """
    
    def __init__(self, llm_client):
        """
        Args:
            llm_client: Cliente de Gemini (google.genai.Client)
        """
        self.llm_client = llm_client
    
    def recommend_video(
        self,
        message: str,
        risk_level: RiskLevel
    ) -> Optional[VideoRecommendation]:
        """
        Recomienda un video según el mensaje y nivel de riesgo.
        
        Implementación del port VideoRecommenderPort.
        """
        # Solo recomendamos video para nivel moderado
        if risk_level != RiskLevel.MODERADO:
            return None
        
        try:
            video_dict = self._select_video_with_gemini(message)
            
            if video_dict:
                return VideoRecommendation(
                    tipo=video_dict["tipo"],
                    titulo=video_dict["titulo"],
                    descripcion=video_dict["descripcion"],
                    url=video_dict["url"],
                    duracion=video_dict["duracion"],
                    situacion=video_dict["situacion"]
                )
            
            # Fallback: video de mindfulness
            return self._get_default_video()
        
        except Exception as e:
            logger.warning(f"[VideoRecommender] Error al seleccionar video: {e}")
            return self._get_default_video()
    
    def _select_video_with_gemini(self, message: str) -> Optional[dict]:
        """Usa Gemini para elegir el video más apropiado"""
        try:
            from google.genai import types
            
            catalogo_str = "\n".join(
                f"- tipo: {v['tipo']} | situacion: {v['situacion']}"
                for v in VIDEOS_AYUDA
            )
            
            prompt = (
                f"Un usuario escribió: \"{message}\"\n\n"
                f"Elige el tipo de video de apoyo más apropiado.\n"
                f"Opciones:\n{catalogo_str}\n\n"
                f"Responde ÚNICAMENTE con el valor 'tipo', sin explicación."
            )
            
            response = self.llm_client.models.generate_content(
                model="gemini-3.1-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1),
            )
            
            tipo_elegido = response.text.strip().lower().replace(".", "")
            
            video = next((v for v in VIDEOS_AYUDA if v["tipo"] == tipo_elegido), None)
            return video
        
        except Exception:
            return None
    
    def _get_default_video(self) -> VideoRecommendation:
        """Video por defecto (mindfulness)"""
        video = VIDEOS_AYUDA[1]  # mindfulness
        return VideoRecommendation(
            tipo=video["tipo"],
            titulo=video["titulo"],
            descripcion=video["descripcion"],
            url=video["url"],
            duracion=video["duracion"],
            situacion=video["situacion"]
        )
