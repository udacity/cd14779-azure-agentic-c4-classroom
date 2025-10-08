import os
import uuid
from typing import List, Dict, Optional
from datetime import datetime
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from pydantic import BaseModel, Field
from blob_connector import BlobStorageConnector

# Pydantic Models for RAG System
class RetrievedDocument(BaseModel):
    """Model representing a retrieved document"""
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: str = Field(..., description="Document source/file name")
    content: str = Field(..., description="Document content")
    relevance_score: float = Field(..., description="Relevance score 0-1")
    retrieval_agent: str = Field(..., description="Which agent retrieved this")
    retrieval_time: datetime = Field(default_factory=datetime.now)

class ResearchReport(BaseModel):
    """Model representing a final research report"""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    topic: str = Field(..., description="Research topic")
    summary: str = Field(..., description="Executive summary")
    key_findings: List[str] = Field(..., description="Key findings")
    recommendations: List[str] = Field(..., description="Recommendations")
    sources: List[str] = Field(..., description="Source documents used")
    generated_by: str = Field(..., description="Synthesis agent name")
    generated_at: datetime = Field(default_factory=datetime.now)

class RAGSystemState(BaseModel):
    """Central state for RAG system"""
    retrieved_documents: Dict[str, RetrievedDocument] = Field(default_factory=dict)
    current_research_topic: Optional[str] = None
    active_reports: Dict[str, ResearchReport] = Field(default_factory=dict)
    retrieval_metrics: Dict[str, int] = Field(default_factory=dict)

# Base RAG Agent
class RAGAgent:
    """Base class for RAG agents with Azure Blob Storage integration"""
    
    def __init__(self, name: str, role: str, system_state: RAGSystemState, blob_connector: BlobStorageConnector):
        self.name = name
        self.role = role
        self.system_state = system_state
        self.blob_connector = blob_connector
        self.kernel = Kernel()
        
        # Initialize Azure OpenAI service
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="chat_completion",
                deployment_name=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
            )
        )
    
    async def retrieve_and_analyze(self, query: str, document_types: List[str] = None) -> Dict:
        raise NotImplementedError("Subclasses must implement this method")

