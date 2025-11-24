# Multi-Agent RAG System with Sequential Orchestration & Risk Assessment

## 🚀 Overview

An advanced multi-agent Retrieval-Augmented Generation (RAG) system that leverages **sequential orchestration** and specialized AI agents to perform comprehensive research and analysis across multiple domains. This enhanced system now includes **risk assessment capabilities** and uses Semantic Kernel 1.37's SequentialOrchestration for coordinated agent workflows with Azure cloud services and intelligent document retrieval.

## ✨ Enhanced Features

- **🤖 Sequential Agent Orchestration**: Six specialized agents working in coordinated sequence (Document Loader, Financial, Technical, Market, Risk Assessment, Synthesis)
- **🎯 Risk Assessment Integration**: New specialized agent for comprehensive risk analysis and mitigation strategies
- **🔍 Advanced Semantic Search**: ChromaDB vector store with risk collection and enhanced document classification
- **☁️ Cloud Integration**: Azure Blob Storage for document management and Azure OpenAI for analysis
- **📊 Comprehensive Reporting**: Synthesis agent that integrates findings including risk assessment into actionable reports
- **⚡ Robust Error Handling**: Partial failure handling, validation, and fallback reporting
- **💾 Report Persistence**: Automatic JSON export of research reports with timestamps
- **🔧 Semantic Kernel 1.37**: Built on Microsoft's latest Semantic Kernel framework with SequentialOrchestration

---

## 🏗️ Enhanced System Architecture

### Sequential Multi-Agent RAG System Flow

```
┌─────────────────┐    ┌─────────────────────────────────────┐    ┌─────────────────┐
│   Azure Blob    │    │     Sequential Multi-Agent          │    │   ChromaDB      │
│   Storage       │◄──►│         RAG System                 │◄──►│   Vector Store  │
│                 │    │                                     │    │                 │
│ • Document      │    │  ┌─────────────────────────────┐    │    │ • Semantic      │
│   Repository    │    │  │  Sequential Orchestration   │    │    │   Search        │
│ • Sample        │    │  └─────────────────────────────┘    │    │ • Document      │
│   Documents     │    │                 │                  │    │   Embeddings    │
└─────────────────┘    │    ┌─────────────┴─────────────┐    │    └─────────────────┘
                       │    │   Specialized Agents      │    │
                       │    └─────────────┬─────────────┘    │    ┌─────────────────┐
                       │        Sequential Flow              │    │   Azure OpenAI  │
                       └─────────────────────────────────────┘    │                 │
                                    │                            │ • GPT-4         │
                                    ▼                            │ • Analysis      │
                       ┌──────────────────┐                      │ • Synthesis     │
                       │  Research Report │                      └─────────────────┘
                       │  with Risk       │
                       │  Assessment      │
                       └──────────────────┘
```

### Sequential Workflow

1. **Document Ingestion**: Documents loaded from Azure Blob Storage and intelligently chunked
2. **Vector Storage**: Document chunks stored in ChromaDB collections (financial, technical, market, **risk**, general)
3. **Sequential Agent Processing**: Specialized agents process in coordinated sequence:
   - **Document Loader** → **Financial Analyst** → **Technical Analyst** → **Market Analyst** → **Risk Assessment Analyst** → **Synthesis Coordinator**
4. **Risk-Integrated Synthesis**: Coordination agent integrates all findings including comprehensive risk assessment
5. **Result Delivery**: Formatted research reports with executive summaries, recommendations, and risk mitigation strategies

## 🎯 Enhanced Specialized Agents

### 1. **Document Loader Agent**
- **Focus**: Identify relevant documents, prepare content, provide document overview
- **Role**: First step in sequential workflow, sets context for all subsequent agents

### 2. **Financial Analyst Agent**
- **Focus**: Revenue, profit margins, growth metrics, financial risks, investment analysis
- **Documents**: Financial reports, earnings statements, budget analysis
- **Output**: Financial performance insights and strategic recommendations
- **Collection**: `financial_documents`

### 3. **Technical Analyst Agent**  
- **Focus**: System architecture, technology stack, performance metrics, scalability, security
- **Documents**: Technical specifications, architecture diagrams, API documentation
- **Output**: Technical assessments and improvement recommendations
- **Collection**: `technical_documents`

