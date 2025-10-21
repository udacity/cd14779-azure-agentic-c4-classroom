import os
import uuid
from typing import List, Dict, Optional
from datetime import datetime
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from pydantic import BaseModel, Field
from blob_connector import BlobStorageConnector
from chroma_manager import ChromaDBManager

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
    
    def __init__(self, name: str, role: str, system_state: RAGSystemState, blob_connector: BlobStorageConnector, chroma_manager: ChromaDBManager):
        self.name = name
        self.role = role
        self.system_state = system_state
        self.blob_connector = blob_connector
        self.chroma_manager = chroma_manager
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
    
    def __init__(self, system_state: RAGSystemState, blob_connector: BlobStorageConnector, chroma_manager: ChromaDBManager):
        super().__init__("Financial Analyst", "Retrieve and analyze financial documents", system_state, blob_connector, chroma_manager)
    
    async def retrieve_and_analyze(self, query: str, document_types: List[str] = None) -> Dict:
        """Retrieve and analyze financial documents using ChromaDB semantic search"""
        
        # Use ChromaDB for semantic search
        search_results = self.chroma_manager.semantic_search(
            query=query, 
            collection_names=["financial"],
            n_results=5
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
        
        # Store retrieved documents in system state (avoid duplicates)
        stored_docs = []
        relevance_scores = []

        for result in search_results:
            # Check if this document is already stored
            existing_doc_id = None
            for doc_id, existing_doc in self.system_state.retrieved_documents.items():
                if existing_doc.source == result["filename"] and existing_doc.retrieval_agent == self.name:
                    existing_doc_id = doc_id
                    break
            
            if existing_doc_id:
                # Update existing document with better relevance score if needed
                relevance_score = max(0.1, min(1.0, 1.0 - (result["min_distance"] / 2.0)))  # Minimum 0.1 to avoid 0 scores
                if relevance_score > self.system_state.retrieved_documents[existing_doc_id].relevance_score:
                    self.system_state.retrieved_documents[existing_doc_id].relevance_score = relevance_score
                stored_docs.append(existing_doc_id)
                relevance_scores.append(relevance_score)
            else:
                # Create new document entry
                doc_id = f"fin_{len(self.system_state.retrieved_documents) + 1}"
                relevance_score = max(0.1, min(1.0, 1.0 - (result["min_distance"] / 2.0)))  # Minimum 0.1 to avoid 0 scores
                
                retrieved_doc = RetrievedDocument(
                    document_id=doc_id,
                    source=result["filename"],
                    content="\n".join([chunk["content"] for chunk in result["best_chunks"]]),
                    relevance_score=relevance_score,
                    retrieval_agent=self.name
                )
                self.system_state.retrieved_documents[doc_id] = retrieved_doc
                stored_docs.append(doc_id)
                relevance_scores.append(relevance_score)
        
        # Analyze financial content using Azure OpenAI
        prompt = """
        You are a financial analyst. Analyze the following financial documents and provide insights.

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
        Be specific and reference the actual content from the documents.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="financial_analysis",
            plugin_name="financial",
            prompt=prompt
        )
        
        documents_text = "\n\n".join([
            f"=== DOCUMENT: {result['filename']} (Relevance: {relevance_scores[i]:.2f}) ===\n" +
            "\n".join([chunk["content"] for chunk in result["best_chunks"]])
            for i, result in enumerate(search_results)
        ])
        
        result = await self.kernel.invoke(
            function, 
            query=query,
            documents=documents_text
        )
        
        # Update metrics
        self.system_state.retrieval_metrics[self.name] = len(search_results)
        
        return {
            "agent": self.name,
            "documents_found": len(search_results),
            "analysis": str(result),
            "key_insights": self._extract_financial_insights(search_results),
            "sources": [result["filename"] for result in search_results],
            "stored_document_ids": stored_docs,
            "relevance_scores": relevance_scores,
            "retrieval_method": "semantic_search"
        }
    
    def _extract_financial_insights(self, documents: List[Dict]) -> List[str]:
        """Extract key financial insights from documents"""
        insights = []
        financial_terms = ["revenue", "profit", "growth", "market share", "investment", "margin", "earnings", "financial"]
        
        for doc in documents[:2]:
            content = "\n".join([chunk["content"] for chunk in doc["best_chunks"]]).lower()
            found_terms = [term for term in financial_terms if term in content]
            if found_terms:
                insights.append(f"Financial metrics ({', '.join(found_terms)}) in {doc['filename']}")
        
        return insights if insights else ["General financial analysis conducted"]

class TechnicalRetrievalAgent(RAGAgent):
    """Agent specializing in technical document retrieval and analysis"""
    
    def __init__(self, system_state: RAGSystemState, blob_connector: BlobStorageConnector, chroma_manager: ChromaDBManager):
        super().__init__("Technical Analyst", "Retrieve and analyze technical documents", system_state, blob_connector, chroma_manager)
    
    async def retrieve_and_analyze(self, query: str, document_types: List[str] = None) -> Dict:
        """Retrieve and analyze technical documents using ChromaDB semantic search"""
        
        # Use ChromaDB for semantic search
        search_results = self.chroma_manager.semantic_search(
            query=query, 
            collection_names=["technical"],
            n_results=5
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
        
        # Store retrieved documents in system state (avoid duplicates)
        stored_docs = []
        relevance_scores = []

        for result in search_results:
            # Check if this document is already stored
            existing_doc_id = None
            for doc_id, existing_doc in self.system_state.retrieved_documents.items():
                if existing_doc.source == result["filename"] and existing_doc.retrieval_agent == self.name:
                    existing_doc_id = doc_id
                    break
            
            if existing_doc_id:
                # Update existing document with better relevance score if needed
                relevance_score = max(0.1, min(1.0, 1.0 - (result["min_distance"] / 2.0)))  # Minimum 0.1 to avoid 0 scores
                if relevance_score > self.system_state.retrieved_documents[existing_doc_id].relevance_score:
                    self.system_state.retrieved_documents[existing_doc_id].relevance_score = relevance_score
                stored_docs.append(existing_doc_id)
                relevance_scores.append(relevance_score)
            else:
                # Create new document entry
                doc_id = f"tech_{len(self.system_state.retrieved_documents) + 1}"
                relevance_score = max(0.1, min(1.0, 1.0 - (result["min_distance"] / 2.0)))  # Minimum 0.1 to avoid 0 scores
                
                retrieved_doc = RetrievedDocument(
                    document_id=doc_id,
                    source=result["filename"],
                    content="\n".join([chunk["content"] for chunk in result["best_chunks"]]),
                    relevance_score=relevance_score,
                    retrieval_agent=self.name
                )
                self.system_state.retrieved_documents[doc_id] = retrieved_doc
                stored_docs.append(doc_id)
                relevance_scores.append(relevance_score)
        
        # Analyze technical content
        prompt = """
        You are a technical analyst. Analyze the following technical documents.

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
        Be specific and reference the actual content from the documents.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="technical_analysis",
            plugin_name="technical",
            prompt=prompt
        )
        
        documents_text = "\n\n".join([
            f"=== DOCUMENT: {result['filename']} (Relevance: {relevance_scores[i]:.2f}) ===\n" +
            "\n".join([chunk["content"] for chunk in result["best_chunks"]])
            for i, result in enumerate(search_results)
        ])
        
        result = await self.kernel.invoke(
            function, 
            query=query,
            documents=documents_text
        )
        
        self.system_state.retrieval_metrics[self.name] = len(search_results)
        
        return {
            "agent": self.name,
            "documents_found": len(search_results),
            "analysis": str(result),
            "technical_specs": self._extract_technical_specs(search_results),
            "sources": [result["filename"] for result in search_results],
            "stored_document_ids": stored_docs,
            "relevance_scores": relevance_scores,
            "retrieval_method": "semantic_search"
        }
    
    def _extract_technical_specs(self, documents: List[Dict]) -> List[str]:
        """Extract technical specifications from documents"""
        specs = []
        tech_terms = ["architecture", "api", "performance", "security", "scalability", "kubernetes", "technical", "system"]
        
        for doc in documents[:2]:
            content = "\n".join([chunk["content"] for chunk in doc["best_chunks"]]).lower()
            found_terms = [term for term in tech_terms if term in content]
            if found_terms:
                specs.append(f"Technical specs ({', '.join(found_terms)}) in {doc['filename']}")
        
        return specs if specs else ["General technical analysis conducted"]

