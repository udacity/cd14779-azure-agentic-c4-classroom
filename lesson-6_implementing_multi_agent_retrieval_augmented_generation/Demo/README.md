# Multi-Agent RAG System with ChromaDB & Azure Blob Storage

## 🚀 Overview

A sophisticated multi-agent Retrieval-Augmented Generation (RAG) system that leverages specialized AI agents to perform comprehensive research and analysis across multiple domains. This system combines the power of semantic search, Azure cloud services, and coordinated AI agents to deliver actionable business intelligence using Semantic Kernel 1.37.

## ✨ Key Features

- **🤖 Multi-Agent Architecture**: Three specialized agents (Financial, Technical, Market) working in parallel with Synthesis coordination
- **🔍 Semantic Search**: ChromaDB vector store for intelligent document retrieval and vector embeddings
- **☁️ Cloud Integration**: Azure Blob Storage for document management and Azure OpenAI for analysis
- **📊 Comprehensive Reporting**: Synthesis agent that integrates findings into actionable reports
- **⚡ Parallel Processing**: Asynchronous execution for optimal performance
- **📈 Performance Metrics**: Detailed analytics on retrieval effectiveness and agent performance
- **🔧 Semantic Kernel 1.37**: Built on Microsoft's latest Semantic Kernel framework

---

## 🏗️ System Architecture

### Multi-Agent RAG System Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Azure Blob    │    │   Multi-Agent    │    │   ChromaDB      │
│   Storage       │◄──►│   RAG System     │◄──►│   Vector Store  │
│                 │    │                  │    │                 │
│ • Document      │    │ • Financial      │    │ • Semantic      │
│   Repository    │    │   Agent          │    │   Search        │
│ • Sample        │    │ • Technical      │    │ • Document      │
│   Documents     │    │   Agent          │    │   Embeddings    │
└─────────────────┘    │ • Market Agent   │    └─────────────────┘
                       │ • Synthesis      │
                       │   Agent          │    ┌─────────────────┐
                       └──────────────────┘    │   Azure OpenAI  │
                            │                  │                 │
                            ▼                  │ • GPT-4         │
                       ┌──────────┐            │ • Analysis      │
                       │ Research │            │ • Synthesis     │
                       │  Report  │            └─────────────────┘
                       └──────────┘
```

### Detailed Workflow

1. **Document Ingestion**: Documents are loaded from Azure Blob Storage and chunked into semantic pieces
2. **Vector Storage**: Document chunks are stored in ChromaDB collections (financial, technical, market, general)
3. **Parallel Agent Processing**: Specialized agents simultaneously search and analyze relevant documents
4. **Semantic Synthesis**: Coordination agent integrates findings into comprehensive reports
5. **Result Delivery**: Formatted research reports with executive summaries and recommendations

## 🎯 Specialized Agents

### 1. **Financial Analyst Agent**
- **Focus**: Revenue, profit margins, growth metrics, financial risks, investment analysis
- **Documents**: Financial reports, earnings statements, budget analysis
- **Output**: Financial performance insights and strategic recommendations
- **Collection**: `financial_documents`

### 2. **Technical Analyst Agent**  
- **Focus**: System architecture, technology stack, performance metrics, scalability, security
- **Documents**: Technical specifications, architecture diagrams, API documentation
- **Output**: Technical assessments and improvement recommendations
- **Collection**: `technical_documents`

### 3. **Market Analyst Agent**
- **Focus**: Market trends, competitive landscape, customer insights, industry analysis
- **Documents**: Market research, competitive analysis, industry reports, customer segmentation
- **Output**: Market intelligence and growth opportunities
- **Collection**: `market_documents`

### 4. **Synthesis Coordinator Agent**
- **Role**: Integrates findings from all specialized agents using Semantic Kernel orchestration
- **Output**: Comprehensive research reports with executive summaries and cross-domain insights
- **Technology**: Semantic Kernel SequentialOrchestration pattern

## 📋 Prerequisites

### Required Services
- **Azure Account** with:
  - Azure Blob Storage (or mock for demo)
  - Azure OpenAI Service (GPT-35-turbo or GPT-4 deployment)
- **Python 3.8+**

### Environment Variables
Create a `.env` file with:
```env
# Azure Blob Storage (Optional for demo)
BLOB_CONNECTION_STRING=your_blob_connection_string
BLOB_CONTAINER_NAME=rag-documents

