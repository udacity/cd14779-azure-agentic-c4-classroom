import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Any
import uuid
import logging
import asyncio
from pydantic import BaseModel, Field
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentChunk(BaseModel):
    """Model representing a document chunk for vector storage"""
    chunk_id: str
    document_id: str
    content: str
    metadata: Dict
    embedding: Optional[List[float]] = None

class ChromaDBManager:
    """Manages ChromaDB vector store for document embeddings and semantic search"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Create collections for different document types
        self.collections = {
            "financial": self.client.get_or_create_collection(
                name="financial_documents",
                metadata={"description": "Financial reports and analysis"}
            ),
            "technical": self.client.get_or_create_collection(
                name="technical_documents", 
                metadata={"description": "Technical specifications and documentation"}
            ),
            "market": self.client.get_or_create_collection(
                name="market_documents",
                metadata={"description": "Market research and analysis"}
            ),
            "general": self.client.get_or_create_collection(
                name="general_documents",
                metadata={"description": "General documents"}
            )
        }
        
        logger.info(f"ChromaDB initialized with {len(self.collections)} collections")
    
    def chunk_document(self, content: str, chunk_size: int = 500, overlap: int = 50) -> List[DocumentChunk]:
        """Better document chunking for semantic search"""
        # Split by paragraphs first for better context
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size, save current chunk
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Keep some overlap by carrying over the last part
                sentences = current_chunk.split('. ')
                if len(sentences) > 2:
                    current_chunk = '. '.join(sentences[-2:]) + '. '
                else:
                    current_chunk = ""
            
            current_chunk += paragraph + "\n\n"
        
        # Add the final chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # If we have no chunks (very short document), use the whole content
        if not chunks:
            chunks = [content]
        
        # Create DocumentChunk objects
        document_chunks = []
        for i, chunk_content in enumerate(chunks):
            content_hash = hashlib.md5(chunk_content.encode()).hexdigest()[:8]
            chunk_id = f"chunk_{content_hash}"
            
            document_chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                document_id=content_hash,
                content=chunk_content,
                metadata={
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "word_count": len(chunk_content.split()),
                    "char_count": len(chunk_content)
                }
            ))
        
        return document_chunks
    
    def determine_collection(self, filename: str, content: str) -> str:
        """Better collection assignment with scoring and content analysis"""
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        collection_scores = {
            "financial": 0,
            "technical": 0, 
            "market": 0,
            "general": 0
        }
        
        # Financial terms with weights
        financial_terms = {
            "revenue": 3, "profit": 3, "financial": 2, "growth": 2, 
            "market cap": 3, "investment": 2, "margin": 2, "earnings": 2,
            "billion": 2, "million": 1, "dollar": 1, "cost": 1
        }
        
        # Technical terms with weights
        technical_terms = {
            "architecture": 3, "api": 3, "technical": 2, "system": 2,
            "infrastructure": 2, "kubernetes": 3, "microservices": 3, 
            "deployment": 2, "performance": 2, "security": 2, "scalability": 2
        }
        
        # Market terms with weights  
        market_terms = {
            "market": 3, "customer": 3, "competition": 3, "trend": 2,
            "analysis": 2, "industry": 2, "competitive": 2, "segmentation": 2,
            "landscape": 2, "opportunity": 2, "threat": 1
        }
        
        # Score based on filename
        for term, weight in financial_terms.items():
            if term in filename_lower:
                collection_scores["financial"] += weight * 2  # Extra weight for filename
        
        for term, weight in technical_terms.items():
            if term in filename_lower: 
                collection_scores["technical"] += weight * 2
        
        for term, weight in market_terms.items():
            if term in filename_lower:
                collection_scores["market"] += weight * 2
        
        # Score based on content (first 2000 chars for efficiency)
        preview = content_lower[:2000]
        for term, weight in financial_terms.items():
            collection_scores["financial"] += preview.count(term) * weight
        
        for term, weight in technical_terms.items():
            collection_scores["technical"] += preview.count(term) * weight
        
        for term, weight in market_terms.items():
            collection_scores["market"] += preview.count(term) * weight
        
        # Return collection with highest score, only if score is significant
        best_collection = max(collection_scores, key=collection_scores.get)
        return best_collection if collection_scores[best_collection] > 5 else "general"

    async def chunk_and_store_document(self, filename: str, content: str, collection_type: str) -> int:
        """Async wrapper for adding document to ChromaDB"""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.add_document, filename, content, collection_type
        )

    def add_document(self, filename: str, content: str, collection_type: str = None) -> int:
        """Add document to ChromaDB with automatic chunking and collection assignment"""
        try:
            # Determine the right collection if not provided
            if collection_type is None:
                collection_type = self.determine_collection(filename, content)
            
            collection = self.collections[collection_type]
            
            # Chunk the document
            chunks = self.chunk_document(content)
            
            # Prepare data for ChromaDB
            ids = []
            documents = []
            metadatas = []
            
            for chunk in chunks:
                chunk_id = f"{filename}_{chunk.chunk_id}"
                ids.append(chunk_id)
                documents.append(chunk.content)
                
                chunk_metadata = {
                    "filename": filename,
                    "chunk_id": chunk.chunk_id,
                    "collection": collection_type,
                    "document_type": self._extract_document_type(filename),
                    **chunk.metadata
                }
                
                metadatas.append(chunk_metadata)
            
            # Add to ChromaDB
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(chunks)} chunks from {filename} to {collection_type} collection")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Error adding document {filename} to ChromaDB: {e}")
            return 0
    
    def _extract_document_type(self, filename: str) -> str:
        """Extract document type from filename"""
        if filename.endswith('.pdf'):
            return 'pdf'
        elif filename.endswith('.md'):
            return 'markdown'
        elif filename.endswith('.json'):
            return 'json'
        elif filename.endswith('.txt'):
            return 'text'
        else:
            return 'unknown'
    
    async def semantic_search(self, query: str, collection_names: List[str] = None, top_k: int = 5) -> List[Dict]:
        """Perform semantic search across specified collections"""
        try:
            if not collection_names:
                collection_names = list(self.collections.keys())
            
            all_results = []
            
            for collection_name in collection_names:
                if collection_name in self.collections:
                    collection = self.collections[collection_name]
                    
                    results = collection.query(
                        query_texts=[query],
                        n_results=top_k
                    )
                    
                    # Process results
                    for i in range(len(results['ids'][0])):
                        result = {
                            "filename": results['metadatas'][0][i]["filename"],
                            "content": results['documents'][0][i],
                            "metadata": results['metadatas'][0][i],
                            "distance": results['distances'][0][i] if results['distances'] else 0.0,
                            "collection": collection_name
                        }
                        all_results.append(result)
            
            # Sort by distance (lower is better)
            if all_results and 'distance' in all_results[0]:
                all_results.sort(key=lambda x: x["distance"])
            
            # Group by document and get best chunks
            unique_docs = self._group_by_document(all_results)
            
            logger.info(f"Semantic search found {len(unique_docs)} relevant documents")
            return unique_docs
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def _group_by_document(self, results: List[Dict]) -> List[Dict]:
        """Group search results by document and return best chunks"""
        document_groups = {}
        
        for result in results:
            filename = result["filename"]
            
            if filename not in document_groups:
                document_groups[filename] = {
                    "filename": filename,
                    "best_chunks": [],
                    "min_distance": result.get("distance", 0.0),
                    "collection": result["collection"],
                    "document_type": result["metadata"].get("document_type", "unknown")
                }
            
            # Keep top 2 chunks per document
            if len(document_groups[filename]["best_chunks"]) < 2:
                document_groups[filename]["best_chunks"].append({
                    "content": result["content"],
                    "distance": result.get("distance", 0.0)
                })
            
            # Update minimum distance
            if result.get("distance", 0.0) < document_groups[filename]["min_distance"]:
                document_groups[filename]["min_distance"] = result.get("distance", 0.0)
        
        # Convert to list and sort by best match
        unique_docs = list(document_groups.values())
        unique_docs.sort(key=lambda x: x["min_distance"])
        
        return unique_docs
    
    def hybrid_search(self, query: str, keywords: List[str], collection_names: List[str] = None) -> List[Dict]:
        """Combine semantic search with keyword matching"""
        # Get semantic results
        semantic_results = self.semantic_search(query, collection_names, top_k=10)
        
        # Boost scores for keyword matches
        for result in semantic_results:
            keyword_boost = 0
            for chunk in result["best_chunks"]:
                content_lower = chunk["content"].lower()
                for keyword in keywords:
                    if keyword.lower() in content_lower:
                        keyword_boost += 0.1  # Small boost for each keyword match
            
            # Adjust score (lower distance is better, so subtract boost)
            result["min_distance"] = max(0, result["min_distance"] - keyword_boost)
        
        # Re-sort by adjusted score
        semantic_results.sort(key=lambda x: x["min_distance"])
        
        return semantic_results[:5]  # Return top 5
    
    async def get_collection_stats(self) -> Dict:
        """Get statistics for all collections"""
        stats = {}
        
        for collection_name, collection in self.collections.items():
            try:
                count = collection.count()
                stats[collection_name] = {
                    "document_count": count,
                    "description": collection.metadata.get("description", "No description")
                }
            except Exception as e:
                stats[collection_name] = {"error": str(e)}
        
        return stats
    
    def clear_collection(self, collection_name: str):
        """Clear a specific collection"""
        if collection_name in self.collections:
            self.collections[collection_name].delete()
            self.collections[collection_name] = self.client.get_or_create_collection(name=collection_name)
            logger.info(f"Cleared collection: {collection_name}")
    
    def clear_all_collections(self):
        """Clear all collections"""
        for collection_name in self.collections.keys():
            self.clear_collection(collection_name)
        logger.info("Cleared all ChromaDB collections")