class MarketRetrievalAgent(RAGAgent):
    """Agent specializing in market research document retrieval and analysis"""
    
    def __init__(self, system_state: RAGSystemState, blob_connector: BlobStorageConnector, chroma_manager: ChromaDBManager):
        super().__init__("Market Analyst", "Retrieve and analyze market research documents", system_state, blob_connector, chroma_manager)
    
    async def retrieve_and_analyze(self, query: str, document_types: List[str] = None) -> Dict:
        """Retrieve and analyze market research documents using ChromaDB semantic search"""
        
        # Use ChromaDB for semantic search
        search_results = self.chroma_manager.semantic_search(
            query=query, 
            collection_names=["market"],
            n_results=5
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
        
        # Store retrieved documents in system state (avoid duplicates)
        stored_docs = []
        relevance_scores = []

        for result in search_results:
            # Check if this document is already stored
            existing_doc_id = None
            for doc_id, existing_doc in self.system_state.retrieved_documents.items():
                if existing_doc.source == result["filename"] and existing_doc.retrieval_agent == self.name:
                    existing_doc_id = doc_id
                    break
            
            if existing_doc_id:
                # Update existing document with better relevance score if needed
                relevance_score = max(0.1, min(1.0, 1.0 - (result["min_distance"] / 2.0)))  # Minimum 0.1 to avoid 0 scores
                if relevance_score > self.system_state.retrieved_documents[existing_doc_id].relevance_score:
                    self.system_state.retrieved_documents[existing_doc_id].relevance_score = relevance_score
                stored_docs.append(existing_doc_id)
                relevance_scores.append(relevance_score)
            else:
                # Create new document entry
                doc_id = f"market_{len(self.system_state.retrieved_documents) + 1}"
                relevance_score = max(0.1, min(1.0, 1.0 - (result["min_distance"] / 2.0)))  # Minimum 0.1 to avoid 0 scores
                
                retrieved_doc = RetrievedDocument(
                    document_id=doc_id,
                    source=result["filename"],
                    content="\n".join([chunk["content"] for chunk in result["best_chunks"]]),
                    relevance_score=relevance_score,
                    retrieval_agent=self.name
                )
                self.system_state.retrieved_documents[doc_id] = retrieved_doc
                stored_docs.append(doc_id)
                relevance_scores.append(relevance_score)
        
        # Analyze market research content
        prompt = """
        You are a market research analyst. Analyze the following market research documents.

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
        Be specific and reference the actual content from the documents.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="market_analysis",
            plugin_name="market",
            prompt=prompt
        )
        
        documents_text = "\n\n".join([
            f"=== DOCUMENT: {result['filename']} (Relevance: {relevance_scores[i]:.2f}) ===\n" +
            "\n".join([chunk["content"] for chunk in result["best_chunks"]])
            for i, result in enumerate(search_results)
        ])
        
        result = await self.kernel.invoke(
            function, 
            query=query,
            documents=documents_text
        )
        
        self.system_state.retrieval_metrics[self.name] = len(search_results)
        
        return {
            "agent": self.name,
            "documents_found": len(search_results),
            "analysis": str(result),
            "market_trends": self._extract_market_trends(search_results),
            "sources": [result["filename"] for result in search_results],
            "stored_document_ids": stored_docs,
            "relevance_scores": relevance_scores,
            "retrieval_method": "semantic_search"
        }
    
    def _extract_market_trends(self, documents: List[Dict]) -> List[str]:
        """Extract market trends from documents"""
        trends = []
        market_terms = ["market", "trend", "competition", "customer", "growth", "opportunity", "analysis", "industry"]
        
        for doc in documents[:2]:
            content = "\n".join([chunk["content"] for chunk in doc["best_chunks"]]).lower()
            found_terms = [term for term in market_terms if term in content]
            if found_terms:
                trends.append(f"Market insights ({', '.join(found_terms)}) in {doc['filename']}")
        
        return trends if trends else ["General market analysis conducted"]

# Synthesis Agent
class SynthesisAgent(RAGAgent):
    """Agent that synthesizes information from all retrieval agents"""
    
    def __init__(self, system_state: RAGSystemState, blob_connector: BlobStorageConnector, chroma_manager: ChromaDBManager):
        super().__init__("Synthesis Coordinator", "Synthesize findings from all agents", system_state, blob_connector, chroma_manager)
    
    async def generate_comprehensive_report(self, topic: str, agent_results: List[Dict]) -> ResearchReport:
        """Generate a comprehensive report using actual AI analysis"""
        
        # Extract actual analyses from agent results
        analyses = []
        for result in agent_results:
            if result.get('analysis'):
                # Extract the actual text from Semantic Kernel result
                analysis_text = str(result['analysis'])
                # Clean up the analysis text to get the actual content
                if hasattr(analysis_text, 'value'):
                    analysis_text = analysis_text.value
                analyses.append(f"=== {result['agent']} Analysis ===\n{analysis_text}")
        
        prompt = """
        You are a synthesis coordinator. Create a comprehensive research report by combining insights from multiple specialized agents.

        RESEARCH TOPIC: {{$topic}}

        AGENT ANALYSES:
        {{$agent_analyses}}

        RETRIEVED DOCUMENTS SUMMARY:
        {{$documents_summary}}

        Please generate a comprehensive report with SPECIFIC insights including:
        1. Executive Summary: Concrete overview of key findings from the analyses
        2. Key Findings: Specific insights from each domain with supporting evidence
        3. Integrated Analysis: How different aspects connect and impact each other
        4. Recommendations: Actionable recommendations based on the combined insights
        5. Limitations: Any gaps in information or areas needing further research

        Use the actual analysis content provided by each specialist agent. Be specific and data-driven.
        Focus on providing actionable insights that business decision-makers can use.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="synthesis_report",
            plugin_name="synthesis",
            prompt=prompt
        )
        
        # Use actual agent analyses
        agent_analyses = "\n\n".join(analyses) if analyses else "No detailed analyses available from agents."
        
        # Prepare documents summary
        unique_documents = {}
        for doc in self.system_state.retrieved_documents.values():
            if doc.source not in unique_documents or doc.relevance_score > unique_documents[doc.source].relevance_score:
                unique_documents[doc.source] = doc
        
        documents_summary = "\n".join([
            f"- {doc.source}: Relevance {doc.relevance_score:.2f}"
            for doc in list(unique_documents.values())[:10]  # Limit to top 10
        ])
        
        result = await self.kernel.invoke(
            function,
            topic=topic,
            agent_analyses=agent_analyses,
            documents_summary=documents_summary
        )
        
        # Parse the actual AI response for the report
        analysis_result = str(result)
        if hasattr(analysis_result, 'value'):
            analysis_result = analysis_result.value
        
        # Extract key parts from the analysis for the report
        summary = analysis_result
        if len(analysis_result) > 500:
            # Try to find a good cutoff point
            sentences = analysis_result.split('. ')
            if len(sentences) > 3:
                summary = '. '.join(sentences[:3]) + '.'
            else:
                summary = analysis_result[:497] + "..."
        
        # Create a more detailed research report using the actual analysis
        report = ResearchReport(
            topic=topic,
            summary=summary,
            key_findings=[
                f"Comprehensive analysis by {len(agent_results)} specialized agents",
                f"Based on {len(unique_documents)} unique documents with average relevance {sum(doc.relevance_score for doc in unique_documents.values())/len(unique_documents):.2f}",
                "Integrated multi-domain perspective"
            ],
            recommendations = [
                f"Prioritize initiatives from {len(agent_results)} domain analyses",
                f"Validate findings against {len(unique_documents)} source documents",
                "Establish cross-functional teams to implement multi-domain insights"
            ],
            sources=list(unique_documents.keys()),
            generated_by=self.name
        )
        
        # Store the report in system state
        self.system_state.active_reports[report.report_id] = report
        self.system_state.current_research_topic = topic
        
        return report