# Azure OpenAI
AZURE_TEXTGENERATOR_DEPLOYMENT_NAME=gpt-35-turbo
AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT=your_azure_openai_endpoint
AZURE_TEXTGENERATOR_DEPLOYMENT_KEY=your_azure_openai_key
```

**Note**: The system includes mock implementations for demo purposes when Azure services are not configured.

## 🛠️ Installation & Setup

1. **Clone and setup environment**
```bash
git clone <repository-url>
cd multi-agent-rag-system
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install semantic-kernel==1.37.0
pip install chromadb
pip install azure-storage-blob
pip install pypdf  # For future PDF support
```

3. **Run the demo**
```bash
python main_demo.py
```

## 📁 Project Structure

```
multi-agent-rag-system/
├── main_demo.py              # Main demo execution script
├── rag_agents.py             # Multi-agent RAG system implementation
├── blob_connector.py         # Azure Blob Storage integration
├── chroma_manager.py         # ChromaDB vector store management
├── README.md                 # This file
└── requirements.txt          # Python dependencies
```

### Core Components

- **`main_demo.py`**: Orchestrates the multi-agent system, manages research topics, and displays results
- **`rag_agents.py`**: Implements specialized agents using Semantic Kernel 1.37 ChatCompletionAgent
- **`blob_connector.py`**: Manages document storage and retrieval from Azure Blob Storage
- **`chroma_manager.py`**: Handles document chunking, vector storage, and semantic search operations

## 🎮 Usage

### Running the Complete Demo
The system automatically processes multiple research topics with built-in sample documents:

```python
research_topics = [
    "Company growth strategy and financial performance",
    "Technical architecture and AI platform development", 
    "Market competition and customer analysis"
]
```

### Custom Research Queries
Modify `main_demo.py` to add your own research topics:

```python
custom_topics = [
    "Your custom research topic here",
    "Another specific business question",
    "Industry trend analysis for next quarter"
]
```

### Sample Document Types
The system includes sample documents:
- `financial_report_2024.md` - Financial performance and metrics
- `technical_spec_ai_platform.md` - Architecture and technical specifications  
- `market_analysis_q1.md` - Market trends and competitive analysis
- `product_roadmap.md` - Strategic initiatives and planning

## 📊 Sample Output

### Agent Retrieval Results
```
🤖 Deploying 3 specialized agents with semantic search...

📊 SEMANTIC SEARCH RESULTS:
--------------------------------------------------

Financial_Analyst:
  📄 Documents Found: 2
  🔍 Retrieval Method: semantic_search  
  🔗 Sources: financial_report_2024.md, product_roadmap.md

Technical_Analyst:
  📄 Documents Found: 1
  🔍 Retrieval Method: semantic_search
  🔗 Sources: technical_spec_ai_platform.md

MarketAnalyst:
  📄 Documents Found: 2
  🔍 Retrieval Method: semantic_search
  🔗 Sources: market_analysis_q1.md, product_roadmap.md
```

### Comprehensive Research Report
```
🎯 COMPREHENSIVE RESEARCH REPORT
==================================================
Report ID: 890ecc6b
Topic: Company growth strategy and financial performance
Generated: 2025-01-15 14:30
By: SynthesisCoordinator

📋 EXECUTIVE SUMMARY:
This integrated analysis combines financial, technical, and market perspectives...
Revenue: $2.3 billion (15% growth YoY), Profit Margin: 22%, Market Cap: $15.6 billion

🔍 KEY FINDINGS:
1. Integrated analysis from 3 specialized domains
2. Based on 4 source documents
3. Strong alignment between financial capacity and technical roadmap
4. Market opportunities match current strategic initiatives

💡 RECOMMENDATIONS:
1. Implement cross-functional initiatives based on integrated findings
2. Establish ongoing monitoring of identified risks and opportunities
3. Continue multi-domain analysis for strategic decisions
4. Prioritize mobile and Asian market expansion