### 4. **Market Analyst Agent**
- **Focus**: Market trends, competitive landscape, customer insights, industry analysis
- **Documents**: Market research, competitive analysis, industry reports, customer segmentation
- **Output**: Market intelligence and growth opportunities
- **Collection**: `market_documents`

### 5. **Risk Assessment Analyst Agent** 🆕
- **Focus**: Operational risks, compliance requirements, security vulnerabilities, market threats, mitigation strategies
- **Documents**: Risk assessment reports, compliance documentation, security audits
- **Output**: Risk identification, impact assessment, and mitigation recommendations
- **Collection**: `risk_documents` 🆕

### 6. **Synthesis Coordinator Agent**
- **Role**: Integrates findings from all specialized agents including risk assessment using Semantic Kernel SequentialOrchestration
- **Output**: Comprehensive research reports with executive summaries, cross-domain insights, and risk mitigation strategies
- **Technology**: Semantic Kernel SequentialOrchestration pattern

## 📋 Prerequisites

### Required Services
- **Azure Account** with:
  - Azure Blob Storage (or mock for demo)
  - Azure OpenAI Service (GPT-4o-mini or GPT-4 deployment)
- **Python 3.8+**

### Environment Variables
Create a `.env` file with:
```env
# Azure Blob Storage (Optional for demo)
BLOB_CONNECTION_STRING=your_blob_connection_string
BLOB_CONTAINER_NAME=rag-documents

# Azure OpenAI
AZURE_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_DEPLOYMENT_ENDPOINT=your_azure_openai_endpoint
AZURE_DEPLOYMENT_KEY=your_azure_openai_key
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

3. **Run the enhanced demo**
```bash
python main_solution.py
```

## 📁 Enhanced Project Structure

```
multi-agent-rag-system/
├── main_solution.py              # COMPLETE: Enhanced main orchestration system
├── chroma_manager.py             # COMPLETE: Enhanced vector store with risk collection
├── blob_connector.py             # COMPLETE: Azure Blob Storage with risk documents
├── README.md                     # This enhanced documentation
└── requirements.txt              # Python dependencies
```

### Enhanced Core Components

- **`main_solution.py`**: Orchestrates sequential multi-agent system with risk assessment, manages research topics, and displays results
- **`chroma_manager.py`**: Enhanced with risk collection, improved classification, and better semantic search
- **`blob_connector.py`**: Manages document storage and retrieval with comprehensive risk assessment sample documents

## 🎮 Usage

### Running the Enhanced Demo
The system automatically processes multiple research topics including risk-focused analysis:

```python
research_topics = [
    "Company growth strategy and financial performance",
    "Technical architecture and AI platform development", 
    "Market competition and customer analysis",
    "Risk assessment and mitigation strategies"  # 🆕 NEW risk-focused topic
]
```

### Custom Research Queries
Modify `main_solution.py` to add your own research topics:

```python
custom_topics = [
    "Your custom research topic here",
    "Risk analysis for new market entry",  # 🆕 Risk-focused queries
    "Technology security assessment and compliance",
    "Business continuity and disaster recovery planning"
]
```

### Enhanced Sample Document Types
The system includes comprehensive sample documents:
- `financial_report_2024.md` - Financial performance and metrics
- `technical_spec_ai_platform.md` - Architecture and technical specifications  
- `market_analysis_q1.md` - Market trends and competitive analysis
- `product_roadmap.md` - Strategic initiatives and planning
- `risk_assessment_report.md` - 🆕 Comprehensive risk analysis and mitigation strategies

## 📊 Enhanced Sample Output

### Sequential Agent Execution
```
🤖 Created 6 specialized agents for this analysis
✅ Runtime started successfully
🚀 Invoking SequentialOrchestration...

# Document_Loader
[Document identification and preparation...]

# Financial_Analyst  
[Financial metrics and performance analysis...]

# Technical_Analyst
[Technical architecture assessment...]

# Market_Analyst
[Market trends and competitive analysis...]

# Risk_Assessment_Analyst  🆕
[Risk identification and mitigation strategies...]