# ADD YOUR NEW AGENT CLASS HERE
class CompetitiveIntelligenceAgent(RAGAgent):
    """Agent specializing in competitive intelligence and market positioning"""
    
    def __init__(self, system_state: RAGSystemState, blob_connector: BlobStorageConnector, chroma_manager: ChromaDBManager):
        super().__init__("Competitive Intelligence Analyst", "Analyze competitive landscape and market positioning", system_state, blob_connector, chroma_manager)
    
    async def retrieve_and_analyze(self, query: str, document_types: List[str] = None) -> Dict:
        """Retrieve and analyze competitive intelligence documents"""
        
        # Use ChromaDB for semantic search
        search_results = self.chroma_manager.semantic_search(
            query=query, 
            collection_names=["market","competitive"],
            n_results=8
        )
        
        if not search_results:
            return {
                "agent": self.name,
                "documents_found": 0,
                "analysis": "No competitive intelligence documents found matching the query.",
                "competitive_insights": [],
                "sources": [],
                "retrieval_method": "semantic_search"
            }
        
        # Store retrieved documents in system state
        stored_docs = []
        relevance_scores = []

        for result in search_results:
            # Check if this document is already stored
            existing_doc_id = None
            for doc_id, existing_doc in self.system_state.retrieved_documents.items():
                if existing_doc.source == result["filename"] and existing_doc.retrieval_agent == self.name:
                    existing_doc_id = doc_id
                    break
            
            if existing_doc_id:
                relevance_score = max(0.1, 1 - result["min_distance"])
                if relevance_score > self.system_state.retrieved_documents[existing_doc_id].relevance_score:
                    self.system_state.retrieved_documents[existing_doc_id].relevance_score = relevance_score
                stored_docs.append(existing_doc_id)
                relevance_scores.append(relevance_score)
            else:
                doc_id = f"comp_{len(self.system_state.retrieved_documents) + 1}"
                relevance_score = max(0.1, 1 - result["min_distance"])
                
                retrieved_doc = RetrievedDocument(
                    document_id=doc_id,
                    source=result["filename"],
                    content="\n".join([chunk["content"] for chunk in result["best_chunks"]]),
                    relevance_score=relevance_score,
                    retrieval_agent=self.name
                )
                self.system_state.retrieved_documents[doc_id] = retrieved_doc
                stored_docs.append(doc_id)
                relevance_scores.append(relevance_score)
        
        # Analyze competitive intelligence content
        prompt = """
        You are a competitive intelligence analyst. Analyze the following competitive documents.

        RESEARCH QUERY: {{$query}}

        RETRIEVED COMPETITIVE INTELLIGENCE DOCUMENTS:
        {{$documents}}

        Please provide:
        1. Competitive landscape overview and market share analysis
        2. Key competitor strengths and weaknesses
        3. Competitive threats and opportunities
        4. Strategic positioning recommendations
        5. Market differentiation opportunities

        Focus on competitive dynamics, market positioning, and strategic advantages.
        Be specific and reference the actual content from the documents.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="competitive_analysis",
            plugin_name="competitive",
            prompt=prompt
        )
        
        documents_text = "\n\n".join([
            f"=== DOCUMENT: {result['filename']} (Relevance: {relevance_scores[i]:.2f}) ===\n" +
            "\n".join([chunk["content"] for chunk in result["best_chunks"]])
            for i, result in enumerate(search_results)
        ])
        
        result = await self.kernel.invoke(
            function, 
            query=query,
            documents=documents_text
        )
        
        self.system_state.retrieval_metrics[self.name] = len(search_results)
        
        return {
            "agent": self.name,
            "documents_found": len(search_results),
            "analysis": str(result),
            "competitive_insights": self._extract_competitive_insights(search_results),
            "sources": [result["filename"] for result in search_results],
            "stored_document_ids": stored_docs,
            "relevance_scores": relevance_scores,
            "retrieval_method": "semantic_search"
        }
    
    def _extract_competitive_insights(self, documents: List[Dict]) -> List[str]:
        """Extract competitive insights from documents"""
        insights = []
        competitive_terms = ["competition", "competitor", "market share", "competitive", "advantage", "threat", "strength"]
        
        for doc in documents[:2]:
            content = "\n".join([chunk["content"] for chunk in doc["best_chunks"]]).lower()
            found_terms = [term for term in competitive_terms if term in content]
            if found_terms:
                insights.append(f"Competitive factors ({', '.join(found_terms)}) in {doc['filename']}")
        
        return insights if insights else ["General competitive analysis conducted"]