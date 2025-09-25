import sys
from pathlib import Path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from app.services.ingest_helpers import embed_texts
from typing import List, Tuple, Dict, Any, Optional
from app.db.session import get_db
from httpx import HTTPError
import logging

logger = logging.getLogger(__name__)

class RetrieverError(Exception):
    """Exception personnalisée pour les erreurs de Retriever"""
    def __init__(self, message: str, error_type: str = "UNKNOWN", details: dict = None):
        self.message = message
        self.error_type = error_type
        self.details = details or {}
        super().__init__(self.message)

class Retriever:
    def __init__(self, user_id: str):
        if not user_id:
            raise RetrieverError(
                "User ID is required and cannot be empty",
                error_type="INVALID_USER_ID",
                details={"user_id": user_id}
            )
        
        self.user_id = user_id
        
        try:
            self.db = get_db()
        except Exception as e:
            raise RetrieverError(
                f"Failed to initialize database connection: {str(e)}",
                error_type="DATABASE_CONNECTION_ERROR",
                details={"user_id": user_id, "original_error": str(e)}
            )
        
        try:
            self.embed_texts = embed_texts
        except Exception as e:
            raise RetrieverError(
                f"Failed to initialize embedding function: {str(e)}",
                error_type="EMBEDDING_INITIALIZATION_ERROR",
                details={"user_id": user_id, "original_error": str(e)}
            )

    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        try:
            if not texts:
                raise RetrieverError(
                    "Texts list cannot be empty for embedding",
                    error_type="EMPTY_TEXTS_LIST",
                    details={"texts": texts}
                )
            
            if not all(isinstance(text, str) for text in texts):
                raise RetrieverError(
                    "All texts must be strings",
                    error_type="INVALID_TEXT_TYPE",
                    details={"texts": texts}
                )
            
            return embed_texts(texts)
            
        except Exception as e:
            raise RetrieverError(
                f"Failed to embed texts: {str(e)}",
                error_type="EMBEDDING_ERROR",
                details={"texts": texts, "original_error": str(e)}
            )
    
    def retrieve_from_knowledge_chunks(self, query: str, k: int = 10, type: str = 'text', query_lang: str = 'simple') -> List[Dict[str, Any]]:
        """
        Retrieve from knowledge
        Args:
            query: The query to retrieve from knowledge
            k: The number of results to retrieve
            type: The type of search to perform
            query_lang: The language of the query
            
        Returns:
            List of dictionaries with content and score
        """
        try:
            if not query or not query.strip():
                raise RetrieverError(
                    "Query cannot be empty or only whitespace",
                    error_type="INVALID_QUERY",
                    details={"query": query}
                )
            
            if k <= 0:
                raise RetrieverError(
                    "Number of results (k) must be positive",
                    error_type="INVALID_K_VALUE",
                    details={"k": k}
                )
            
            if type not in ['text', 'vector', 'hybrid']:
                raise RetrieverError(
                    "Type must be one of: text, vector, hybrid",
                    error_type="INVALID_TYPE",
                    details={"type": type, "valid_types": ['text', 'vector', 'hybrid']}
                )
            
            if query_lang not in ['simple', 'french', 'english', 'spanish']:
                raise RetrieverError(
                    "Query language must be one of: simple, french, english, spanish",
                    error_type="INVALID_QUERY_LANG",
                    details={"query_lang": query_lang, "valid_langs": ['simple', 'french', 'english', 'spanish']}
                )
            
            db = get_db()
            result = None
            
            try:
                if type == 'text':
                    result = db.rpc(f'{type}_knowledge_chunks_search', {
                        'query_text': query,
                        'query_lang': query_lang,
                        'match_count': k,
                        'user_id': self.user_id
                    }).execute()
                elif type == 'vector':
                    try:
                        embedding = self._embed_texts([query])[0]
                    except RetrieverError:
                        raise
                    except Exception as e:
                        raise RetrieverError(
                            f"Failed to generate embedding for query: {str(e)}",
                            error_type="EMBEDDING_GENERATION_ERROR",
                            details={"query": query, "original_error": str(e)}
                        )
                    
                    result = db.rpc(f'{type}_knowledge_chunks_search', {
                        'query_text': query,
                        'query_embedding': embedding,
                        'match_count': k,
                        'user_id': self.user_id
                    }).execute()
                elif type == 'hybrid':
                    try:
                        embedding = self._embed_texts([query])[0]
                    except RetrieverError:
                        raise
                    except Exception as e:
                        raise RetrieverError(
                            f"Failed to generate embedding for query: {str(e)}",
                            error_type="EMBEDDING_GENERATION_ERROR",
                            details={"query": query, "original_error": str(e)}
                        )
                    
                    result = db.rpc(f'{type}_knowledge_chunks_search', {
                        'query_text': query,
                        'query_embedding': embedding,
                        'query_lang': query_lang,
                        'match_count': k,
                        'rrf_k': k,
                        'user_id': self.user_id
                    }).execute()
                
            except HTTPError as e:
                raise RetrieverError(
                    f"Database API error during knowledge chunks search: {str(e)}",
                    error_type="DATABASE_API_ERROR",
                    details={"query": query, "type": type, "user_id": self.user_id, "original_error": str(e)}
                )
            except Exception as e:
                raise RetrieverError(
                    f"Unexpected error during knowledge chunks search: {str(e)}",
                    error_type="SEARCH_ERROR",
                    details={"query": query, "type": type, "user_id": self.user_id, "original_error": str(e)}
                )
            
            if result and result[0]:
                logger.info(f"Retrieved {len(result[0])} knowledge chunks for query: '{query}'")
                return result[0]
            
            logger.info(f"No knowledge chunks found for query: '{query}'")
            return []
            
        except RetrieverError:
            raise
        except Exception as e:
            raise RetrieverError(
                f"Unexpected error in retrieve_from_knowledge_chunks: {str(e)}",
                error_type="UNEXPECTED_ERROR",
                details={"query": query, "user_id": self.user_id, "original_error": str(e)}
            )
    
    def retrieve_from_faq(self, query: str, k: int = 10, type: str = 'text', query_lang: str = 'simple') -> List[Dict[str, Any]]:
        """
        Retrieve from faq
        Args:
            query: The query to retrieve from faq
            k: The number of results to retrieve
            type: The type of search to perform
            query_lang: The language of the query
            
        Returns:
            List of dictionaries with content and score
        """
        try:
            if not query or not query.strip():
                raise RetrieverError(
                    "Query cannot be empty or only whitespace",
                    error_type="INVALID_QUERY",
                    details={"query": query}
                )
            
            if k <= 0:
                raise RetrieverError(
                    "Number of results (k) must be positive",
                    error_type="INVALID_K_VALUE",
                    details={"k": k}
                )
            
            if type not in ['text']:
                raise RetrieverError(
                    "Type must be one of: text",
                    error_type="INVALID_TYPE",
                    details={"type": type, "valid_types": ['text']}
                )
            
            if query_lang not in ['simple', 'french', 'english', 'spanish']:
                raise RetrieverError(
                    "Query language must be one of: simple, french, english, spanish",
                    error_type="INVALID_QUERY_LANG",
                    details={"query_lang": query_lang, "valid_langs": ['simple', 'french', 'english', 'spanish']}
                )
            
            db = get_db()
            result = None
            
            try:
                if type == 'text':
                    result = db.rpc(f'{type}_faq_search', {
                        'query_text': query,
                        'query_lang': query_lang,
                        'match_count': k,
                        'user_id': self.user_id
                    }).execute()
                
            except HTTPError as e:
                raise RetrieverError(
                    f"Database API error during FAQ search: {str(e)}",
                    error_type="DATABASE_API_ERROR",
                    details={"query": query, "type": type, "user_id": self.user_id, "original_error": str(e)}
                )
            except Exception as e:
                raise RetrieverError(
                    f"Unexpected error during FAQ search: {str(e)}",
                    error_type="SEARCH_ERROR",
                    details={"query": query, "type": type, "user_id": self.user_id, "original_error": str(e)}
                )
            
            if result and result[0]:
                logger.info(f"Retrieved {len(result[0])} FAQ results for query: '{query}'")
                return result[0]
            
            logger.info(f"No FAQ results found for query: '{query}'")
            return []
            
        except RetrieverError:
            raise
        except Exception as e:
            raise RetrieverError(
                f"Unexpected error in retrieve_from_faq: {str(e)}",
                error_type="UNEXPECTED_ERROR",
                details={"query": query, "user_id": self.user_id, "original_error": str(e)}
            )
        
    def retrieve_from_knowledge_and_faq(
        self, 
        query: str, 
        k: int = 10, 
        type_faq: str = 'text', 
        type_doc: str = 'hybrid', 
        query_lang: str = 'simple',
        faq_weight: float = 1.0,
        doc_weight: float = 1.0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve from knowledge and faq with customizable weights
        Args:
            query: The query to retrieve from knowledge and faq
            k: The number of results to retrieve
            type_faq: The type of search to perform for faq
            type_doc: The type of search to perform for document
            query_lang: The language of the query
            faq_weight: Weight to apply to FAQ results (higher values increase FAQ importance)
            doc_weight: Weight to apply to document results (higher values increase document importance)
            
        Returns:
            List of dictionaries with content and score
        """
        try:
            if not query or not query.strip():
                raise RetrieverError(
                    "Query cannot be empty or only whitespace",
                    error_type="INVALID_QUERY",
                    details={"query": query}
                )
            
            if k <= 0:
                raise RetrieverError(
                    "Number of results (k) must be positive",
                    error_type="INVALID_K_VALUE",
                    details={"k": k}
                )
            
            if faq_weight < 0:
                raise RetrieverError(
                    "FAQ weight must be non-negative",
                    error_type="INVALID_FAQ_WEIGHT",
                    details={"faq_weight": faq_weight}
                )
            
            if doc_weight < 0:
                raise RetrieverError(
                    "Document weight must be non-negative",
                    error_type="INVALID_DOC_WEIGHT",
                    details={"doc_weight": doc_weight}
                )
            
            try:
                faq_results = self.retrieve_from_faq(query, k, type_faq, query_lang)
            except RetrieverError:
                raise
            except Exception as e:
                raise RetrieverError(
                    f"Failed to retrieve from FAQ: {str(e)}",
                    error_type="FAQ_RETRIEVAL_ERROR",
                    details={"query": query, "original_error": str(e)}
                )
            
            try:
                doc_results = self.retrieve_from_knowledge_chunks(query, k, type_doc, query_lang)
            except RetrieverError:
                raise
            except Exception as e:
                raise RetrieverError(
                    f"Failed to retrieve from knowledge chunks: {str(e)}",
                    error_type="KNOWLEDGE_RETRIEVAL_ERROR",
                    details={"query": query, "original_error": str(e)}
                )
            
            try:
                for item in faq_results:
                    if 'score' in item:
                        item['score'] = item['score'] * faq_weight
                    item['source'] = 'faq'
                    
                for item in doc_results:
                    if 'score' in item:
                        item['score'] = item['score'] * doc_weight
                    item['source'] = 'document'
                    
                combined_results = faq_results + doc_results
                combined_results.sort(key=lambda x: x.get('score', 0), reverse=True)
                
                logger.info(f"Combined {len(faq_results)} FAQ and {len(doc_results)} document results for query: '{query}'")
                return combined_results[:k]
                
            except Exception as e:
                raise RetrieverError(
                    f"Failed to combine and sort results: {str(e)}",
                    error_type="RESULT_COMBINATION_ERROR",
                    details={"query": query, "faq_count": len(faq_results), "doc_count": len(doc_results), "original_error": str(e)}
                )
                
        except RetrieverError:
            raise
        except Exception as e:
            raise RetrieverError(
                f"Unexpected error in retrieve_from_knowledge_and_faq: {str(e)}",
                error_type="UNEXPECTED_ERROR",
                details={"query": query, "user_id": self.user_id, "original_error": str(e)}
            )
    
    # def retrieve_from_knowledge_and_faq_native(
    #     self, 
    #     query: str, 
    #     k: int = 10, 
    #     query_lang: str = 'simple',
    #     rrf_k: int = 10
    # ) -> List[Dict[str, Any]]:
    #     """
    #     Retrieve from knowledge and faq using the native unified retrieve function
    #     This method doesn't support custom weighting between FAQ and documents
        
    #     Args:
    #         query: The query to retrieve from knowledge and faq
    #         k: The number of results to retrieve
    #         query_lang: The language of the query
    #         rrf_k: RRF constant value
            
    #     Returns:
    #         List of dictionaries with content and score
    #     """
    #     db = get_authenticated_db()
        
    #     result = db.rpc('text_unified_retrieve', {
    #         'query_text': query,
    #         'query_embedding': self._embed_texts([query])[0],
    #         'query_lang': query_lang,
    #         'match_count': k,
    #         'rrf_k': rrf_k
    #     }).execute()
        
    #     if result and result[0]:
    #         return result[0]
    #     return []