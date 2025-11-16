import os
import uuid
from typing import List, Dict, Optional
from datetime import datetime
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.kernel_pydantic import KernelBaseModel, Field
import logging

from blob_connector import BlobStorageConnector
from chroma_manager import ChromaDBManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic Models for RAG System
class RetrievedDocument(KernelBaseModel):
    """Model representing a retrieved document"""
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: str = Field(..., description="Document source/file name")
    content: str = Field(..., description="Document content")
    relevance_score: float = Field(..., description="Relevance score 0-1")
    retrieval_agent: str = Field(..., description="Which agent retrieved this")
    retrieval_time: datetime = Field(default_factory=datetime.now)

class ResearchReport(KernelBaseModel):
    """Model representing a final research report"""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    topic: str = Field(..., description="Research topic")
    summary: str = Field(..., description="Executive summary")
    key_findings: List[str] = Field(..., description="Key findings")
    recommendations: List[str] = Field(..., description="Recommendations")
    sources: List[str] = Field(..., description="Source documents used")
    generated_by: str = Field(..., description="Synthesis agent name")
    generated_at: datetime = Field(default_factory=datetime.now)

class RAGSystemState(KernelBaseModel):
    """Central state for RAG system"""
    retrieved_documents: Dict[str, RetrievedDocument] = Field(default_factory=dict)
    current_research_topic: Optional[str] = None
    active_reports: Dict[str, ResearchReport] = Field(default_factory=dict)
    retrieval_metrics: Dict[str, int] = Field(default_factory=dict)

# Base RAG Agent with Semantic Kernel Functions
class RAGAgent:
    """Base class for RAG agents with Semantic Kernel integration"""
    
    def __init__(self, name: str, system_state: RAGSystemState, blob_connector: BlobStorageConnector, chroma_store: ChromaDBManager):
        self.name = name
        self.system_state = system_state
        self.blob_connector = blob_connector
        self.chroma_store = chroma_store
        
        # Initialize kernel
        self.kernel = Kernel()
        
        # Initialize Azure OpenAI service
        service_id = "chat_completion"
        
        # Get environment variables with fallbacks for demo
        deployment_name = os.getenv("AZURE_TEXTGENERATOR_DEPLOYMENT_NAME", "gpt-35-turbo")
        endpoint = os.getenv("AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT", "https://mock-openai.azure.com/")
        api_key = os.getenv("AZURE_TEXTGENERATOR_DEPLOYMENT_KEY", "mock-key")
        
        self.kernel.add_service(
            AzureChatCompletion(
                service_id=service_id,
                deployment_name=deployment_name,
                endpoint=endpoint,
                api_key=api_key
            )
        )

    @kernel_function(
        name="store_retrieved_document",
        description="Store a retrieved document in the system state"
    )
    def store_retrieved_document(self, source: str, content: str, relevance_score: float) -> str:
        """Store retrieved document and return document ID"""
        doc_id = f"{self.name.lower().replace(' ', '_')}_{len(self.system_state.retrieved_documents) + 1}"
        
        retrieved_doc = RetrievedDocument(
            document_id=doc_id,
            source=source,
            content=content,
            relevance_score=relevance_score,
            retrieval_agent=self.name
        )
        
        self.system_state.retrieved_documents[doc_id] = retrieved_doc
        return doc_id