# Synthesis_Coordinator
[Comprehensive report generation with risk integration...]
```

### Enhanced Research Report with Risk Assessment
```
🎯 COMPREHENSIVE RESEARCH REPORT
======================================================================
Report ID: report_a1b2c3d4
Topic: Company growth strategy and financial performance
Generated: 2025-01-15 14:30
By: SequentialOrchestration

📋 EXECUTIVE SUMMARY:
This integrated analysis combines financial, technical, market, and risk perspectives...
Includes comprehensive risk assessment with mitigation strategies for identified vulnerabilities.

🔍 KEY FINDINGS:
1. Sequential analysis completed by 6 specialized agents 🆕
2. Analyzed 5 source documents including risk assessment 🆕
3. Used Semantic Kernel SequentialOrchestration
4. Found documents in collections: financial, technical, market, risk 🆕
5. Includes comprehensive risk assessment 🆕

💡 RECOMMENDATIONS:
1. Implement cross-functional initiatives based on integrated findings
2. Establish ongoing monitoring of identified opportunities and risks 🆕
3. Continue multi-agent analysis for strategic decisions
4. Prioritize implementation of risk mitigation strategies 🆕
5. Validate findings with additional market research

📚 SOURCES USED (5 documents):
- financial_report_2024.md
- technical_spec_ai_platform.md
- market_analysis_q1.md
- product_roadmap.md
- risk_assessment_report.md 🆕

💾 Report saved to: research_report_a1b2c3d4_20250115_143045.json 🆕
```

## 🔧 Enhanced Configuration Options

### Document Classification (chroma_manager.py)
```python
# Enhanced with risk term scoring
risk_terms = {
    "risk": 3, "threat": 3, "vulnerability": 3, "mitigation": 3,
    "compliance": 3, "security": 2, "cyber": 2, "breach": 3
}
collection_types = ["financial", "technical", "market", "risk", "general"]  # 🆕
```

### Sequential Orchestration Parameters
```python
# Agent sequence in main_solution.py
agents_sequence = [
    "Document_Loader", "Financial_Analyst", "Technical_Analyst",
    "Market_Analyst", "Risk_Assessment_Analyst", "Synthesis_Coordinator"  # 🆕
]
```

### Search Parameters
```python
top_k = 2             # Documents per agent search
collection_names = ["financial", "technical", "market", "risk"]  # 🆕 Enhanced collections
```

### Semantic Kernel Configuration
```python
# Enhanced agent initialization with risk assessment
risk_agent = ChatCompletionAgent(
    name="Risk_Assessment_Analyst",
    instructions="Risk assessment specialist focusing on operational, technical, and market risks...",
    service=AzureChatCompletion(...)
)
```

## 🚀 Enhanced Performance Features

### Intelligent Document Processing
- **Smart Chunking**: Paragraph-based chunking with overlap for context preservation
- **Enhanced Classification**: Risk term scoring with 20+ specialized keywords for better document categorization
- **Collection Assignment**: Automatic document classification using weighted term scoring across 5 domains
- **Semantic Search**: Vector similarity search with distance-based relevance scoring across all collections

### Sequential Processing Architecture
- **Coordinated Agent Execution**: Six specialized agents process in optimal sequence
- **Context Building**: Each agent builds upon previous analyses for comprehensive insights
- **Risk Integration**: Risk assessment naturally integrated between market analysis and synthesis
- **Asynchronous Operations**: Non-blocking I/O for document retrieval and analysis

### Advanced Search Capabilities
- **Semantic Search**: Vector-based similarity matching across all collections
- **Risk-Aware Retrieval**: Specialized search in risk collection for threat identification 🆕
- **Collection-specific Search**: Domain-targeted document retrieval including risk domain
- **Relevance Scoring**: Distance-based relevance metrics (0-1 scale)

### Enhanced Error Handling & Resilience 🆕
- **Agent Validation**: Pre-execution validation of all agent configurations
- **Partial Failure Handling**: Graceful degradation when individual agents fail
- **Fallback Reporting**: Comprehensive reporting even when orchestration encounters issues
- **Report Persistence**: Automatic JSON export with timestamps for later analysis

## 🛠️ Technical Implementation

### Semantic Kernel 1.37 SequentialOrchestration
```python
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, SequentialOrchestration
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
```

### Enhanced ChromaDB Vector Store
- **Risk Collection**: Dedicated collection for risk assessment documents 🆕
- **Persistent Storage**: Local ChromaDB with automatic persistence
- **Enhanced Metadata**: Comprehensive document and chunk metadata with risk classification
- **Smart Retrieval**: Improved semantic search across all domains including risk

### Robust Error Handling 🆕
```python
# Enhanced error handling with partial failure management
async def handle_partial_failure(self, research_topic: str, 
                               successful_agents: List[str], 
                               failed_agent: str, 
                               error_message: str) -> ResearchReport:
    # Creates comprehensive reports even when agents fail