📚 SOURCES USED (4 documents):
- financial_report_2024.md
- technical_spec_ai_platform.md
- market_analysis_q1.md
- product_roadmap.md
```

## 🔧 Configuration Options

### Document Chunking (chroma_manager.py)
```python
chunk_size = 500      # Characters per chunk
overlap = 50          # Overlap between chunks
collection_types = ["financial", "technical", "market", "general"]
```

### Search Parameters (rag_agents.py)
```python
top_k = 3             # Documents per agent search
collection_names = ["financial", "technical", "market"]  # Collections to search
```

### Semantic Kernel Configuration
```python
# Agent initialization with Azure OpenAI
self.agent = ChatCompletionAgent(
    name=self.name,
    instructions="Domain-specific instructions...",
    service=AzureChatCompletion(...)
)
```

## 🚀 Performance Features

### Intelligent Document Processing
- **Smart Chunking**: Paragraph-based chunking with overlap for context preservation
- **Collection Assignment**: Automatic document classification using weighted term scoring
- **Semantic Search**: Vector similarity search with distance-based relevance scoring

### Parallel Processing Architecture
- **Concurrent Agent Execution**: All three specialized agents run simultaneously
- **Asynchronous Operations**: Non-blocking I/O for document retrieval and analysis
- **Optimized API Calls**: Efficient use of Azure OpenAI services

### Advanced Search Capabilities
- **Semantic Search**: Vector-based similarity matching
- **Hybrid Search**: Combination of semantic and keyword matching
- **Collection-specific Search**: Domain-targeted document retrieval
- **Relevance Scoring**: Distance-based relevance metrics (0-1 scale)

## 🛠️ Technical Implementation

### Semantic Kernel 1.37 Integration
```python
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.kernel_pydantic import BaseModel, Field
```

### ChromaDB Vector Store
- **Persistent Storage**: Local ChromaDB with automatic persistence
- **Collection Management**: Separate collections for different document types
- **Metadata Tracking**: Comprehensive document and chunk metadata

### Error Handling & Resilience
- **Mock Implementations**: Fallback when Azure services are unavailable
- **Graceful Degradation**: System continues with reduced functionality
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## 🛠️ Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   ```
   ⚠️  Missing environment variables. Using mock values for demo.
   ```
   **Solution**: System will use mock implementations. For full functionality, set Azure environment variables.

2. **ChromaDB Initialization**
   ```
   Error: Unable to initialize ChromaDB
   ```
   **Solution**: Ensure write permissions in the current directory for ChromaDB storage.

3. **Azure Service Connection**
   ```
   Error: Azure Blob Storage initialization failed
   ```
   **Solution**: System will use mock document storage. Check connection string if using real Azure services.

### Debug Mode
Enable detailed logging by modifying the logging configuration:

```python
logging.getLogger('semantic_kernel').setLevel(logging.DEBUG)
logging.getLogger('chromadb').setLevel(logging.DEBUG)
```

## 📈 Extension Opportunities

### Additional Specialized Agents
- **Legal Analyst**: Contract analysis and compliance monitoring
- **HR Analyst**: Workforce analytics and talent management
- **Operations Analyst**: Process optimization and efficiency analysis
- **Risk Analyst**: Risk assessment and mitigation strategies

### Enhanced Features
- **Real-time Data Integration**: Live market data and news feeds
- **Multi-modal Analysis**: Support for images, tables, and structured data
- **Custom Domain Adaptation**: Industry-specific fine-tuning and terminology
- **API Endpoints**: RESTful API for integration with other business systems
- **User Interface**: Web-based dashboard for result visualization
- **Advanced Analytics**: Trend analysis and predictive insights

### Storage & Database Options
- **Alternative Vector Stores**: Pinecone, Weaviate, or Qdrant integration
- **Cloud Storage**: AWS S3, Google Cloud Storage alternatives
- **Database Integration**: SQL database for structured data storage

## 🎯 Use Cases

### Business Intelligence
- Competitive market analysis
- Financial performance benchmarking
- Technology stack evaluation
- Strategic planning support

### Research & Development
- Technology landscape analysis
- Patent and innovation research
- Industry trend monitoring
- Product development insights

### Corporate Strategy
- Merger and acquisition analysis
- Market entry strategy development
- Risk assessment and mitigation
- Investment opportunity evaluation

## 🤝 Contributing

This multi-agent RAG system demonstrates advanced patterns in:
- Semantic Kernel 1.37 agent orchestration
- Vector database integration
- Cloud service integration
- Asynchronous multi-agent systems

Feel free to extend the system with additional agents, storage providers, or analysis capabilities.

---
