import asyncio
import os
import logging
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.contents import ChatMessageContent

from blob_connector import BlobStorageConnector
from chroma_manager import ChromaDBManager
from rag_agents import (
    RAGSystemState, FinancialRetrievalAgent, TechnicalRetrievalAgent, 
    MarketRetrievalAgent, SynthesisAgent, ResearchReport
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Reduce verbosity of some loggers
logging.getLogger('azure').setLevel(logging.WARNING)
logging.getLogger('chromadb').setLevel(logging.WARNING)
logging.getLogger('semantic_kernel').setLevel(logging.WARNING)

class MultiAgentRAGSystem:
    """Main multi-agent RAG system using Semantic Kernel's Chroma store and Agent Framework"""
    
    def __init__(self):
        # Initialize Azure Blob Storage connector
        self.blob_connector = BlobStorageConnector()
        
        # Initialize Chroma vector store using Semantic Kernel's ChromaStore
        self.chroma_store = ChromaDBManager()
        
        # Initialize system state
        self.system_state = RAGSystemState()
        
        # Initialize specialized agents
        self.retrieval_agents = {
            "financial": FinancialRetrievalAgent(self.system_state, self.blob_connector, self.chroma_store),
            "technical": TechnicalRetrievalAgent(self.system_state, self.blob_connector, self.chroma_store),
            "market": MarketRetrievalAgent(self.system_state, self.blob_connector, self.chroma_store)
        }
        
        # Initialize synthesis agent
        self.synthesis_agent = SynthesisAgent(self.system_state, self.blob_connector, self.chroma_store)
        
        # Initialize Semantic Kernel runtime
        self.runtime = InProcessRuntime()
        
        # Track if documents are loaded
        self.documents_loaded = False
    
    async def load_documents_to_chromadb(self):
        """Load documents from Azure Blob Storage to ChromaDB using Semantic Kernel's ChromaStore"""
        if self.documents_loaded:
            print("📚 Documents already loaded to ChromaDB")
            return
        
        print("🔄 Loading documents to Chroma vector store...")
        
        # Upload sample documents to Azure Blob Storage if needed
        documents = self.blob_connector.list_documents()
        if not documents:
            print("📁 Uploading sample documents to Azure Blob Storage...")
            self.blob_connector.upload_sample_documents()
            documents = self.blob_connector.list_documents()
        
        # Load documents into ChromaDB using the new vector store
        total_chunks = 0
        for doc_name in documents:
            content = self.blob_connector.get_document_content(doc_name)
            if content:
                # Determine the appropriate collection
                collection_type = self.chroma_store.determine_collection(doc_name, content)
                
                # Store document in Chroma
                chunks_added = await self.chroma_store.chunk_and_store_document(
                    doc_name, content, collection_type
                )
                total_chunks += chunks_added
                print(f"  ✅ Loaded {doc_name} to {collection_type} collection ({chunks_added} chunks)")
        
        self.documents_loaded = True
        print(f"🎉 Successfully loaded {len(documents)} documents with {total_chunks} chunks to ChromaDB")
        
        # Show ChromaDB statistics
        stats = await self.chroma_store.get_collection_stats()
        print(f"\n📊 ChromaDB Collection Stats:")
        for collection, info in stats.items():
            print(f"  {collection}: {info.get('document_count', 0)} documents")

    def reset_system_state(self):
        """Reset system state between research topics to avoid accumulation"""
        self.system_state = RAGSystemState()
        
        # Reinitialize all agents with the new system state
        self.retrieval_agents = {
            "financial": FinancialRetrievalAgent(self.system_state, self.blob_connector, self.chroma_store),
            "technical": TechnicalRetrievalAgent(self.system_state, self.blob_connector, self.chroma_store),
            "market": MarketRetrievalAgent(self.system_state, self.blob_connector, self.chroma_store)
        }
        
        self.synthesis_agent = SynthesisAgent(self.system_state, self.blob_connector, self.chroma_store)

    async def run_research_analysis(self, research_topic: str):
        """Run complete multi-agent research analysis using Semantic Kernel Agent Framework"""
        # Reset state for new research topic
        self.reset_system_state()
        
        print(f"\n🔍 RESEARCH TOPIC: {research_topic}")
        print("=" * 60)
        
        # Ensure documents are loaded
        if not self.documents_loaded:
            await self.load_documents_to_chromadb()
            
        # Step 1: Parallel retrieval by all specialized agents using Chroma semantic search
        print(f"\n🤖 Deploying {len(self.retrieval_agents)} specialized agents with semantic search...")
        
        agent_tasks = []
        for agent_name, agent in self.retrieval_agents.items():
            task = agent.retrieve_and_analyze(research_topic)
            agent_tasks.append(task)
        
        # Wait for all agents to complete retrieval and analysis
        agent_results = await asyncio.gather(*agent_tasks)
        
        # Display agent results
        print(f"\n📊 SEMANTIC SEARCH RESULTS:")
        print("-" * 50)
        total_documents_found = 0
        for result in agent_results:
            print(f"\n{result['agent']}:")
            print(f"  📄 Documents Found: {result['documents_found']}")
            print(f"  🔍 Retrieval Method: {result.get('retrieval_method', 'N/A')}")
            if result['sources']:
                print(f"  🔗 Sources: {', '.join(result['sources'][:2])}")
                if result['documents_found'] > 2:
                    print(f"    ... and {result['documents_found'] - 2} more")
            
            total_documents_found += result['documents_found']
        
        # Step 2: Synthesis by coordination agent
        print(f"\n🧠 SYNTHESIZING FINDINGS FROM {len(agent_results)} SPECIALIZED AGENTS...")
        print("-" * 50)
        
        final_report = await self.synthesis_agent.generate_comprehensive_report(
            research_topic, agent_results
        )
        
        # Display final report
        self._display_report(final_report)
        
        # Display system metrics
        self._display_system_metrics()
        
        return final_report
    
    def _display_report(self, report: ResearchReport):
        """Display the final research report"""
        print(f"\n🎯 COMPREHENSIVE RESEARCH REPORT")
        print("=" * 50)
        print(f"Report ID: {report.report_id}")
        print(f"Topic: {report.topic}")
        print(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"By: {report.generated_by}")
        
        print(f"\n📋 EXECUTIVE SUMMARY:")
        print(report.summary)
        
        print(f"\n🔍 KEY FINDINGS:")
        for i, finding in enumerate(report.key_findings, 1):
            print(f"  {i}. {finding}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for i, recommendation in enumerate(report.recommendations, 1):
            print(f"  {i}. {recommendation}")
        
        print(f"\n📚 SOURCES USED ({len(report.sources)} documents):")
        for source in report.sources[:5]:  # Show first 5 sources
            print(f"  - {source}")
        if len(report.sources) > 5:
            print(f"    ... and {len(report.sources) - 5} more")
    
    def _display_system_metrics(self):
        """Display system performance metrics"""
        print(f"\n📈 SYSTEM METRICS:")
        print("-" * 30)
        print(f"Total Documents Retrieved: {len(self.system_state.retrieved_documents)}")
        print(f"Active Reports: {len(self.system_state.active_reports)}")
        
        # Calculate average relevance
        if self.system_state.retrieved_documents:
            avg_relevance = sum(doc.relevance_score for doc in self.system_state.retrieved_documents.values()) / len(self.system_state.retrieved_documents)
            print(f"Average Relevance Score: {avg_relevance:.2f}")
        
        print(f"\nAgent Retrieval Performance:")
        for agent_name, count in self.system_state.retrieval_metrics.items():
            print(f"  {agent_name}: {count} documents")

async def main():
    """Main demo execution using Semantic Kernel Agent Framework"""
    print("🚀 MULTI-AGENT RAG SYSTEM WITH SEMANTIC KERNEL AGENT FRAMEWORK")
    print("=" * 70)
    
    # Check environment variables with fallbacks for demo
    required_vars = [
        "AZURE_TEXTGENERATOR_DEPLOYMENT_NAME", 
        "AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT",
        "AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        print("⚠️  Missing environment variables. Using mock values for demo.")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nTo use real Azure OpenAI, please set these environment variables.")
    
    # Initialize the multi-agent RAG system
    rag_system = MultiAgentRAGSystem()
    
    # Demo research topics
    research_topics = [
        "Company growth strategy and financial performance",
        "Technical architecture and AI platform development",
        "Market competition and customer analysis"
    ]
    
    # Run analysis for each topic
    for i, topic in enumerate(research_topics, 1):
        print(f"\n{'='*70}")
        print(f"ANALYSIS {i}/{len(research_topics)}")
        print(f"{'='*70}")
        
        try:
            await rag_system.run_research_analysis(topic)
            
            # Small delay between analyses
            if i < len(research_topics):
                print(f"\n⏳ Preparing next analysis...")
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"❌ Error in analysis {i}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print(f"\n🎉 DEMO COMPLETED!")

if __name__ == "__main__":
    asyncio.run(main())