# Specialized Retrieval Agents using ChatCompletionAgent
class FinancialRetrievalAgent:
    """Agent specializing in financial document retrieval and analysis"""
    
    def __init__(self, system_state: RAGSystemState, blob_connector: BlobStorageConnector, chroma_store: ChromaDBManager):
        self.name = "Financial_Analyst"
        self.system_state = system_state
        self.blob_connector = blob_connector
        self.chroma_store = chroma_store
        
        # Create the agent using Semantic Kernel's ChatCompletionAgent
        self.agent = ChatCompletionAgent(
            name=self.name,
            instructions="""
            You are a financial analyst specializing in financial documents, reports, and analysis.
            Your role is to retrieve and analyze financial documents to provide insights on:
            - Financial performance and metrics
            - Revenue trends and growth analysis
            - Profitability and margin analysis
            - Financial risks and opportunities
            - Strategic financial recommendations
            
            Always provide specific, data-driven insights and reference the actual content from documents.
            Focus on numerical data, financial indicators, and actionable business insights.
            """
        )
    
    async def retrieve_and_analyze(self, query: str) -> Dict:
        """Retrieve and analyze financial documents using Chroma semantic search"""
        try:
            # Use Chroma for semantic search
            search_results = await self.chroma_store.semantic_search(
                query=query, 
                collection_names=["financial"],
                top_k=3
            )
            
            if not search_results:
                return {
                    "agent": self.name,
                    "documents_found": 0,
                    "analysis": "No financial documents found matching the query.",
                    "key_insights": [],
                    "sources": [],
                    "retrieval_method": "semantic_search"
                }
            
            # Prepare documents for analysis
            documents_text = "\n\n".join([
                f"=== DOCUMENT: {result['filename']} ===\n" + 
                "\n".join([chunk['content'] for chunk in result['best_chunks']])
                for result in search_results
            ])
            
            # Use the agent to analyze the documents
            analysis_prompt = f"""
            RESEARCH QUERY: {query}
            
            RETRIEVED FINANCIAL DOCUMENTS:
            {documents_text}
            
            Please provide a comprehensive financial analysis including:
            1. Key financial metrics and performance indicators found
            2. Revenue trends and growth analysis
            3. Financial risks or opportunities identified
            4. Strategic recommendations based on the data
            5. Any data gaps or limitations in the available documents
            
            Focus on numerical data, financial indicators, and actionable business insights.
            Be specific and reference the actual content from the documents.
            """
            
            # For demo purposes, create a mock response
            response = ChatMessageContent(role="assistant", content=f"""
            Financial Analysis for: {query}
            
            Based on the retrieved financial documents, here are the key insights:
            
            1. **Financial Performance**: Found revenue growth of 15% YoY reaching $2.3 billion
            2. **Profitability**: Profit margin maintained at 22% with strong market cap of $15.6 billion
            3. **Strategic Initiatives**: European expansion and AI product development are key growth drivers
            4. **Risk Factors**: Increasing competition and regulatory changes noted
            
            Recommendations:
            - Continue investment in AI product development
            - Monitor European regulatory landscape closely
            - Diversify revenue streams to mitigate competition risks
            """)
            
            # Store retrieved documents
            stored_docs = []
            for result in search_results:
                # Combine chunks for storage
                combined_content = "\n".join([chunk['content'] for chunk in result['best_chunks']])
                doc_id = f"fin_{len(self.system_state.retrieved_documents) + 1}"
                retrieved_doc = RetrievedDocument(
                    document_id=doc_id,
                    source=result['filename'],
                    content=combined_content,
                    relevance_score=0.8,  # Simplified scoring
                    retrieval_agent=self.name
                )
                self.system_state.retrieved_documents[doc_id] = retrieved_doc
                stored_docs.append(doc_id)
            
            # Update metrics
            self.system_state.retrieval_metrics[self.name] = len(search_results)
            
            return {
                "agent": self.name,
                "documents_found": len(search_results),
                "analysis": str(response),
                "key_insights": [f"Found {len(search_results)} financial documents"],
                "sources": [result['filename'] for result in search_results],
                "stored_document_ids": stored_docs,
                "retrieval_method": "semantic_search"
            }
            
        except Exception as e:
            logger.error(f"Error in financial agent: {e}")
            return {
                "agent": self.name,
                "documents_found": 0,
                "analysis": f"Error during analysis: {e}",
                "key_insights": [],
                "sources": [],
                "retrieval_method": "semantic_search"
            }

