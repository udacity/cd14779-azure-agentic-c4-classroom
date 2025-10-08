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
    
    def chunk_document(self, content: str, chunk_size: int = 1000, overlap: int = 200) -> List[DocumentChunk]:
        """Split document into chunks for better embedding"""
        chunks = []
        words = content.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_content = " ".join(chunk_words)
            
            # Create unique chunk ID
            content_hash = hashlib.md5(chunk_content.encode()).hexdigest()[:8]
            chunk_id = f"chunk_{content_hash}"
            
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=content_hash,  # Using hash as document ID for demo
                content=chunk_content,
                metadata={
                    "chunk_index": i,
                    "total_chunks": len(words) // (chunk_size - overlap) + 1,
                    "word_count": len(chunk_words)
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def determine_collection(self, filename: str, content: str) -> str:
        """Determine which collection to use based on filename and content"""
        filename_lower = filename.lower()
        content_lower = content.lower()
        
        # Check filename patterns
        if any(term in filename_lower for term in ["financial", "revenue", "profit", "report"]):
            return "financial"
        elif any(term in filename_lower for term in ["technical", "spec", "architecture", "api"]):
            return "technical" 
        elif any(term in filename_lower for term in ["market", "customer", "analysis", "trend"]):
            return "market"
        
        # Check content patterns
        if any(term in content_lower for term in ["revenue", "profit", "financial", "growth"]):
            return "financial"
        elif any(term in content_lower for term in ["architecture", "api", "technical", "system"]):
            return "technical"
        elif any(term in content_lower for term in ["market", "customer", "competition", "trend"]):
            return "market"
        
        return "general"
    
    def add_document(self, filename: str, content: str, metadata: Dict = None) -> int:
        """Add document to ChromaDB with automatic chunking and collection assignment"""
        try:
            # Determine the right collection
            collection_name = self.determine_collection(filename, content)
            collection = self.collections[collection_name]
            
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
                    "collection": collection_name,
                    "document_type": self._extract_document_type(filename),
                    **chunk.metadata
                }
                
                if metadata:
                    chunk_metadata.update(metadata)
                
                metadatas.append(chunk_metadata)
            
            # Add to ChromaDB
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
            
            for collection_name in collection_names:
                if collection_name in self.collections:
                    collection = self.collections[collection_name]
                    
                    results = collection.query(
                        query_texts=[query],
                        n_results=n_results
                    )
                    
                    # Process results
                    for i in range(len(results['ids'][0])):
                        result = {
                            "chunk_id": results['ids'][0][i],
                            "content": results['documents'][0][i],
                            "metadata": results['metadatas'][0][i],
                            "distance": results['distances'][0][i],
                            "collection": collection_name
                        }
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
            filename = result["metadata"]["filename"]
            
            if filename not in document_groups:
                document_groups[filename] = {
                    "filename": filename,
                    "best_chunks": [],
                    "min_distance": result["distance"],
                    "collection": result["collection"],
                    "document_type": result["metadata"]["document_type"]
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