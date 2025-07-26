"""
Enhanced vector search service optimized for Supabase
Uses native Supabase functions for better performance
"""
import time
import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.models.embeddings import ProductEmbedding, ConversationMemory, KnowledgeBase, SearchLog
from app.models.product import Product
from app.core.config import settings
import logging
import openai

logger = logging.getLogger(__name__)


class SupabaseVectorSearchService:
    """Enhanced vector search service optimized for Supabase"""
    
    def __init__(self):
        # Initialize embedding model
        self.embedding_model = None
        self.embedding_dimension = 384
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        
        # Initialize OpenAI if available
        self.use_openai_embeddings = False
        if hasattr(settings, 'openai_api_key') and settings.openai_api_key:
            openai.api_key = settings.openai_api_key
            self.use_openai_embeddings = True
            self.embedding_dimension = 1536
        
        self._load_embedding_model()
    
    def _load_embedding_model(self):
        """Load the sentence transformer model"""
        try:
            if not self.use_openai_embeddings:
                self.embedding_model = SentenceTransformer(self.model_name)
                logger.info(f"Loaded embedding model: {self.model_name}")
            else:
                logger.info("Using OpenAI embeddings")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            self.embedding_model = None
    
    def get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        start_time = time.time()
        
        try:
            if self.use_openai_embeddings:
                response = openai.Embedding.create(
                    input=text,
                    model="text-embedding-ada-002"
                )
                embedding = np.array(response['data'][0]['embedding'])
            else:
                if self.embedding_model is None:
                    logger.warning("Embedding model not loaded, using random vector")
                    embedding = np.random.rand(self.embedding_dimension)
                else:
                    embedding = self.embedding_model.encode(text)
            
            embedding_time = int((time.time() - start_time) * 1000)
            logger.debug(f"Generated embedding in {embedding_time}ms")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return np.random.rand(self.embedding_dimension)
    
    def create_product_embeddings(self, restaurant_id: int, db: Session) -> Dict[str, int]:
        """Create embeddings for all products in a restaurant"""
        
        products = db.query(Product).filter(
            Product.restaurant_id == restaurant_id,
            Product.available == True
        ).all()
        
        stats = {'created': 0, 'updated': 0, 'errors': 0}
        
        for product in products:
            try:
                # Check if embedding already exists
                existing_embedding = db.query(ProductEmbedding).filter(
                    ProductEmbedding.product_id == product.id
                ).first()
                
                # Create searchable content
                content_parts = [product.name]
                if product.description:
                    content_parts.append(product.description)
                content_parts.append(product.category)
                
                # Add price context in Spanish
                if product.price < 10000:
                    content_parts.append("económico barato accesible")
                elif product.price > 25000:
                    content_parts.append("premium caro exclusivo")
                else:
                    content_parts.append("precio medio estándar")
                
                # Add Colombian food context
                if 'bandeja' in product.name.lower():
                    content_parts.append("típico tradicional colombiano completo")
                elif 'empanada' in product.name.lower():
                    content_parts.append("frito entrada aperitivo")
                elif 'sancocho' in product.name.lower():
                    content_parts.append("sopa caliente tradicional familiar")
                elif 'arepa' in product.name.lower():
                    content_parts.append("maíz tradicional desayuno")
                
                content = " ".join(content_parts)
                
                # Generate embedding
                embedding = self.get_embedding(content)
                embedding_str = f"[{','.join(map(str, embedding.tolist()))}]"
                
                if existing_embedding:
                    # Update existing
                    existing_embedding.content = content
                    existing_embedding.embedding = embedding_str
                    existing_embedding.embedding_model = self.model_name
                    stats['updated'] += 1
                else:
                    # Create new
                    new_embedding = ProductEmbedding(
                        product_id=product.id,
                        restaurant_id=restaurant_id,
                        content=content,
                        embedding=embedding_str,
                        embedding_model=self.model_name
                    )
                    db.add(new_embedding)
                    stats['created'] += 1
                
            except Exception as e:
                logger.error(f"Error creating embedding for product {product.id}: {e}")
                stats['errors'] += 1
        
        db.commit()
        logger.info(f"Product embeddings: {stats}")
        return stats
    
    def search_products_semantic_supabase(
        self, 
        query: str, 
        restaurant_id: int, 
        db: Session,
        limit: int = 5,
        similarity_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Search products using Supabase native vector functions"""
        
        start_time = time.time()
        
        try:
            # Generate embedding for query
            embedding_start = time.time()
            query_embedding = self.get_embedding(query)
            embedding_time = int((time.time() - embedding_start) * 1000)
            
            # Format embedding as Supabase vector string
            embedding_str = f"[{','.join(map(str, query_embedding.tolist()))}]"
            
            # Use Supabase function for optimized search
            search_start = time.time()
            
            results = db.execute(text("""
                SELECT * FROM match_products(
                    CAST(:query_embedding AS vector),
                    :restaurant_id,
                    :match_threshold,
                    :match_count
                )
            """), {
                'query_embedding': embedding_str,
                'restaurant_id': restaurant_id,
                'match_threshold': similarity_threshold,
                'match_count': limit
            }).fetchall()
            
            search_time = int((time.time() - search_start) * 1000)
            total_time = int((time.time() - start_time) * 1000)
            
            # Format results
            products = []
            for row in results:
                products.append({
                    'product_id': row.product_id,
                    'name': row.name,
                    'description': row.description,
                    'price': row.price,
                    'category': row.category,
                    'similarity_score': round(row.similarity, 3),
                    'content': f"{row.name} {row.description or ''}"
                })
            
            # Log search
            self._log_search(
                query, 'products', restaurant_id, db,
                len(products), max([p['similarity_score'] for p in products] + [0]),
                total_time, embedding_time
            )
            
            logger.info(f"Supabase semantic search '{query}' found {len(products)} products in {total_time}ms")
            return products
            
        except Exception as e:
            logger.error(f"Error in Supabase semantic search: {e}")
            # Fallback to regular search
            return self._fallback_search_products(query, restaurant_id, db, limit, similarity_threshold)
    
    def search_knowledge_base_supabase(
        self,
        query: str,
        restaurant_id: int,
        db: Session,
        limit: int = 3,
        similarity_threshold: float = 0.4
    ) -> List[Dict[str, Any]]:
        """Search knowledge base using Supabase native functions"""
        
        try:
            query_embedding = self.get_embedding(query)
            embedding_str = f"[{','.join(map(str, query_embedding.tolist()))}]"
            
            results = db.execute(text("""
                SELECT * FROM match_knowledge(
                    CAST(:query_embedding AS vector),
                    :restaurant_id,
                    :match_threshold,
                    :match_count
                )
            """), {
                'query_embedding': embedding_str,
                'restaurant_id': restaurant_id,
                'match_threshold': similarity_threshold,
                'match_count': limit
            }).fetchall()
            
            knowledge_items = []
            for row in results:
                knowledge_items.append({
                    'id': row.id,
                    'question': row.question,
                    'answer': row.answer,
                    'category': row.category,
                    'similarity_score': round(row.similarity, 3)
                })
            
            return knowledge_items
            
        except Exception as e:
            logger.error(f"Error in Supabase knowledge search: {e}")
            return []
    
    def search_conversation_memory_supabase(
        self,
        query: str,
        customer_phone: str,
        restaurant_id: int,
        db: Session,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Search conversation memories using Supabase functions"""
        
        try:
            query_embedding = self.get_embedding(query)
            embedding_str = f"[{','.join(map(str, query_embedding.tolist()))}]"
            
            results = db.execute(text("""
                SELECT * FROM match_memories(
                    CAST(:query_embedding AS vector),
                    :customer_phone,
                    :restaurant_id,
                    :match_count
                )
            """), {
                'query_embedding': embedding_str,
                'customer_phone': customer_phone,
                'restaurant_id': restaurant_id,
                'match_count': limit
            }).fetchall()
            
            memories = []
            for row in results:
                memories.append({
                    'id': row.id,
                    'memory_type': row.memory_type,
                    'content': row.content,
                    'summary': row.summary,
                    'importance_score': row.importance_score,
                    'similarity_score': round(row.similarity, 3),
                    'created_at': row.created_at
                })
            
            # Update access count
            for memory in memories:
                db.execute(text("""
                    UPDATE conversation_memories 
                    SET access_count = access_count + 1, last_accessed = NOW()
                    WHERE id = :memory_id
                """), {'memory_id': memory['id']})
            
            db.commit()
            return memories
            
        except Exception as e:
            logger.error(f"Error in Supabase memory search: {e}")
            return []
    
    def store_conversation_memory(
        self,
        conversation_id: int,
        restaurant_id: int,
        customer_phone: str,
        memory_type: str,
        content: str,
        summary: str,
        importance_score: float,
        db: Session
    ) -> bool:
        """Store a conversation memory with embedding"""
        
        try:
            # Generate embedding
            embedding = self.get_embedding(content + " " + summary)
            embedding_str = f"[{','.join(map(str, embedding.tolist()))}]"
            
            memory = ConversationMemory(
                conversation_id=conversation_id,
                restaurant_id=restaurant_id,
                customer_phone=customer_phone,
                memory_type=memory_type,
                content=content,
                summary=summary,
                importance_score=importance_score,
                embedding=embedding_str
            )
            
            db.add(memory)
            db.commit()
            
            logger.info(f"Stored memory: {memory_type} for customer {customer_phone}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}")
            return False
    
    def create_knowledge_base_entry(
        self,
        restaurant_id: int,
        question: str,
        answer: str,
        category: str,
        tags: List[str],
        db: Session
    ) -> bool:
        """Create a knowledge base entry with embedding"""
        
        try:
            # Create searchable content
            searchable_content = f"{question} {answer} {' '.join(tags)}"
            embedding = self.get_embedding(searchable_content)
            embedding_str = f"[{','.join(map(str, embedding.tolist()))}]"
            
            kb_entry = KnowledgeBase(
                restaurant_id=restaurant_id,
                question=question,
                answer=answer,
                category=category,
                tags=tags,
                searchable_content=searchable_content,
                embedding=embedding_str
            )
            
            db.add(kb_entry)
            db.commit()
            
            logger.info(f"Created knowledge base entry: {category}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating knowledge base entry: {e}")
            return False
    
    def _fallback_search_products(
        self,
        query: str,
        restaurant_id: int, 
        db: Session,
        limit: int,
        similarity_threshold: float
    ) -> List[Dict[str, Any]]:
        """Fallback search when Supabase functions are not available"""
        
        try:
            query_embedding = self.get_embedding(query)
            embedding_str = f"[{','.join(map(str, query_embedding.tolist()))}]"
            
            results = db.execute(text("""
                SELECT 
                    pe.product_id,
                    pe.content,
                    p.name,
                    p.description,
                    p.price,
                    p.category,
                    p.available,
                    (pe.embedding <=> CAST(:query_embedding AS vector)) as distance
                FROM product_embeddings pe
                JOIN products p ON pe.product_id = p.id
                WHERE pe.restaurant_id = :restaurant_id 
                    AND p.available = true
                    AND (pe.embedding <=> CAST(:query_embedding AS vector)) < :threshold
                ORDER BY pe.embedding <=> CAST(:query_embedding AS vector)
                LIMIT :limit
            """), {
                'query_embedding': embedding_str,
                'restaurant_id': restaurant_id,
                'threshold': 1 - similarity_threshold,
                'limit': limit
            }).fetchall()
            
            products = []
            for row in results:
                similarity_score = 1 - row.distance
                products.append({
                    'product_id': row.product_id,
                    'name': row.name,
                    'description': row.description,
                    'price': row.price,
                    'category': row.category,
                    'similarity_score': round(similarity_score, 3),
                    'content': row.content
                })
            
            return products
            
        except Exception as e:
            logger.error(f"Error in fallback search: {e}")
            return []
    
    def _log_search(
        self,
        query: str,
        search_type: str,
        restaurant_id: int,
        db: Session,
        results_found: int,
        top_similarity: float,
        search_time_ms: int,
        embedding_time_ms: int,
        conversation_id: Optional[int] = None
    ):
        """Log search for analytics"""
        
        try:
            query_embedding = self.get_embedding(query)
            embedding_str = f"[{','.join(map(str, query_embedding.tolist()))}]"
            
            log = SearchLog(
                conversation_id=conversation_id,
                restaurant_id=restaurant_id,
                query=query,
                search_type=search_type,
                embedding=embedding_str,
                results_found=results_found,
                top_similarity=top_similarity,
                search_time_ms=search_time_ms,
                embedding_time_ms=embedding_time_ms
            )
            
            db.add(log)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error logging search: {e}")


# Global service instance optimized for Supabase
supabase_vector_search_service = SupabaseVectorSearchService()