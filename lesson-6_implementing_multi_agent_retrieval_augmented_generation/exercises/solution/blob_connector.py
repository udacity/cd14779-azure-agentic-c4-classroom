import os
import json
import tempfile
from typing import List, Dict, Optional
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError
from pydantic import BaseModel, Field
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentMetadata(BaseModel):
    """Metadata for documents in blob storage"""
    filename: str
    content_type: str
    file_size: int
    upload_date: str
    tags: Dict[str, str] = Field(default_factory=dict)

class BlobStorageConnector:
    """Manages document storage and retrieval from Azure Blob Storage"""
    
    def __init__(self, connection_string: str = None, container_name: str = "rag-documents"):
        self.connection_string = connection_string or os.getenv("BLOB_CONNECTION_STRING")
        if not self.connection_string:
            raise ValueError("Azure Storage connection string not provided")
        
        self.container_name = container_name
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        self.container_client = self.blob_service_client.get_container_client(container_name)
        
        # Create container if it doesn't exist
        self._create_container()
    
    def _create_container(self):
        """Create blob container if it doesn't exist"""
        try:
            self.container_client.create_container()
            logger.info(f"Created container: {self.container_name}")
        except ResourceExistsError:
            logger.info(f"Container {self.container_name} already exists")
        except Exception as e:
            logger.error(f"Error creating container: {e}")
            raise
    
    def upload_text_as_document(self, content: str, blob_name: str, tags: Dict = None) -> bool:
        """Upload text content as a document to blob storage"""
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.upload_blob(content, overwrite=True)
            
            if tags:
                blob_client.set_blob_tags(tags)
            
            logger.info(f"Uploaded text document: {blob_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading text document {blob_name}: {e}")
            return False
    
    def get_document_content(self, blob_name: str) -> Optional[str]:
        """Get document content as text directly"""
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            download_stream = blob_client.download_blob()
            content = download_stream.readall().decode('utf-8')
            
            logger.info(f"Retrieved content from Azure: {blob_name}")
            return content
            
        except Exception as e:
            logger.error(f"Error getting content from {blob_name}: {e}")
            return None
    
    def list_documents(self) -> List[str]:
        """List all documents in the container"""
        try:
            blob_list = self.container_client.list_blobs()
            return [blob.name for blob in blob_list]
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return []
    
    def upload_sample_documents(self):
        """Upload sample documents for demonstration"""
        sample_docs = {
            "financial_report_2024.md": """
# Financial Report 2024

## Company Performance
- Revenue: $2.3 billion (15% growth YoY)
- Profit Margin: 22%
- Market Cap: $15.6 billion
- Customer Acquisition Cost: $1,200
- Lifetime Value: $8,500
- Churn Rate: 2.3%

## Strategic Initiatives
- European market expansion
- AI product development  
- Strategic partnerships

## Risk Factors
- Market competition increasing
- Regulatory changes in EU
- Supply chain disruptions
""",
            "technical_spec_ai_platform.md": """
# Technical Specification: AI Platform

## Architecture Overview
- Microservices-based architecture
- Kubernetes orchestration  
- Azure Cloud infrastructure

## Core Components
1. **Data Processing Pipeline**
   - Real-time data ingestion
   - Batch processing capabilities
   - Data validation and cleaning

2. **Machine Learning Models**
   - Transformer architectures
   - Federated learning support
   - Model versioning and A/B testing

3. **API Gateway**
   - RESTful APIs
   - GraphQL support
   - Rate limiting and authentication

## Performance Targets
- 99.9% uptime SLA
- <100ms inference latency
- Support for 1M+ concurrent users
""",
            "market_analysis_q1.md": """
# Market Analysis Q1 2024

## Industry Trends
- AI adoption increased by 45% year-over-year
- Cloud migration accelerating
- Remote work tools in high demand

## Competitive Landscape
**Top 3 Competitors:**
1. TechCorp Inc. (35% market share)
2. Innovate Solutions (25% market share) 
3. Digital Systems (20% market share)

## Customer Segmentation
- Enterprise: 45% of revenue
- SMB: 35% of revenue  
- Education: 20% of revenue

## Growth Opportunities
- Asian market expansion
- Mobile-first solutions
- Industry-specific AI tools
""",
            "product_roadmap.md": """
# Product Roadmap 2024

## Q2 2024
- Mobile app v2.0 launch
- Enhanced AI features
- Performance optimization

## Q3 2024  
- Enterprise integration suite
- Advanced analytics dashboard
- API rate limit increases

## Q4 2024
- Industry-specific solutions
- International expansion
- Partner ecosystem launch

## Success Metrics
- User adoption rate > 60%
- Customer satisfaction > 4.5/5
- Revenue growth > 20%
""",
            "competitive_analysis_2024.md": """
# Competitive Analysis 2024

## Market Share Breakdown
- TechCorp Inc: 35% market share
- Innovate Solutions: 25% market share  
- Digital Systems: 20% market share
- Our Company: 15% market share
- Others: 5% market share

## Competitor Strengths
- **TechCorp**: Strong enterprise sales, global presence
- **Innovate Solutions**: Innovative product features, agile development
- **Digital Systems**: Cost-effective solutions, strong SMB focus

## Competitive Threats
- Price erosion in SMB segment
- New entrants in Asian markets
- Rapid feature copying by competitors

## Strategic Recommendations
- Differentiate through AI capabilities
- Strengthen enterprise partnerships
- Accelerate mobile platform development
"""
    }     
        
        uploaded_count = 0
        for filename, content in sample_docs.items():
            tags = {
                "document_type": filename.split('_')[0],
                "upload_date": "2025-01-15",
                "source": "internal"
            }
            
            if self.upload_text_as_document(content, filename, tags):
                uploaded_count += 1
        
        logger.info(f"Uploaded {uploaded_count} sample documents to Azure Blob Storage")
        return uploaded_count