class TechnicalRetrievalAgent:
    """Agent specializing in technical document retrieval and analysis"""
    
    def __init__(self, system_state: RAGSystemState, blob_connector: BlobStorageConnector, chroma_store: ChromaDBManager):
        self.name = "Technical_Analyst"
        self.system_state = system_state
        self.blob_connector = blob_connector
        self.chroma_store = chroma_store
        
        self.agent = ChatCompletionAgent(
            name=self.name,
            instructions="""
            You are a technical analyst specializing in technical documents, specifications, and architecture.
            Your role is to retrieve and analyze technical documents to provide insights on:
            - System architecture and design patterns
            - Technology stacks and frameworks
            - Performance characteristics and scalability
            - Security considerations and implementation
            - Technical recommendations and improvements
            
            Focus on technical specifications, architecture patterns, and implementation details.
            Be specific and reference the actual content from the documents.
            """
        )
    
    async def retrieve_and_analyze(self, query: str) -> Dict:
        """Retrieve and analyze technical documents using Chroma semantic search"""
        try:
            search_results = await self.chroma_store.semantic_search(
                query=query, 
                collection_names=["technical"],
                top_k=3
            )
            
            if not search_results:
                return {
                    "agent": self.name,
                    "documents_found": 0,
                    "analysis": "No technical documents found matching the query.",
                    "technical_specs": [],
                    "sources": [],
                    "retrieval_method": "semantic_search"
                }
            
            documents_text = "\n\n".join([
                f"=== DOCUMENT: {result['filename']} ===\n" + 
                "\n".join([chunk['content'] for chunk in result['best_chunks']])
                for result in search_results
            ])
            
            # Mock response for demo
            response = ChatMessageContent(role="assistant", content=f"""
            Technical Analysis for: {query}
            
            Based on the technical specifications found:
            
            1. **Architecture**: Microservices-based with Kubernetes orchestration
            2. **Core Components**: Data processing pipeline, ML models, and API gateway
            3. **Performance**: Targets include 99.9% uptime and <100ms inference latency
            4. **Scalability**: Designed for 1M+ concurrent users
            
            Technical Recommendations:
            - Implement advanced monitoring for microservices
            - Consider edge computing for lower latency
            - Enhance API rate limiting strategies
            """)
            
            # Store retrieved documents
            stored_docs = []
            for result in search_results:
                combined_content = "\n".join([chunk['content'] for chunk in result['best_chunks']])
                doc_id = f"tech_{len(self.system_state.retrieved_documents) + 1}"
                retrieved_doc = RetrievedDocument(
                    document_id=doc_id,
                    source=result['filename'],
                    content=combined_content,
                    relevance_score=0.8,
                    retrieval_agent=self.name
                )
                self.system_state.retrieved_documents[doc_id] = retrieved_doc
                stored_docs.append(doc_id)
            
            self.system_state.retrieval_metrics[self.name] = len(search_results)
            
            return {
                "agent": self.name,
                "documents_found": len(search_results),
                "analysis": str(response),
                "technical_specs": [f"Found {len(search_results)} technical documents"],
                "sources": [result['filename'] for result in search_results],
                "stored_document_ids": stored_docs,
                "retrieval_method": "semantic_search"
            }
            
        except Exception as e:
            logger.error(f"Error in technical agent: {e}")
            return {
                "agent": self.name,
                "documents_found": 0,
                "analysis": f"Error during analysis: {e}",
                "technical_specs": [],
                "sources": [],
                "retrieval_method": "semantic_search"
            }

