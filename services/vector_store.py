"""
Gerenciador do banco de dados vetorial ChromaDB.
Permite armazenar e buscar documentos usando embeddings.
"""
import chromadb
from openai import OpenAI
from typing import List, Optional
from core.config import get_settings

settings = get_settings()


class VectorStore:
    """Gerenciador de busca semântica usando ChromaDB e OpenAI embeddings."""
    
    def __init__(self):
        # Inicializa o cliente ChromaDB com persistência local
        self.chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY
        )
        
        # Cria ou obtém a coleção principal
        self.collection = self.chroma_client.get_or_create_collection(
            name="knowledge_base",
            metadata={"description": "Base de conhecimento do Notion"}
        )
        
        # Cliente OpenAI para geração de embeddings
        self.openai_client = None
        if settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Gera um embedding para o texto usando o modelo text-embedding-3-small.
        
        Args:
            text: Texto para gerar embedding
            
        Returns:
            Lista de floats representando o embedding
        """
        if not self.openai_client:
            raise ValueError("OpenAI API key não configurada")
        
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    def add_document(self, doc_id: str, text: str, metadata: Optional[dict] = None) -> None:
        """
        Adiciona um documento à base de conhecimento.
        
        Args:
            doc_id: ID único do documento
            text: Conteúdo do documento
            metadata: Metadados opcionais (título, fonte, etc.)
        """
        embedding = self._generate_embedding(text)
        
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata or {}]
        )
    
    def add_documents(self, doc_ids: List[str], texts: List[str], metadatas: Optional[List[dict]] = None) -> None:
        """
        Adiciona múltiplos documentos à base de conhecimento.
        
        Args:
            doc_ids: Lista de IDs únicos
            texts: Lista de conteúdos
            metadatas: Lista de metadados opcionais
        """
        embeddings = [self._generate_embedding(text) for text in texts]
        
        self.collection.add(
            ids=doc_ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas or [{}] * len(texts)
        )
    
    def search(self, query: str, n_results: int = 3) -> List[dict]:
        """
        Busca documentos relevantes para a consulta.
        
        Args:
            query: Pergunta ou consulta do usuário
            n_results: Número máximo de resultados
            
        Returns:
            Lista de documentos relevantes com scores
        """
        if not self.openai_client:
            return []
        
        query_embedding = self._generate_embedding(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Formata os resultados
        documents = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                documents.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else None
                })
        
        return documents
    
    def clear(self) -> None:
        """Limpa toda a base de conhecimento."""
        try:
            self.chroma_client.delete_collection("knowledge_base")
        except Exception:
            pass
        self.collection = self.chroma_client.get_or_create_collection(
            name="knowledge_base",
            metadata={"description": "Base de conhecimento do Notion"}
        )
    
    def count(self) -> int:
        """Retorna o número de documentos na base."""
        return self.collection.count()


# Inicialização lazy do vector store
_vector_store = None

def get_vector_store() -> VectorStore:
    """Retorna instância singleton do VectorStore."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store

# Para compatibilidade com código existente
vector_store = None
try:
    vector_store = VectorStore()
except Exception:
    pass
