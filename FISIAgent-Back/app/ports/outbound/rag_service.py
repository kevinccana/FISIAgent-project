"""
RAGServicePort - Contrato para servicio de Retrieval-Augmented Generation

Este port define la interfaz para recuperar información contextual de documentos.
Cualquier implementación (ChromaDB, Pinecone, FAISS, etc.) debe cumplir este contrato.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class DocumentChunk:
    """Fragmento de documento recuperado."""
    content: str
    source: str
    relevance_score: float
    metadata: dict


class RAGServicePort(ABC):
    """
    Port de salida para servicios de RAG.
    
    Permite recuperar información contextual de documentos FISI-UNSM
    para enriquecer las respuestas del chatbot.
    """
    
    @abstractmethod
    def retrieve_context(self, query: str, top_k: int = 3) -> List[DocumentChunk]:
        """
        Recupera los fragmentos de documentos más relevantes para una consulta.
        
        Args:
            query: Pregunta o mensaje del usuario
            top_k: Número máximo de fragmentos a retornar (default: 3)
            
        Returns:
            Lista de fragmentos ordenados por relevancia (score descendente)
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Verifica si el servicio RAG está disponible.
        
        Returns:
            True si la base vectorial está cargada y lista, False en caso contrario
        """
        pass