class MarketRetrievalAgent:
    """Agent specializing in market research document retrieval and analysis"""
    
    def __init__(self, system_state: RAGSystemState, blob_connector: BlobStorageConnector, chroma_store: ChromaDBManager):
        self.name = "MarketAnalyst"
        self.system_state = system_state
        self.blob_connector = blob_connector
        self.chroma_store = chroma_store
        
        self.agent = ChatCompletionAgent(
            name=self.name,
            instructions="""
            You are a market research analyst specializing in market analysis, competitive intelligence, and industry trends.
            Your role is to retrieve and analyze market research documents to provide insights on:
            - Market trends and industry analysis
            - Competitive landscape and positioning
            - Customer insights and segmentation
            - Growth opportunities and market threats
            - Strategic market recommendations
            
            Focus on market dynamics, customer behavior, and competitive intelligence.
            Be specific and reference the actual content from the documents.
            """
        )
    
    async def retrieve_and_analyze(self, query: str) -> Dict:
        """Retrieve and analyze market research documents using Chroma semantic search"""
        try:
            search_results = await self.chroma_store.semantic_search(
                query=query, 
                collection_names=["market"],
                top_k=3
            )
            
            if not search_results:
                return {
                    "agent": self.name,
                    "documents_found": 0,
                    "analysis": "No market research documents found matching the query.",
                    "market_trends": [],
                    "sources": [],
                    "retrieval_method": "semantic_search"
                }
            
            documents_text = "\n\n".join([
                f"=== DOCUMENT: {result['filename']} ===\n" + 
                "\n".join([chunk['content'] for chunk in result['best_chunks']])
                for result in search_results
            ])
            
            # Mock response for demo
            response = ChatMessageContent(role="assistant", content=f"""
            Market Analysis for: {query}
            
            Market Insights from Research:
            
            1. **Industry Trends**: 45% YoY growth in AI adoption, cloud migration accelerating
            2. **Competitive Landscape**: Top 3 competitors hold 80% market share
            3. **Customer Segments**: Enterprise (45%), SMB (35%), Education (20%)
            4. **Growth Opportunities**: Asian market expansion, mobile-first solutions
            
            Strategic Recommendations:
            - Focus on industry-specific AI solutions
            - Expand mobile offerings for SMB segment
            - Explore partnerships in Asian markets
            """)
            
            # Store retrieved documents
            stored_docs = []
            for result in search_results:
                combined_content = "\n".join([chunk['content'] for chunk in result['best_chunks']])
                doc_id = f"market_{len(self.system_state.retrieved_documents) + 1}"
                retrieved_doc = RetrievedDocument(
                    document_id=doc_id,
                    source=result['filename'],
                    content=combined_content,
                    relevance_score=0.8,
                    retrieval_agent=self.name
                )
                self.system_state.retrieved_documents[doc_id] = retrieved_doc
                stored_docs.append(doc_id)
            
            self.system_state.retrieval_metrics[self.name] = len(search_results)
            
            return {
                "agent": self.name,
                "documents_found": len(search_results),
                "analysis": str(response),
                "market_trends": [f"Found {len(search_results)} market research documents"],
                "sources": [result['filename'] for result in search_results],
                "stored_document_ids": stored_docs,
                "retrieval_method": "semantic_search"
            }
            
        except Exception as e:
            logger.error(f"Error in market agent: {e}")
            return {
                "agent": self.name,
                "documents_found": 0,
                "analysis": f"Error during analysis: {e}",
                "market_trends": [],
                "sources": [],
                "retrieval_method": "semantic_search"
            }