```

### Report Persistence 🆕
```python
def save_report_to_file(self, report: ResearchReport, filename: str = None) -> str:
    # Automatically saves reports as JSON with timestamps
    # Enables later analysis and comparison
```

## 🛠️ Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   ```
   ⚠️  Using mock Azure OpenAI values for demo
   ```
   **Solution**: System will use mock implementations. For full functionality, set Azure environment variables.

2. **ChromaDB Initialization**
   ```
   Error: Unable to initialize ChromaDB
   ```
   **Solution**: Ensure write permissions in the current directory for ChromaDB storage.

3. **Sequential Orchestration Timeout**
   ```
   ⏰ Orchestration timed out - creating timeout report...
   ```
   **Solution**: System creates comprehensive timeout reports. Increase timeout in `run_sequential_analysis` if needed.

4. **Agent Validation Failures**
   ```
   ❌ Agent validation failed, skipping this analysis
   ```
   **Solution**: Check agent configurations and Azure OpenAI service availability.

### Debug Mode
Enable detailed logging by modifying the logging configuration:

```python
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger('semantic_kernel').setLevel(logging.DEBUG)
logging.getLogger('chromadb').setLevel(logging.DEBUG)
```

## 📈 Extension Opportunities

### Additional Specialized Agents
- **Compliance Analyst**: Regulatory compliance and legal requirements monitoring
- **Environmental Analyst**: Sustainability and environmental impact assessment
- **Supply Chain Analyst**: Logistics and supply chain risk analysis
- **Geopolitical Analyst**: Political and country risk assessment

### Enhanced Features
- **Real-time Risk Monitoring**: Live threat intelligence feeds and risk indicators
- **Multi-modal Risk Analysis**: Support for security footage, network logs, and sensor data
- **Predictive Risk Modeling**: Machine learning for risk prediction and early warning
- **Compliance Automation**: Automated regulatory compliance checking and reporting
- **API Endpoints**: RESTful API for integration with enterprise risk management systems
- **Risk Dashboard**: Web-based visualization of risk assessments and mitigation progress

### Storage & Database Options
- **Alternative Vector Stores**: Pinecone, Weaviate, or Qdrant integration for scale
- **Cloud Storage**: AWS S3, Google Cloud Storage alternatives
- **Risk Database Integration**: SQL database for structured risk data and historical analysis

## 🎯 Enhanced Use Cases

### Enterprise Risk Management
- Comprehensive risk assessment and mitigation planning
- Regulatory compliance monitoring and reporting
- Business continuity and disaster recovery planning
- Cybersecurity threat analysis and response planning

### Business Intelligence with Risk Focus
- Competitive market analysis with risk assessment
- Financial performance benchmarking with risk factors
- Technology stack evaluation with security considerations
- Strategic planning with integrated risk management

### Research & Development with Risk Awareness
- Technology landscape analysis with vulnerability assessment
- Innovation research with intellectual property risk analysis
- Industry trend monitoring with emerging risk identification
- Product development insights with safety and compliance risks

### Corporate Strategy with Risk Integration
- Merger and acquisition analysis with due diligence risk assessment
- Market entry strategy development with country risk analysis
- Investment opportunity evaluation with risk-adjusted returns
- Strategic initiative planning with risk mitigation strategies

## 🤝 Contributing

This enhanced multi-agent RAG system demonstrates advanced patterns in:
- Semantic Kernel 1.37 sequential orchestration
- Risk assessment integration in AI workflows
- Vector database integration with specialized collections
- Cloud service integration with robust error handling
- Sequential multi-agent systems with context building

Feel free to extend the system with additional specialized agents, enhanced risk assessment capabilities, or integration with enterprise risk management platforms.

---
