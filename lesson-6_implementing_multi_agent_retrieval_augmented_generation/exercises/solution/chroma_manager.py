import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import uuid
import logging
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
        # Use PersistentClient if available; keep existing call
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Map logical collection keys -> actual collection names (used with get_or_create_collection)
        self.collection_names = {
            "financial": "financial_documents",
            "technical": "technical_documents",
            "market": "market_documents",
            "competitive": "competitive_documents",
            "general": "general_documents"
        }

        # Create collections for different document types (store collection objects in self.collections)
        self.collections = {}
        for key, name in self.collection_names.items():
            self.collections[key] = self.client.get_or_create_collection(
                name=name,
                metadata={"description": f"{key} documents"}
            )
        
        logger.info(f"ChromaDB initialized with {len(self.collections)} collections: {list(self.collections.keys())}")
    
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
        # Use a stable document id (hash of full content) and chunk-specific ids
        document_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        for i, chunk_content in enumerate(chunks):
            # create a chunk-specific id based on document hash + index
            chunk_hash = hashlib.md5((chunk_content + str(i)).encode()).hexdigest()[:8]
            chunk_id = f"chunk_{document_hash}_{chunk_hash}"
            
            document_chunks.append(DocumentChunk(
                chunk_id=chunk_id,
                document_id=document_hash,
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
            "competitive": 0,
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
        
        # Market/competitive terms with weights  
        market_terms = {
            "market": 3, "customer": 3, "competition": 3, "trend": 2,
            "analysis": 2, "industry": 2, "competitive": 2, "segmentation": 2,
            "landscape": 2, "opportunity": 2, "threat": 1, "market share": 3, "competitor": 2
        }
        
        # Score based on filename (extra weight)
        for term, weight in financial_terms.items():
            if term in filename_lower:
                collection_scores["financial"] += weight * 2
        
        for term, weight in technical_terms.items():
            if term in filename_lower: 
                collection_scores["technical"] += weight * 2
        
        for term, weight in market_terms.items():
            if term in filename_lower:
                # treat market-related filename hits as either market or competitive
                collection_scores["market"] += weight * 2
                collection_scores["competitive"] += weight  # lighter boost for competitive
        
        # Score based on content (first 2000 chars for efficiency)
        preview = content_lower[:2000]
        for term, weight in financial_terms.items():
            collection_scores["financial"] += preview.count(term) * weight
        
        for term, weight in technical_terms.items():
            collection_scores["technical"] += preview.count(term) * weight
        
        for term, weight in market_terms.items():
            occurrences = preview.count(term)
            collection_scores["market"] += occurrences * weight
            # increase competitive score for presence of clear competitor/market-share mentions
            if term in ["competitive", "market share", "competitor", "competition"]:
                collection_scores["competitive"] += occurrences * (weight + 1)
        
        # Decide best collection (only return a non-general if score is significant)
        best_collection = max(collection_scores, key=collection_scores.get)
        if collection_scores[best_collection] > 5:
            return best_collection
        else:
            return "general"

    def add_document(self, filename: str, content: str, metadata: Dict = None) -> int:
        """Add document to ChromaDB with automatic chunking and collection assignment"""
        try:
            # Determine the right collection
            collection_name = self.determine_collection(filename, content)
            if collection_name not in self.collections:
                collection_name = "general"
            collection = self.collections[collection_name]
            
            # Chunk the document
            chunks = self.chunk_document(content)
            
            # Prepare data for ChromaDB
            ids = []
            documents = []
            metadatas = []
            
            for chunk in chunks:
                # create stable per-chunk id that includes filename to avoid collisions across files
                chunk_id = f"{filename}_{chunk.chunk_id}"
                ids.append(chunk_id)
                documents.append(chunk.content)
                
                chunk_metadata = {
                    "filename": filename,
                    "chunk_id": chunk.chunk_id,
                    "collection": collection_name,
                    "document_type": self._extract_document_type(filename),
                    **chunk.metadata
                }
                
                if metadata:
                    chunk_metadata.update(metadata)
                
                metadatas.append(chunk_metadata)
            
            # Add to ChromaDB (embeddings can be empty if collection supports it)
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(chunks)} chunks from {filename} to {collection_name} collection")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Error adding document {filename} to ChromaDB: {e}")
            return 0
    
    def _extract_document_type(self, filename: str) -> str:
        """Extract document type from filename"""
        filename = filename.lower()
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
    
    def semantic_search(self, query: str, collection_names: List[str] = None, n_results: int = 5) -> List[Dict]:
        """Perform semantic search across specified collections"""
        try:
            if not collection_names:
                collection_names = list(self.collections.keys())
            
            all_results = []
            
            for logical_name in collection_names:
                if logical_name in self.collections:
                    collection = self.collections[logical_name]
                    
                    results = collection.query(
                        query_texts=[query],
                        n_results=n_results
                    )
                    
                    # Process results (guard for empty)
                    ids_list = results.get('ids', [[]])
                    docs_list = results.get('documents', [[]])
                    metas_list = results.get('metadatas', [[]])
                    dists_list = results.get('distances', [[]])
                    
                    for i in range(len(ids_list[0])):
                        result = {
                            "chunk_id": ids_list[0][i],
                            "content": docs_list[0][i],
                            "metadata": metas_list[0][i],
                            "distance": dists_list[0][i],
                            "collection": logical_name
                        }
                        # Normalize filename metadata key (older code expects 'filename')
                        if "filename" not in result["metadata"] and "file_name" in result["metadata"]:
                            result["metadata"]["filename"] = result["metadata"].pop("file_name")
                        # Provide convenience fields used by callers
                        result["filename"] = result["metadata"].get("filename", result["chunk_id"])
                        # min_distance for compatibility with caller logic
                        result["min_distance"] = result["distance"]
                        # create a 'best_chunks' format expected by agents (single chunk here)
                        result["best_chunks"] = [{"content": result["content"], "distance": result["distance"]}]
                        
                        all_results.append(result)
            
            # Sort by distance (lower is better)
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
            filename = result["metadata"].get("filename", result["chunk_id"])
            
            if filename not in document_groups:
                document_groups[filename] = {
                    "filename": filename,
                    "best_chunks": [],
                    "min_distance": result["distance"],
                    "collection": result["collection"],
                    "document_type": result["metadata"].get("document_type", "unknown")
                }
            
            # Keep top 2 chunks per document
            if len(document_groups[filename]["best_chunks"]) < 2:
                document_groups[filename]["best_chunks"].append({
                    "content": result["content"],
                    "distance": result["distance"]
                })
            
            # Update minimum distance
            if result["distance"] < document_groups[filename]["min_distance"]:
                document_groups[filename]["min_distance"] = result["distance"]
        
        # Convert to list and sort by best match
        unique_docs = list(document_groups.values())
        unique_docs.sort(key=lambda x: x["min_distance"])
        
        return unique_docs
    
    def hybrid_search(self, query: str, keywords: List[str], collection_names: List[str] = None) -> List[Dict]:
        """Combine semantic search with keyword matching"""
        # Get semantic results
        semantic_results = self.semantic_search(query, collection_names, n_results=10)
        
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
    
    def get_collection_stats(self) -> Dict:
        """Get statistics for all collections"""
        stats = {}
        
        for collection_name, collection in self.collections.items():
            try:
                # collection.count() may be available; guard with getattr
                count = None
                if hasattr(collection, "count"):
                    count = collection.count()
                elif hasattr(collection, "num_docs"):
                    count = collection.num_docs()
                else:
                    # fallback: attempt to get length via query if supported
                    try:
                        # Some chroma clients expose a get method or return metadata; attempt safe call
                        count = collection.count()
                    except Exception:
                        count = None
                
                desc = None
                try:
                    desc = collection.metadata.get("description", None)
                except Exception:
                    desc = None
                
                stats[collection_name] = {
                    "document_count": count if count is not None else 0,
                    "description": desc or "No description"
                }
            except Exception as e:
                stats[collection_name] = {"error": str(e)}
        
        return stats
    
    def clear_collection(self, collection_name: str):
        """Clear a specific collection"""
        if collection_name in self.collections:
            old_collection = self.collections[collection_name]
            try:
                # Delete all documents in the collection
                # Many chroma collection objects have a delete method that can accept filters.
                # To clear entirely, attempt to delete the collection documents if supported.
                if hasattr(old_collection, "delete"):
                    # If delete expects ids or a query, call without args only if supported
                    try:
                        old_collection.delete()
                    except TypeError:
                        # fallback: recreate collection by name
                        pass
                # Recreate collection with same underlying name
                underlying_name = self.collection_names.get(collection_name, getattr(old_collection, "name", collection_name))
                self.collections[collection_name] = self.client.get_or_create_collection(
                    name=underlying_name,
                    metadata={"description": f"{collection_name} documents"}
                )
                logger.info(f"Cleared collection: {collection_name}")
            except Exception as e:
                logger.error(f"Error clearing collection {collection_name}: {e}")
    
    def clear_all_collections(self):
        """Clear all collections"""
        for collection_name in list(self.collections.keys()):
            self.clear_collection(collection_name)
        logger.info("Cleared all ChromaDB collections")