# Specialized Retrieval Agents
class FinancialRetrievalAgent(RAGAgent):
    """Agent specializing in financial document retrieval and analysis"""
    
    def __init__(self, system_state: RAGSystemState, blob_connector: BlobStorageConnector):
        super().__init__("Financial Analyst", "Retrieve and analyze financial documents", system_state, blob_connector)
    
    async def retrieve_and_analyze(self, query: str, document_types: List[str] = None) -> Dict:
        """Retrieve and analyze financial documents from Azure Blob Storage"""
        
        # Search for financial documents in blob storage
        financial_keywords = ["revenue", "profit", "financial", "growth", "market", "investment"]
        search_terms = [query] + financial_keywords
        
        all_results = []
        for term in search_terms:
            results = self.blob_connector.search_documents_by_content(term, "md")
            all_results.extend(results)
        
        # Remove duplicates and get top results
        unique_results = {}
        for result in all_results:
            if result["filename"] not in unique_results:
                unique_results[result["filename"]] = result
            else:
                # Keep the highest relevance score
                if result["relevance_score"] > unique_results[result["filename"]]["relevance_score"]:
                    unique_results[result["filename"]] = result
        
        financial_docs = list(unique_results.values())
        financial_docs.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        if not financial_docs:
            return {
                "agent": self.name,
                "documents_found": 0,
                "analysis": "No financial documents found matching the query.",
                "key_insights": [],
                "sources": []
            }
        
        # Store retrieved documents in system state
        stored_docs = []
        for doc in financial_docs[:3]:  # Top 3 most relevant
            doc_id = f"fin_{len(self.system_state.retrieved_documents) + 1}"
            retrieved_doc = RetrievedDocument(
                document_id=doc_id,
                source=doc["filename"],
                content=doc["full_content"],
                relevance_score=doc["relevance_score"],
                retrieval_agent=self.name
            )
            self.system_state.retrieved_documents[doc_id] = retrieved_doc
            stored_docs.append(doc_id)
        
        # Analyze financial content using Azure OpenAI
        prompt = """
        You are a financial analyst. Analyze the following financial documents retrieved from our Azure Blob Storage and provide insights.

        RESEARCH QUERY: {{$query}}

        RETRIEVED FINANCIAL DOCUMENTS:
        {{$documents}}

        Please provide a comprehensive analysis including:
        1. Key financial metrics and performance indicators found
        2. Revenue trends and growth analysis
        3. Financial risks or opportunities identified
        4. Strategic recommendations based on the data
        5. Any data gaps or limitations in the available documents

        Focus on numerical data, financial indicators, and actionable business insights.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="financial_analysis",
            plugin_name="financial",
            prompt=prompt
        )
        
        documents_text = "\n\n".join([
            f"=== DOCUMENT: {doc['filename']} (Relevance: {doc['relevance_score']:.2f}) ===\n{doc['full_content']}" 
            for doc in financial_docs[:3]
        ])
        
        result = await self.kernel.invoke(
            function, 
            query=query,
            documents=documents_text
        )
        
        # Update metrics
        self.system_state.retrieval_metrics[self.name] = len(financial_docs)
        
        return {
            "agent": self.name,
            "documents_found": len(financial_docs),
            "analysis": str(result),
            "key_insights": self._extract_financial_insights(financial_docs),
            "sources": [doc["filename"] for doc in financial_docs[:3]],
            "stored_document_ids": stored_docs
        }
    
    def _extract_financial_insights(self, documents: List[Dict]) -> List[str]:
        """Extract key financial insights from documents"""
        insights = []
        financial_terms = ["revenue", "profit", "growth", "market share", "investment", "margin"]
        
        for doc in documents[:2]:
            content = doc["full_content"].lower()
            found_terms = [term for term in financial_terms if term in content]
            if found_terms:
                insights.append(f"Financial metrics ({', '.join(found_terms)}) in {doc['filename']}")
        
        return insights

class TechnicalRetrievalAgent(RAGAgent):
    """Agent specializing in technical document retrieval and analysis"""
    
    def __init__(self, system_state: RAGSystemState, blob_connector: BlobStorageConnector):
        super().__init__("Technical Analyst", "Retrieve and analyze technical documents", system_state, blob_connector)
    
    async def retrieve_and_analyze(self, query: str, document_types: List[str] = None) -> Dict:
        """Retrieve and analyze technical documents from Azure Blob Storage"""
        
        # Search for technical documents
        technical_keywords = ["technical", "architecture", "system", "api", "development", "infrastructure"]
        search_terms = [query] + technical_keywords
        
        all_results = []
        for term in search_terms:
            results = self.blob_connector.search_documents_by_content(term, "md")
            all_results.extend(results)
        
        # Remove duplicates and get top results
        unique_results = {}
        for result in all_results:
            if result["filename"] not in unique_results:
                unique_results[result["filename"]] = result
        
        technical_docs = list(unique_results.values())
        technical_docs.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        if not technical_docs:
            return {
                "agent": self.name,
                "documents_found": 0,
                "analysis": "No technical documents found matching the query.",
                "technical_specs": [],
                "sources": []
            }
        
        # Store retrieved documents in system state
        stored_docs = []
        for doc in technical_docs[:3]:
            doc_id = f"tech_{len(self.system_state.retrieved_documents) + 1}"
            retrieved_doc = RetrievedDocument(
                document_id=doc_id,
                source=doc["filename"],
                content=doc["full_content"],
                relevance_score=doc["relevance_score"],
                retrieval_agent=self.name
            )
            self.system_state.retrieved_documents[doc_id] = retrieved_doc
            stored_docs.append(doc_id)
        
        # Analyze technical content
        prompt = """
        You are a technical analyst. Analyze the following technical documents retrieved from Azure Blob Storage.

        RESEARCH QUERY: {{$query}}

        RETRIEVED TECHNICAL DOCUMENTS:
        {{$documents}}

        Please provide:
        1. Technical architecture and system overview
        2. Key technologies and frameworks used
        3. Performance characteristics and scalability
        4. Security considerations and implementation
        5. Technical recommendations and potential improvements

        Focus on technical specifications, architecture patterns, and implementation details.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="technical_analysis",
            plugin_name="technical",
            prompt=prompt
        )
        
        documents_text = "\n\n".join([
            f"=== DOCUMENT: {doc['filename']} (Relevance: {doc['relevance_score']:.2f}) ===\n{doc['full_content']}" 
            for doc in technical_docs[:3]
        ])
        
        result = await self.kernel.invoke(
            function, 
            query=query,
            documents=documents_text
        )
        
        self.system_state.retrieval_metrics[self.name] = len(technical_docs)
        
        return {
            "agent": self.name,
            "documents_found": len(technical_docs),
            "analysis": str(result),
            "technical_specs": self._extract_technical_specs(technical_docs),
            "sources": [doc["filename"] for doc in technical_docs[:3]],
            "stored_document_ids": stored_docs
        }
    
    def _extract_technical_specs(self, documents: List[Dict]) -> List[str]:
        """Extract technical specifications from documents"""
        specs = []
        tech_terms = ["architecture", "api", "performance", "security", "scalability", "kubernetes"]
        
        for doc in documents[:2]:
            content = doc["full_content"].lower()
            found_terms = [term for term in tech_terms if term in content]
            if found_terms:
                specs.append(f"Technical specs ({', '.join(found_terms)}) in {doc['filename']}")
        
        return specs

