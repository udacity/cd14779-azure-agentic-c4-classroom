import asyncio
import os
import uuid
import logging
import warnings
import json
from typing import List, Dict
from datetime import datetime
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, SequentialOrchestration
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.contents import ChatMessageContent

from blob_connector import BlobStorageConnector
from chroma_manager import ChromaDBManager

# SUPPRESS VERBOSE LOGGING
warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("azure").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("semantic_kernel").setLevel(logging.WARNING)
logging.getLogger("in_process_runtime").setLevel(logging.WARNING)
logging.getLogger("in_process_runtime.events").setLevel(logging.WARNING)

from dotenv import load_dotenv

load_dotenv()

class ResearchReport(KernelBaseModel):
    """Model representing a final research report using KernelBaseModel"""
    report_id: str
    topic: str
    summary: str
    key_findings: List[str] = []
    recommendations: List[str] = []
    sources: List[str] = []
    generated_by: str = "SequentialOrchestration"
    generated_at: datetime = datetime.now()

class SequentialRAGOrchestration:
    """Multi-agent RAG system using Semantic Kernel SequentialOrchestration"""
    
    def __init__(self):
        # Initialize storage components
        self.blob_connector = BlobStorageConnector()
        self.chroma_store = ChromaDBManager()
        
        # Initialize shared kernel
        self.kernel = Kernel()
        
        # Azure OpenAI service configuration
        deployment_name = os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-4o-mini")
        endpoint = os.getenv("AZURE_DEPLOYMENT_ENDPOINT", "https://mock-openai.azure.com/")
        api_key = os.getenv("AZURE_DEPLOYMENT_KEY", "mock-key")
        
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="azure_rag_chat",
                deployment_name=deployment_name,
                endpoint=endpoint,
                api_key=api_key
            )
        )

    def create_sequential_agents(self) -> List[ChatCompletionAgent]:
        """Create specialized agents for sequential orchestration"""
        
        # Document Loader Agent
        document_agent = ChatCompletionAgent(
            name="Document_Loader",
            instructions="""
            You are a document preparation specialist. Your role is to:
            1. Identify relevant documents for the research topic
            2. Load and prepare document content for analysis
            3. Ensure documents are properly categorized
            4. Provide a document overview to the next agent
            
            Focus on identifying key documents from financial, technical, market, and risk collections.
            Provide a brief summary of available documents and their relevance.
            Keep your response focused and under 200 words.
            """,
            service=self.kernel.get_service("azure_rag_chat")
        )
        
        # Financial Analyst Agent
        financial_agent = ChatCompletionAgent(
            name="Financial_Analyst",
            instructions="""
            You are a financial analyst specializing in financial documents and analysis.
            Your expertise includes:
            - Financial performance metrics and analysis
            - Revenue trends and growth analysis  
            - Profitability and margin analysis
            - Financial risks and opportunities
            
            Analyze the documents from a financial perspective and provide data-driven insights.
            Focus on numerical data, financial indicators, and actionable business insights.
            Keep your response focused and under 200 words.
            Build upon the document analysis provided.
            """,
            service=self.kernel.get_service("azure_rag_chat")
        )
        
        # Technical Analyst Agent
        technical_agent = ChatCompletionAgent(
            name="Technical_Analyst",
            instructions="""
            You are a technical analyst specializing in technical documents and architecture.
            Your expertise includes:
            - System architecture and design patterns
            - Technology stacks and frameworks
            - Performance characteristics and scalability
            - Technical recommendations and improvements
            
            Analyze the documents from a technical perspective and provide implementation insights.
            Focus on technical specifications, architecture patterns, and implementation details.
            Keep your response focused and under 200 words.
            Build upon previous financial and document analysis.
            """,
            service=self.kernel.get_service("azure_rag_chat")
        )
        
        # Market Analyst Agent
        market_agent = ChatCompletionAgent(
            name="Market_Analyst",
            instructions="""
            You are a market research analyst specializing in market analysis and competitive intelligence.
            Your expertise includes:
            - Market trends and industry analysis
            - Competitive landscape and positioning
            - Customer insights and segmentation
            - Growth opportunities and market threats
            
            Analyze the documents from a market perspective and provide strategic insights.
            Focus on market dynamics, customer behavior, and competitive intelligence.
            Keep your response focused and under 200 words.
            Build upon previous financial and technical analysis.
            """,
            service=self.kernel.get_service("azure_rag_chat")
        )

        # Risk Assessment Agent - COMPLETED
        risk_agent = ChatCompletionAgent(
            name="Risk_Assessment_Analyst",
            instructions="""
            You are a risk assessment specialist focusing on identifying and evaluating potential risks.
            Your expertise includes:
            - Operational risks and compliance requirements
            - Market risks and external threats
            - Technical risks and security vulnerabilities
            - Financial risks and mitigation strategies
            
            Analyze the documents from a risk perspective and identify potential threats and vulnerabilities.
            Focus on risk identification, impact assessment, and preliminary mitigation recommendations.
            Keep your response focused and under 200 words.
            Build upon previous financial, technical, and market analysis.
            """,
            service=self.kernel.get_service("azure_rag_chat")
        )
        
        # Synthesis Coordinator Agent (updated to include risk assessment)
        synthesis_agent = ChatCompletionAgent(
            name="Synthesis_Coordinator",
            instructions="""
            You are a synthesis coordinator that creates comprehensive research reports.
            Your role is to integrate findings from all specialized agents and create a final report.
            
            Create a comprehensive research report with:
            1. Executive Summary
            2. Integrated Analysis (combining financial, technical, market, and risk insights)
            3. Key Findings
            4. Strategic Recommendations
            5. Risk Assessment with mitigation strategies
            
            Provide a holistic view that business leaders can use for decision-making.
            Use all previous analyses as context for your synthesis.
            """,
            service=self.kernel.get_service("azure_rag_chat")
        )
        
        # Return all agents including the new risk agent - COMPLETED
        return [document_agent, financial_agent, technical_agent, market_agent, risk_agent, synthesis_agent]

    async def load_documents(self):
        """Load documents to ChromaDB if not already loaded in the database"""
        print("🔄 Checking document availability in Chroma vector store...")
        
        # Check if documents are already in ChromaDB by trying to get collection stats
        try:
            stats = await self.chroma_store.get_collection_stats()
            total_docs = sum(stat.get('document_count', 0) for stat in stats.values())
            
            if total_docs > 0:
                print(f"📚 Found {total_docs} existing documents in ChromaDB")
                return
        except Exception:
            # If we can't get stats, assume we need to load documents
            pass
        
        print("📁 Uploading and loading sample documents...")
        
        documents = self.blob_connector.list_documents()
        if not documents:
            print("📁 Uploading sample documents...")
            self.blob_connector.upload_sample_documents()
            documents = self.blob_connector.list_documents()
        
        total_chunks = 0
        for doc_name in documents:
            content = self.blob_connector.get_document_content(doc_name)
            if content:
                collection_type = self.chroma_store.determine_collection(doc_name, content)
                chunks_added = await self.chroma_store.chunk_and_store_document(
                    doc_name, content, collection_type
                )
                total_chunks += chunks_added
                print(f"  ✅ Loaded {doc_name} to {collection_type} collection")
        
        print(f"🎉 Loaded {len(documents)} documents with {total_chunks} chunks")

    async def search_relevant_documents(self, research_topic: str) -> List[Dict]:
        """Search for relevant documents across all collections"""
        return await self.chroma_store.semantic_search(
            query=research_topic,
            collection_names=["financial", "technical", "market", "risk"],
            top_k=2
        )

    def agent_response_callback(self, message: ChatMessageContent) -> None:
        """Callback to observe agent responses"""
        print(f"# {message.name}")
        print(f"{message.content}\n")

    async def run_sequential_analysis(self, research_topic: str) -> ResearchReport:
        """Run research analysis using SequentialOrchestration"""
        print(f"\n🔍 RESEARCH TOPIC: {research_topic}")
        print("=" * 60)
        
        # Ensure documents are available
        await self.load_documents()
        
        # Search for relevant documents for THIS specific topic
        search_results = await self.search_relevant_documents(research_topic)
        document_context = self._prepare_document_context(search_results)
        
        # Create sequential agents
        agents = self.create_sequential_agents()
        
        print(f"🤖 Created {len(agents)} specialized agents for this analysis")
        
        # Create SequentialOrchestration with callback
        sequential_orchestration = SequentialOrchestration(
            members=agents,
            agent_response_callback=self.agent_response_callback,
        )
        
        # Set up runtime
        runtime = InProcessRuntime()
        
        try:
            # Start runtime
            runtime.start()
            print("✅ Runtime started successfully")
            
            # Updated orchestration task to include the new risk agent - COMPLETED
            orchestration_task = f"""
            RESEARCH TOPIC: {research_topic}
            
            AVAILABLE DOCUMENTS:
            {document_context}
            
            Please analyze this research topic through the sequential workflow:
            1. Document Loader: Identify key documents and their relevance
            2. Financial Analyst: Analyze financial metrics and performance
            3. Technical Analyst: Assess technical architecture and capabilities  
            4. Market Analyst: Evaluate market trends and competition
            5. Risk Assessment Analyst: Identify and evaluate potential risks
            6. Synthesis Coordinator: Create comprehensive final report
            
            Each agent builds upon the previous analysis.
            """
            
            print("🚀 Invoking SequentialOrchestration...")
            
            # Invoke the orchestration
            orchestration_result = await sequential_orchestration.invoke(
                task=orchestration_task,
                runtime=runtime
            )
            
            print("⏳ Waiting for orchestration to complete...")
            
            # Get the final result with timeout
            final_output = await asyncio.wait_for(orchestration_result.get(), timeout=120.0)
            
            print("✅ Sequential orchestration completed successfully")
            
            # Extract sources from search results
            sources = list(set([result['filename'] for result in search_results]))
            
            # Create research report
            report = ResearchReport(
                report_id=f"report_{uuid.uuid4().hex[:8]}",
                topic=research_topic,
                summary=str(final_output),
                key_findings=[
                    f"Sequential analysis completed by {len(agents)} specialized agents",
                    f"Analyzed {len(sources)} source documents",
                    "Used Semantic Kernel SequentialOrchestration",
                    f"Found documents in collections: {', '.join(set(r['collection'] for r in search_results))}",
                    "Includes comprehensive risk assessment"
                ],
                recommendations=[
                    "Implement cross-functional initiatives based on integrated findings",
                    "Establish ongoing monitoring of identified opportunities",
                    "Continue multi-agent analysis for strategic decisions",
                    "Validate findings with additional market research",
                    "Implement risk mitigation strategies identified"
                ],
                sources=sources,
                generated_by="SequentialOrchestration"
            )
            
            return report
            
        except asyncio.TimeoutError:
            logger.error("Sequential orchestration timed out")
            return await self._create_timeout_report(research_topic, search_results)
        except Exception as e:
            logger.error(f"Error in sequential orchestration: {e}")
            import traceback
            traceback.print_exc()
            return await self._create_fallback_report(research_topic, search_results)
        finally:
            # Stop runtime
            try:
                await runtime.stop_when_idle()
                print("✅ Runtime stopped successfully")
            except Exception as e:
                logger.warning(f"Error stopping runtime: {e}")

    def _prepare_document_context(self, search_results: List[Dict]) -> str:
        """Prepare document context for the orchestration"""
        if not search_results:
            return "No relevant documents found for this research topic."
        
        document_groups = {}
        for result in search_results:
            filename = result['filename']
            if filename not in document_groups:
                document_groups[filename] = {
                    'filename': filename,
                    'collection': result['collection'],
                    'content': []
                }
            if result['best_chunks']:
                document_groups[filename]['content'].append(result['best_chunks'][0]['content'][:300] + "...")
        
        context = "RELEVANT DOCUMENTS FOR ANALYSIS:\n"
        context += "=" * 50 + "\n"
        
        for filename, info in document_groups.items():
            context += f"\n📄 {filename} ({info['collection'].upper()} COLLECTION)\n"
            for content in info['content'][:1]:
                context += f"   {content}\n"
        
        context += "\n" + "=" * 50
        return context

    async def _create_timeout_report(self, research_topic: str, search_results: List[Dict]) -> ResearchReport:
        """Create a report when orchestration times out"""
        print("⏰ Orchestration timed out - creating timeout report...")
        
        sources = list(set([result['filename'] for result in search_results]))
        collections = list(set([result['collection'] for result in search_results]))
        
        summary = f"""
        RESEARCH REPORT: {research_topic}
        
        EXECUTIVE SUMMARY:
        Analysis initiated for {research_topic} but the sequential orchestration process timed out.
        The system identified {len(sources)} relevant documents across {len(collections)} domains.
        
        STATUS: Analysis incomplete due to timeout
        DOCUMENTS AVAILABLE: {', '.join(sources)}
        DOMAINS COVERED: {', '.join(collections)}
        
        RECOMMENDATIONS:
        1. Review the document contents manually for immediate insights
        2. Consider simplifying the research query
        3. Check system resources and API availability
        4. Retry with a shorter timeout or fewer agents
        """
        
        return ResearchReport(
            report_id=f"timeout_{uuid.uuid4().hex[:8]}",
            topic=research_topic,
            summary=summary,
            key_findings=[
                f"Orchestration timed out during processing",
                f"Identified {len(sources)} relevant documents",
                f"Coverage across {len(collections)} domains: {', '.join(collections)}",
                "Manual document review recommended for detailed insights"
            ],
            recommendations=[
                "Review system configuration and API availability",
                "Simplify the research query or reduce agent complexity",
                "Check Azure OpenAI service status and quotas",
                "Consider manual analysis of identified documents"
            ],
            sources=sources,
            generated_by="TimeoutHandler"
        )

    async def _create_fallback_report(self, research_topic: str, search_results: List[Dict]) -> ResearchReport:
        """Create a fallback report when orchestration fails"""
        print("🔄 Using fallback analysis method...")
        
        sources = list(set([result['filename'] for result in search_results]))
        collections = list(set([result['collection'] for result in search_results]))
        
        summary = f"""
        COMPREHENSIVE RESEARCH REPORT: {research_topic}
        
        EXECUTIVE SUMMARY:
        This analysis examines {research_topic} based on {len(sources)} relevant documents 
        from {len(collections)} specialized collections. The documents provide insights into 
        financial performance, technical capabilities, market positioning, and risk factors.
        
        KEY INSIGHTS:
        • Multiple document sources available for comprehensive analysis
        • Coverage across {', '.join(collections)} domains
        • Direct document analysis performed due to orchestration constraints
        
        RECOMMENDATIONS:
        1. Review the specific document contents for detailed insights
        2. Consider expanding analysis with additional data sources
        3. Validate findings through targeted market research
        4. Conduct dedicated risk assessment based on available documents
        
        NOTE: This report was generated using fallback analysis methods.
        """
        
        return ResearchReport(
            report_id=f"fallback_{uuid.uuid4().hex[:8]}",
            topic=research_topic,
            summary=summary,
            key_findings=[
                f"Analyzed {len(sources)} source documents across {len(collections)} domains",
                f"Document collections: {', '.join(collections)}",
                "Fallback analysis method used",
                "Documents contain relevant financial, technical, market, and risk insights"
            ],
            recommendations=[
                "Review system configuration for agent orchestration",
                "Validate document relevance and content quality", 
                "Consider manual review of key document findings",
                "Expand analysis with additional data sources as needed"
            ],
            sources=sources,
            generated_by="FallbackAnalyzer"
        )

    def validate_agent_responses(self, research_topic: str, agents: List[ChatCompletionAgent]) -> bool:
        """Validate that all agents are properly configured for the research topic"""
        print("🔍 Validating agent configurations...")
        
        required_agents = ["Document_Loader", "Financial_Analyst", "Technical_Analyst", 
                          "Market_Analyst", "Risk_Assessment_Analyst", "Synthesis_Coordinator"]
        
        agent_names = [agent.name for agent in agents]
        
        # Check if all required agents are present
        missing_agents = set(required_agents) - set(agent_names)
        if missing_agents:
            print(f"❌ Missing required agents: {missing_agents}")
            return False
        
        # Check if agents have proper service configuration
        for agent in agents:
            if not hasattr(agent, 'service') or agent.service is None:
                print(f"❌ Agent {agent.name} is missing service configuration")
                return False
        
        print("✅ All agents validated successfully")
        return True

    async def handle_partial_failure(self, research_topic: str, successful_agents: List[str], 
                                   failed_agent: str, error_message: str) -> ResearchReport:
        """Create a report when some agents succeed but others fail"""
        print(f"⚠️ Handling partial failure: {failed_agent} failed")
        
        # Search for relevant documents
        search_results = await self.search_relevant_documents(research_topic)
        sources = list(set([result['filename'] for result in search_results]))
        
        summary = f"""
        PARTIAL RESEARCH REPORT: {research_topic}
        
        EXECUTIVE SUMMARY:
        This analysis encountered a partial failure during the sequential orchestration.
        
        SUCCESSFUL AGENTS: {', '.join(successful_agents)}
        FAILED AGENT: {failed_agent}
        ERROR: {error_message}
        
        The analysis incorporates insights from successful agents but may lack complete
        coverage due to the failure in one specialized area.
        
        RECOMMENDATIONS:
        1. Review the failed agent's configuration and inputs
        2. Consider re-running the analysis with adjusted parameters
        3. Use the successful agent outputs for immediate decision-making
        4. Conduct manual analysis for the failed domain if critical
        """
        
        return ResearchReport(
            report_id=f"partial_{uuid.uuid4().hex[:8]}",
            topic=research_topic,
            summary=summary,
            key_findings=[
                f"Partial analysis completed with {len(successful_agents)} successful agents",
                f"Agent failure: {failed_agent}",
                f"Analyzed {len(sources)} source documents",
                "Report includes insights from available agent analyses"
            ],
            recommendations=[
                f"Investigate and fix the {failed_agent} configuration",
                "Use successful agent outputs for immediate insights",
                "Consider manual analysis for the missing domain",
                "Retry the complete analysis after fixes"
            ],
            sources=sources,
            generated_by="PartialAnalysisHandler"
        )

    def save_report_to_file(self, report: ResearchReport, filename: str = None) -> str:
        """Save research report to a JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"research_report_{report.report_id}_{timestamp}.json"
        
        # Convert report to dictionary
        report_dict = {
            "report_id": report.report_id,
            "topic": report.topic,
            "summary": report.summary,
            "key_findings": report.key_findings,
            "recommendations": report.recommendations,
            "sources": report.sources,
            "generated_by": report.generated_by,
            "generated_at": report.generated_at.isoformat()
        }
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Report saved to: {filename}")
        return filename

    def load_report_from_file(self, filename: str) -> ResearchReport:
        """Load research report from a JSON file"""
        with open(filename, 'r', encoding='utf-8') as f:
            report_dict = json.load(f)
        
        # Convert string back to datetime
        report_dict['generated_at'] = datetime.fromisoformat(report_dict['generated_at'])
        
        return ResearchReport(**report_dict)

    def display_report(self, report: ResearchReport):
        """Display the research report without truncation"""
        print(f"\n🎯 COMPREHENSIVE RESEARCH REPORT")
        print("=" * 70)
        print(f"Report ID: {report.report_id}")
        print(f"Topic: {report.topic}")
        print(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"By: {report.generated_by}")
        
        print(f"\n📋 EXECUTIVE SUMMARY:")
        summary_lines = str(report.summary).split('\n')
        for line in summary_lines:
            if line.strip():
                print(f"  {line.strip()}")
        
        print(f"\n🔍 KEY FINDINGS:")
        for i, finding in enumerate(report.key_findings, 1):
            print(f"  {i}. {finding}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for i, recommendation in enumerate(report.recommendations, 1):
            print(f"  {i}. {recommendation}")
        
        print(f"\n📚 SOURCES USED ({len(report.sources)} documents):")
        for source in report.sources:
            print(f"  - {source}")

async def main():
    """Main demo execution"""
    print("🚀 MULTI-AGENT RAG SYSTEM WITH SEQUENTIAL ORCHESTRATION")
    print("Udacity AI Programming Course - Enhanced with Risk Analysis")
    print("=" * 70)
    
    # Check environment variables
    required_vars = [
        "AZURE_DEPLOYMENT_NAME", 
        "AZURE_DEPLOYMENT_ENDPOINT",
        "AZURE_DEPLOYMENT_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("⚠️  Using mock Azure OpenAI values for demo")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nTo use real Azure OpenAI, please set these environment variables.")
    
    # Initialize the system
    rag_system = SequentialRAGOrchestration()
    
    # Pre-load documents once at the beginning
    print("📚 Pre-loading documents...")
    await rag_system.load_documents()
    print("✅ Documents ready for analysis\n")
    
    # Research topics - now including risk-focused topics
    research_topics = [
        "Company growth strategy and financial performance",
        "Technical architecture and AI platform development", 
        "Market competition and customer analysis",
        "Risk assessment and mitigation strategies"
    ]
    
    # Run analysis for each topic
    all_reports = []
    
    for i, topic in enumerate(research_topics, 1):
        print(f"\n{'='*70}")
        print(f"ANALYSIS {i}/{len(research_topics)}: {topic}")
        print(f"{'='*70}")
        
        try:
            # Validate agents before running analysis
            agents = rag_system.create_sequential_agents()
            if not rag_system.validate_agent_responses(topic, agents):
                print("❌ Agent validation failed, skipping this analysis")
                continue
            
            # Run sequential analysis for this topic
            report = await rag_system.run_sequential_analysis(topic)
            all_reports.append(report)
            
            # Display this report immediately
            rag_system.display_report(report)
            
            # Save report to file
            rag_system.save_report_to_file(report)
            
            if i < len(research_topics):
                print(f"\n⏳ Preparing next analysis...")
                await asyncio.sleep(2)
                
        except Exception as e:
            print(f"❌ Error in analysis {i}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n🎉 SEQUENTIAL ORCHESTRATION DEMO COMPLETED!")
    print(f"📊 Total research topics processed: {len(all_reports)}")
    
    # Display summary of all reports
    if all_reports:
        print(f"\n📈 ANALYSIS SUMMARY:")
        for i, report in enumerate(all_reports, 1):
            print(f"  {i}. {report.topic} - {len(report.sources)} sources")

if __name__ == "__main__":
    asyncio.run(main())