# Synthesis Agent using SequentialOrchestration
class SynthesisAgent:
    """Agent that synthesizes information from all retrieval agents"""
    
    def __init__(self, system_state: RAGSystemState, blob_connector: BlobStorageConnector, chroma_store: ChromaDBManager):
        self.name = "SynthesisCoordinator"
        self.system_state = system_state
        self.blob_connector = blob_connector
        self.chroma_store = chroma_store
        
        self.agent = ChatCompletionAgent(
            name=self.name,
            instructions="""
            You are a synthesis coordinator that creates comprehensive research reports by combining insights from multiple specialized agents.
            
            Your role is to:
            1. Integrate findings from financial, technical, and market analysts
            2. Identify connections and patterns across different domains
            3. Provide holistic recommendations that consider multiple perspectives
            4. Highlight potential conflicts or synergies between different analyses
            5. Create executive summaries that business decision-makers can use
            
            Always provide specific, actionable insights that combine the specialized knowledge from all domains.
            """
        )
    
    async def generate_comprehensive_report(self, topic: str, agent_results: List[Dict]) -> ResearchReport:
        """Generate a comprehensive report using SequentialOrchestration pattern"""
        try:
            # Prepare agent analyses for synthesis
            analyses_text = "\n\n".join([
                f"=== {result['agent']} ANALYSIS ===\n{result.get('analysis', 'No analysis provided')}"
                for result in agent_results if result.get('analysis')
            ])
            
            synthesis_prompt = f"""
            RESEARCH TOPIC: {topic}
            
            SPECIALIZED AGENT ANALYSES:
            {analyses_text}
            
            Please generate a comprehensive research report that integrates all the specialized analyses:
            
            1. EXECUTIVE SUMMARY: Brief overview of key integrated findings
            2. INTEGRATED ANALYSIS: How financial, technical, and market insights connect
            3. CROSS-DOMAIN INSIGHTS: Patterns and relationships across different domains
            4. STRATEGIC RECOMMENDATIONS: Actionable advice that considers all perspectives
            5. RISKS AND OPPORTUNITIES: Comprehensive risk assessment and opportunity identification
            
            Focus on providing a holistic view that business leaders can use for decision-making.
            """
            
            # Mock response for demo
            response = ChatMessageContent(role="assistant", content=f"""
            COMPREHENSIVE RESEARCH REPORT: {topic}
            
            EXECUTIVE SUMMARY:
            This integrated analysis combines financial, technical, and market perspectives to provide a holistic view. Key findings indicate strong growth potential in AI-driven solutions, with opportunities in mobile platforms and Asian markets. Technical architecture supports scalability while financial metrics show healthy profitability.
            
            INTEGRATED ANALYSIS:
            - Financial strength supports technical innovation investments
            - Market trends align with current technical capabilities
            - Customer segmentation matches product roadmap priorities
            
            STRATEGIC RECOMMENDATIONS:
            1. Accelerate AI product development with focus on mobile platforms
            2. Expand into Asian markets with localized solutions
            3. Enhance technical infrastructure to support enterprise scaling
            4. Monitor competitive landscape for emerging threats
            
            RISKS AND OPPORTUNITIES:
            Opportunities: Mobile-first solutions, Asian market expansion, industry-specific AI
            Risks: Increasing competition, regulatory changes, supply chain dependencies
            """)
            
            # Get unique documents for sources
            unique_sources = list(set([
                doc.source for doc in self.system_state.retrieved_documents.values()
            ]))
            
            # Create research report
            report = ResearchReport(
                topic=topic,
                summary=str(response),
                key_findings=[
                    f"Integrated analysis from {len(agent_results)} specialized domains",
                    f"Based on {len(unique_sources)} source documents",
                    "Strong alignment between financial capacity and technical roadmap",
                    "Market opportunities match current strategic initiatives"
                ],
                recommendations=[
                    "Implement cross-functional initiatives based on integrated findings",
                    "Establish ongoing monitoring of identified risks and opportunities",
                    "Continue multi-domain analysis for strategic decisions",
                    "Prioritize mobile and Asian market expansion"
                ],
                sources=unique_sources,
                generated_by=self.name
            )
            
            # Store the report in system state
            self.system_state.active_reports[report.report_id] = report
            self.system_state.current_research_topic = topic
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return ResearchReport(
                topic=topic,
                summary="Error generating comprehensive report",
                key_findings=["System encountered an error during report generation"],
                recommendations=["Please check the system logs and try again"],
                sources=[],
                generated_by=self.name
            )