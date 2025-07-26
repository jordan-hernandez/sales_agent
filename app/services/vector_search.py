import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from sqlalchemy import text, func, desc
from app.models.embeddings import ProductEmbedding, ConversationMemory, KnowledgeBase, SearchLog
from app.models.product import Product
from app.models.conversation import Conversation
from app.models.restaurant import Restaurant
from app.core.database import get_db
import logging
import openai
from app.core.config import settings

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Service for semantic search using pgvector and embeddings"""
    
    def __init__(self):
        # Initialize embedding model
        self.embedding_model = None
        self.embedding_dimension = 384
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        
        # Force use of sentence-transformers (no OpenAI embeddings)
        self.use_openai_embeddings = False
        
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
        """Generate embedding for text using sentence-transformers"""
        start_time = time.time()
        
        try:
            if self.embedding_model is None:
                # Fallback to random vector if model failed to load
                logger.warning("Embedding model not loaded, using random vector")
                embedding = np.random.rand(self.embedding_dimension)
            else:
                embedding = self.embedding_model.encode(text)
            
            embedding_time = int((time.time() - start_time) * 1000)
            logger.debug(f"Generated embedding in {embedding_time}ms")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return random vector as fallback
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
                
                # Add price range context
                if product.price < 10000:
                    content_parts.append("económico barato")
                elif product.price > 25000:
                    content_parts.append("premium caro")
                else:
                    content_parts.append("precio medio")
                
                content = " ".join(content_parts)
                
                # Generate embedding
                embedding = self.get_embedding(content)
                
                if existing_embedding:
                    # Update existing
                    existing_embedding.content = content
                    existing_embedding.embedding = embedding.tolist()
                    existing_embedding.embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
                    stats['updated'] += 1
                else:
                    # Create new
                    new_embedding = ProductEmbedding(
                        product_id=product.id,
                        restaurant_id=restaurant_id,
                        content=content,
                        embedding=embedding.tolist(),
                        embedding_model="sentence-transformers/all-MiniLM-L6-v2"
                    )
                    db.add(new_embedding)
                    stats['created'] += 1
                
            except Exception as e:
                logger.error(f"Error creating embedding for product {product.id}: {e}")
                stats['errors'] += 1
        
        db.commit()
        logger.info(f"Product embeddings: {stats}")
        return stats
    
    def search_products_semantic(
        self, 
        query: str, 
        restaurant_id: int, 
        db: Session,
        limit: int = 5,
        similarity_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Search products using semantic similarity"""
        
        start_time = time.time()
        
        try:
            # Generate embedding for query
            embedding_start = time.time()
            query_embedding = self.get_embedding(query)
            embedding_time = int((time.time() - embedding_start) * 1000)
            
            # Perform vector similarity search
            search_start = time.time()
            
            # Using cosine similarity with pgvector (Supabase compatible)
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
                'query_embedding': query_embedding.tolist(),
                'restaurant_id': restaurant_id,
                'threshold': 1 - similarity_threshold,  # Convert similarity to distance
                'limit': limit
            }).fetchall()
            
            search_time = int((time.time() - search_start) * 1000)
            total_time = int((time.time() - start_time) * 1000)
            
            # Format results
            products = []
            for row in results:
                similarity_score = 1 - row.distance  # Convert distance back to similarity
                products.append({
                    'product_id': row.product_id,
                    'name': row.name,
                    'description': row.description,
                    'price': row.price,
                    'category': row.category,
                    'similarity_score': round(similarity_score, 3),
                    'content': row.content
                })
            
            # Log search
            self._log_search(
                query, 'products', restaurant_id, db,
                len(products), max([p['similarity_score'] for p in products] + [0]),
                total_time, embedding_time
            )
            
            logger.info(f"Semantic search '{query}' found {len(products)} products in {total_time}ms")
            return products
            
        except Exception as e:
            logger.error(f"Error in semantic product search: {e}")
            return []
    
    def search_knowledge_base(
        self,
        query: str,
        restaurant_id: int,
        db: Session,
        limit: int = 3,
        similarity_threshold: float = 0.4
    ) -> List[Dict[str, Any]]:
        """Search knowledge base using semantic similarity"""
        
        try:
            query_embedding = self.get_embedding(query)
            
            results = db.execute(text("""
                SELECT 
                    kb.id,
                    kb.question,
                    kb.answer,
                    kb.category,
                    kb.usage_count,
                    (kb.embedding <=> CAST(:query_embedding AS vector)) as distance
                FROM knowledge_base kb
                WHERE kb.restaurant_id = :restaurant_id 
                    AND kb.active = true
                    AND (kb.embedding <=> CAST(:query_embedding AS vector)) < :threshold
                ORDER BY kb.embedding <=> CAST(:query_embedding AS vector)
                LIMIT :limit
            """), {
                'query_embedding': query_embedding.tolist(),
                'restaurant_id': restaurant_id,
                'threshold': 1 - similarity_threshold,
                'limit': limit
            }).fetchall()
            
            knowledge_items = []
            for row in results:
                knowledge_items.append({
                    'id': row.id,
                    'question': row.question,
                    'answer': row.answer,
                    'category': row.category,
                    'similarity_score': round(1 - row.distance, 3),
                    'usage_count': row.usage_count
                })
            
            return knowledge_items
            
        except Exception as e:
            logger.error(f"Error in knowledge base search: {e}")
            return []
    
    def search_conversation_memory(
        self,
        query: str,
        customer_phone: str,
        restaurant_id: int,
        db: Session,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Search conversation memories for a specific customer"""
        
        try:
            query_embedding = self.get_embedding(query)
            
            results = db.execute(text("""
                SELECT 
                    cm.id,
                    cm.memory_type,
                    cm.content,
                    cm.summary,
                    cm.importance_score,
                    cm.access_count,
                    cm.created_at,
                    (cm.embedding <=> CAST(:query_embedding AS vector)) as distance
                FROM conversation_memories cm
                WHERE cm.customer_phone = :customer_phone
                    AND cm.restaurant_id = :restaurant_id
                ORDER BY 
                    cm.importance_score DESC,
                    cm.embedding <=> CAST(:query_embedding AS vector),
                    cm.created_at DESC
                LIMIT :limit
            """), {
                'query_embedding': query_embedding.tolist(),
                'customer_phone': customer_phone,
                'restaurant_id': restaurant_id,
                'limit': limit
            }).fetchall()
            
            memories = []
            for row in results:
                memories.append({
                    'id': row.id,
                    'memory_type': row.memory_type,
                    'content': row.content,
                    'summary': row.summary,
                    'importance_score': row.importance_score,
                    'similarity_score': round(1 - row.distance, 3),
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
            logger.error(f"Error in memory search: {e}")
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
            
            memory = ConversationMemory(
                conversation_id=conversation_id,
                restaurant_id=restaurant_id,
                customer_phone=customer_phone,
                memory_type=memory_type,
                content=content,
                summary=summary,
                importance_score=importance_score,
                embedding=embedding.tolist()
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
            
            kb_entry = KnowledgeBase(
                restaurant_id=restaurant_id,
                question=question,
                answer=answer,
                category=category,
                tags=tags,
                searchable_content=searchable_content,
                embedding=embedding.tolist()
            )
            
            db.add(kb_entry)
            db.commit()
            
            logger.info(f"Created knowledge base entry: {category}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating knowledge base entry: {e}")
            return False
    
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
            
            log = SearchLog(
                conversation_id=conversation_id,
                restaurant_id=restaurant_id,
                query=query,
                search_type=search_type,
                embedding=query_embedding.tolist(),
                results_found=results_found,
                top_similarity=top_similarity,
                search_time_ms=search_time_ms,
                embedding_time_ms=embedding_time_ms
            )
            
            db.add(log)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error logging search: {e}")
    
    def get_search_analytics(self, restaurant_id: int, db: Session, days: int = 7) -> Dict[str, Any]:
        """Get search analytics for the restaurant"""
        
        try:
            # Most common search terms
            common_queries = db.execute(text("""
                SELECT query, COUNT(*) as count, AVG(top_similarity) as avg_similarity
                FROM search_logs 
                WHERE restaurant_id = :restaurant_id 
                    AND created_at > NOW() - INTERVAL '%s days'
                GROUP BY query
                ORDER BY count DESC
                LIMIT 10
            """ % days), {'restaurant_id': restaurant_id}).fetchall()
            
            # Performance stats
            performance = db.execute(text("""
                SELECT 
                    AVG(search_time_ms) as avg_search_time,
                    AVG(embedding_time_ms) as avg_embedding_time,
                    AVG(results_found) as avg_results,
                    COUNT(*) as total_searches
                FROM search_logs 
                WHERE restaurant_id = :restaurant_id 
                    AND created_at > NOW() - INTERVAL '%s days'
            """ % days), {'restaurant_id': restaurant_id}).fetchone()
            
            return {
                'common_queries': [
                    {'query': row.query, 'count': row.count, 'avg_similarity': round(row.avg_similarity, 3)}
                    for row in common_queries
                ],
                'performance': {
                    'avg_search_time_ms': round(performance.avg_search_time or 0, 1),
                    'avg_embedding_time_ms': round(performance.avg_embedding_time or 0, 1),
                    'avg_results': round(performance.avg_results or 0, 1),
                    'total_searches': performance.total_searches or 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting search analytics: {e}")
            return {'common_queries': [], 'performance': {}}


# Global service instance
vector_search_service = VectorSearchService()