class MarketRetrievalAgent(RAGAgent):
    """Agent specializing in market research document retrieval and analysis"""
    
    def __init__(self, system_state: RAGSystemState, blob_connector: BlobStorageConnector):
        super().__init__("Market Analyst", "Retrieve and analyze market research documents", system_state, blob_connector)
    
    async def retrieve_and_analyze(self, query: str, document_types: List[str] = None) -> Dict:
        """Retrieve and analyze market research documents from Azure Blob Storage"""
        
        # Search for market research documents
        market_keywords = ["market", "customer", "competition", "trend", "analysis", "growth"]
        search_terms = [query] + market_keywords
        
        all_results = []
        for term in search_terms:
            # Search in both markdown and JSON files
            results_md = self.blob_connector.search_documents_by_content(term, "md")
            results_json = self.blob_connector.search_documents_by_content(term, "json")
            all_results.extend(results_md + results_json)
        
        # Remove duplicates
        unique_results = {}
        for result in all_results:
            if result["filename"] not in unique_results:
                unique_results[result["filename"]] = result
        
        market_docs = list(unique_results.values())
        market_docs.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        if not market_docs:
            return {
                "agent": self.name,
                "documents_found": 0,
                "analysis": "No market research documents found matching the query.",
                "market_trends": [],
                "sources": []
            }
        
        # Store retrieved documents in system state
        stored_docs = []
        for doc in market_docs[:3]:
            doc_id = f"market_{len(self.system_state.retrieved_documents) + 1}"
            retrieved_doc = RetrievedDocument(
                document_id=doc_id,
                source=doc["filename"],
                content=doc["full_content"],
                relevance_score=doc["relevance_score"],
                retrieval_agent=self.name
            )
            self.system_state.retrieved_documents[doc_id] = retrieved_doc
            stored_docs.append(doc_id)
        
        # Analyze market research content
        prompt = """
        You are a market research analyst. Analyze the following market research documents from Azure Blob Storage.

        RESEARCH QUERY: {{$query}}

        RETRIEVED MARKET RESEARCH DOCUMENTS:
        {{$documents}}

        Please provide:
        1. Market trends and industry analysis
        2. Competitive landscape overview
        3. Customer insights and segmentation
        4. Growth opportunities and market threats
        5. Strategic market recommendations

        Focus on market dynamics, customer behavior, and competitive intelligence.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="market_analysis",
            plugin_name="market",
            prompt=prompt
        )
        
        documents_text = "\n\n".join([
            f"=== DOCUMENT: {doc['filename']} (Relevance: {doc['relevance_score']:.2f}) ===\n{doc['full_content']}" 
            for doc in market_docs[:3]
        ])
        
        result = await self.kernel.invoke(
            function, 
            query=query,
            documents=documents_text
        )
        
        self.system_state.retrieval_metrics[self.name] = len(market_docs)
        
        return {
            "agent": self.name,
            "documents_found": len(market_docs),
            "analysis": str(result),
            "market_trends": self._extract_market_trends(market_docs),
            "sources": [doc["filename"] for doc in market_docs[:3]],
            "stored_document_ids": stored_docs
        }
    
    def _extract_market_trends(self, documents: List[Dict]) -> List[str]:
        """Extract market trends from documents"""
        trends = []
        market_terms = ["market", "trend", "competition", "customer", "growth", "opportunity"]
        
        for doc in documents[:2]:
            content = doc["full_content"].lower()
            found_terms = [term for term in market_terms if term in content]
            if found_terms:
                trends.append(f"Market insights ({', '.join(found_terms)}) in {doc['filename']}")
        
        return trends

# Synthesis Agent
class SynthesisAgent(RAGAgent):
    """Agent that synthesizes information from all retrieval agents"""
    
    def __init__(self, system_state: RAGSystemState, blob_connector: BlobStorageConnector):
        super().__init__("Synthesis Coordinator", "Synthesize findings from all agents", system_state, blob_connector)
    
    async def generate_comprehensive_report(self, topic: str, agent_results: List[Dict]) -> ResearchReport:
        """Generate a comprehensive report by synthesizing all agent findings"""
        
        prompt = """
        You are a synthesis coordinator. Create a comprehensive research report by combining insights from multiple specialized agents.

        RESEARCH TOPIC: {{$topic}}

        AGENT FINDINGS:
        {{$agent_findings}}

        RETRIEVED DOCUMENTS SUMMARY:
        {{$documents_summary}}

        Please generate a comprehensive report including:
        1. Executive Summary: Brief overview of key findings
        2. Key Findings: Detailed insights from each domain
        3. Integrated Analysis: How different aspects connect and impact each other
        4. Recommendations: Actionable recommendations based on the combined insights
        5. Limitations: Any gaps in information or areas needing further research

        Ensure the report is well-structured, insightful, and actionable for business decision-makers.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="synthesis_report",
            plugin_name="synthesis",
            prompt=prompt
        )
        
        # Prepare agent findings
        agent_findings = "\n\n".join([
            f"=== {result['agent']} ===\nDocuments Found: {result['documents_found']}\nAnalysis: {result['analysis']}"
            for result in agent_results
        ])
        
        # Prepare documents summary
        documents_summary = "\n".join([
            f"- {doc_id}: {doc.source} (Relevance: {doc.relevance_score:.2f})"
            for doc_id, doc in self.system_state.retrieved_documents.items()
        ])
        
        result = await self.kernel.invoke(
            function,
            topic=topic,
            agent_findings=agent_findings,
            documents_summary=documents_summary
        )
        
        # Create research report
        report = ResearchReport(
            topic=topic,
            summary="Comprehensive analysis generated from multiple data sources",
            key_findings=[
                f"Findings from {len(agent_results)} specialized agents",
                f"Based on {len(self.system_state.retrieved_documents)} retrieved documents",
                "Integrated multi-domain analysis"
            ],
            recommendations=[
                "Consider all domain perspectives in decision-making",
                "Validate findings with additional data sources",
                "Monitor key metrics identified in the analysis"
            ],
            sources=list(set([doc.source for doc in self.system_state.retrieved_documents.values()])),
            generated_by=self.name
        )
        
        # Store the report in system state
        self.system_state.active_reports[report.report_id] = report
        self.system_state.current_research_topic = topic
        
        return report