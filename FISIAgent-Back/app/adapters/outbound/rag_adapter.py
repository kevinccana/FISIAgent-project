"""
RAGAdapter - Implementación de RAG con ChromaDB + LangChain

Implementa el RAGServicePort usando:
- ChromaDB: Base de datos vectorial para almacenar embeddings
- sentence-transformers: Modelo 'paraphrase-multilingual-MiniLM-L12-v2' para embeddings en español
- LangChain: Pipeline de carga y chunking de documentos
"""
import logging
from pathlib import Path
from typing import List
from app.ports.outbound.rag_service import RAGServicePort, DocumentChunk
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class RAGAdapter(RAGServicePort):
    """
    Adapter que implementa RAG con ChromaDB.
    
    Flujo:
    1. Carga documentos desde app/docs/fisi/
    2. Divide en chunks de ~500 caracteres con overlap
    3. Genera embeddings con modelo multilingüe
    4. Almacena en ChromaDB (persistido en disco)
    5. Recupera chunks relevantes con similarity search
    """
    
    def __init__(self, docs_path: str = "app/docs/fisi", persist_directory: str = "chroma_db"):
        """
        Inicializa el adapter RAG.
        
        Args:
            docs_path: Directorio con documentos FISI-UNSM (.txt)
            persist_directory: Directorio para persistir la base vectorial
        """
        self.docs_path = Path(docs_path)
        self.persist_directory = persist_directory
        self.vectorstore = None
        self._is_initialized = False
        
        # Configuración del modelo de embeddings
        # paraphrase-multilingual-MiniLM-L12-v2: 118M parámetros, optimizado para español
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'},  # Cambiar a 'cuda' si hay GPU
            encode_kwargs={'normalize_embeddings': True}
        )
        
        logger.info(f"RAGAdapter inicializado. Docs: {self.docs_path}")
    
    def load_documents(self):
        """
        Carga y procesa documentos FISI-UNSM.
        
        Pasos:
        1. Carga archivos .txt del directorio
        2. Divide en chunks con RecursiveCharacterTextSplitter
        3. Crea/carga ChromaDB con embeddings
        """
        try:
            # 1. Cargar documentos
            logger.info(f"Cargando documentos desde {self.docs_path}...")
            loader = DirectoryLoader(
                str(self.docs_path),
                glob="**/*.txt",
                loader_cls=TextLoader,
                loader_kwargs={'encoding': 'utf-8'}
            )
            documents = loader.load()
            
            if not documents:
                logger.warning(f"No se encontraron documentos en {self.docs_path}")
                return
            
            logger.info(f"✓ Cargados {len(documents)} documentos")
            
            # 2. Dividir en chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,          # Tamaño de chunk (caracteres)
                chunk_overlap=50,        # Overlap para mantener contexto
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            chunks = text_splitter.split_documents(documents)
            logger.info(f"✓ Generados {len(chunks)} chunks")
            
            # 3. Crear/cargar ChromaDB
            logger.info("Creando base vectorial con ChromaDB...")
            self.vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            self.vectorstore.persist()
            
            self._is_initialized = True
            logger.info("✅ RAG inicializado correctamente")
            
        except Exception as e:
            logger.error(f"Error al cargar documentos RAG: {e}")
            self._is_initialized = False
    
    def retrieve_context(self, query: str, top_k: int = 3) -> List[DocumentChunk]:
        """
        Recupera fragmentos relevantes para la consulta del usuario.
        
        Args:
            query: Pregunta del usuario (ej: "¿Cuántos créditos mínimos debo llevar?")
            top_k: Número de chunks a retornar
            
        Returns:
            Lista de DocumentChunk ordenados por relevancia
        """
        if not self.is_available():
            logger.warning("RAG no disponible, retornando lista vacía")
            return []
        
        try:
            # Búsqueda por similitud en ChromaDB
            results = self.vectorstore.similarity_search_with_relevance_scores(
                query=query,
                k=top_k
            )
            
            # Convertir a DocumentChunk
            chunks = []
            for doc, score in results:
                chunk = DocumentChunk(
                    content=doc.page_content,
                    source=doc.metadata.get('source', 'desconocido'),
                    relevance_score=score,
                    metadata=doc.metadata
                )
                chunks.append(chunk)
            
            logger.info(f"RAG: Recuperados {len(chunks)} chunks para '{query[:50]}...'")
            return chunks
            
        except Exception as e:
            logger.error(f"Error en retrieve_context: {e}")
            return []
    
    def is_available(self) -> bool:
        """Verifica si RAG está listo."""
        return self._is_initialized and self.vectorstore is not None
