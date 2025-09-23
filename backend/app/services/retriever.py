from app.services.ingest_helpers import embed_texts
from typing import List, Tuple, Dict, Any, Optional
from app.db.session import get_authenticated_db

class Retriever:
    def __init__(self):
        self.embed_texts = embed_texts

    def _embed_texts(self, texts: List[str]) -> List[List[float]]:
        return embed_texts(texts)
    
    async def retrieve_from_knowledge_chunks(self, query: str, k: int = 10, type: str = 'text', query_lang: str = 'simple') -> List[Dict[str, Any]]:
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
        db = get_authenticated_db()
        if type not in ['text', 'vector', 'hybrid']:
            raise ValueError('Type must be one of: text, vector, hybrid')
        
        result = None
        if type == 'text':
            result = db.rpc(f'{type}_knowledge_chunks_search', {
                'query_text': query,
                'query_lang': query_lang,
                'match_count': k,
            }).execute()
        elif type == 'vector':
            result = db.rpc(f'{type}_knowledge_chunks_search', {
                'query_text': query,
                'query_embedding': self._embed_texts([query])[0],
                'match_count': k,
            }).execute()
        elif type == 'hybrid':
            result = db.rpc(f'{type}_knowledge_chunks_search', {
                'query_text': query,
                'query_embedding': self._embed_texts([query])[0],
                'query_lang': query_lang,
                'match_count': k,
                'rrf_k': k
            }).execute()
        
        if result and result[0]:
            return result[0]
        return []
    
    async def retrieve_from_faq(self, query: str, k: int = 10, type: str = 'text', query_lang: str = 'simple') -> List[Dict[str, Any]]:
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
        db = get_authenticated_db()
        if type not in ['text']:
            raise ValueError('Type must be one of: text')
        
        result = None
        if type == 'text':
            result = db.rpc(f'{type}_faq_search', {
                'query_text': query,
                'query_lang': query_lang,
                'match_count': k
            }).execute()
        
        if result and result[0]:
            return result[0]
        return []
        
    async def retrieve_from_knowledge_and_faq(
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
        faq_results = await self.retrieve_from_faq(query, k, type_faq, query_lang)
        doc_results = await self.retrieve_from_knowledge_chunks(query, k, 
                                                        type_doc, 
                                                        query_lang)
        
        for item in faq_results:
            item['score'] = item['score'] * faq_weight
            item['source'] = 'faq'
            
        for item in doc_results:
            item['score'] = item['score'] * doc_weight
            item['source'] = 'document'
            
        combined_results = faq_results + doc_results
        combined_results.sort(key=lambda x: x['score'], reverse=True)
        
        return combined_results[:k]
    
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