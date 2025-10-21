import asyncio
import os
import logging
from blob_connector import BlobStorageConnector
from chroma_manager import ChromaDBManager
from rag_agents import (
    RAGSystemState, FinancialRetrievalAgent, TechnicalRetrievalAgent, 
    MarketRetrievalAgent, SynthesisAgent, CompetitiveIntelligenceAgent
)
from dotenv import load_dotenv
load_dotenv("../../../.env")
# Setup logging
logging.getLogger('semantic_kernel').setLevel(logging.WARNING)
logging.getLogger('azure').setLevel(logging.WARNING)
logging.getLogger('chromadb').setLevel(logging.WARNING)


class MultiAgentRAGSystem:
    """Main multi-agent RAG system with ChromaDB and Azure Blob Storage"""
    
    def __init__(self):
        # Initialize Azure Blob Storage connector
        self.blob_connector = BlobStorageConnector()
        
        # Initialize ChromaDB vector store
        self.chroma_manager = ChromaDBManager()
        
        # Initialize system state
        self.system_state = RAGSystemState()
        
         # Initialize specialized agents with new competitive agent
        self.retrieval_agents = {
            "financial": FinancialRetrievalAgent(self.system_state, self.blob_connector, self.chroma_manager),
            "technical": TechnicalRetrievalAgent(self.system_state, self.blob_connector, self.chroma_manager),
            "market": MarketRetrievalAgent(self.system_state, self.blob_connector, self.chroma_manager),
            "competitive": CompetitiveIntelligenceAgent(self.system_state, self.blob_connector, self.chroma_manager)
        }
        
        # Initialize synthesis agent
        self.synthesis_agent = SynthesisAgent(self.system_state, self.blob_connector, self.chroma_manager)
        
        # Track if documents are loaded
        self.documents_loaded = False
    
    def load_documents_to_chromadb(self):
        """Load documents from Azure Blob Storage to ChromaDB"""
        if self.documents_loaded:
            print("📚 Documents already loaded to ChromaDB")
            return
        
        print("🔄 Loading documents to ChromaDB vector store...")
        
        # Upload sample documents to Azure Blob Storage if needed
        documents = self.blob_connector.list_documents()
        if not documents:
            print("📁 Uploading sample documents to Azure Blob Storage...")
            self.blob_connector.upload_sample_documents()
            documents = self.blob_connector.list_documents()
        
        # Load documents into ChromaDB
        total_chunks = 0
        for doc_name in documents:
            content = self.blob_connector.get_document_content(doc_name)
            if content:
                chunks_added = self.chroma_manager.add_document(doc_name, content)
                total_chunks += chunks_added
                print(f"  ✅ Loaded {doc_name} ({chunks_added} chunks)")
        
        self.documents_loaded = True
        print(f"🎉 Successfully loaded {len(documents)} documents with {total_chunks} chunks to ChromaDB")
        
        # Show ChromaDB statistics
        stats = self.chroma_manager.get_collection_stats()
        print(f"\n📊 ChromaDB Collection Stats:")
        for collection, info in stats.items():
            print(f"  {collection}: {info.get('document_count', 0)} documents")

    def reset_system_state(self):
        """Reset system state between research topics to avoid accumulation"""
        self.system_state = RAGSystemState()
        
        # Reinitialize all agents with the new system state
        self.retrieval_agents = {
            "financial": FinancialRetrievalAgent(self.system_state, self.blob_connector, self.chroma_manager),
            "technical": TechnicalRetrievalAgent(self.system_state, self.blob_connector, self.chroma_manager),
            "market": MarketRetrievalAgent(self.system_state, self.blob_connector, self.chroma_manager),
            "competitive": CompetitiveIntelligenceAgent(self.system_state, self.blob_connector, self.chroma_manager)
        }
        
        self.synthesis_agent = SynthesisAgent(self.system_state, self.blob_connector, self.chroma_manager)

    async def run_research_analysis(self, research_topic: str):
        """Run complete multi-agent research analysis with semantic search"""
        # Reset state for new research topic
        self.reset_system_state()
        
        print(f"\n🔍 RESEARCH TOPIC: {research_topic}")
        print("=" * 60)
        
        # Ensure documents are loaded
        if not self.documents_loaded:
            self.load_documents_to_chromadb()
            
        # Step 1: Parallel retrieval by all specialized agents using ChromaDB
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
            print(f"  🔗 Sources: {', '.join(result['sources'][:2])}")
            if result['documents_found'] > 2:
                print(f"    ... and {result['documents_found'] - 2} more")
            
            # Show relevance scores
            if result.get('relevance_scores'):
                avg_relevance = sum(result['relevance_scores']) / len(result['relevance_scores'])
                print(f"  📈 Average Relevance: {avg_relevance:.2f}")
            
            total_documents_found += result['documents_found']
        
        # Step 2: Synthesis by coordination agent
        print(f"\n🧠 SYNTHESIZING FINDINGS FROM SEMANTIC SEARCH...")
        print("-" * 50)
        
        final_report = await self.synthesis_agent.generate_comprehensive_report(
            research_topic, agent_results
        )
        
        # Display final report
        self._display_report(final_report)
        
        # Display system metrics
        self._display_system_metrics()
        
        return final_report
    
    def _display_report(self, report):
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
        for source in report.sources:
            # Find relevance score for this source
            relevance = next(
                (doc.relevance_score for doc in self.system_state.retrieved_documents.values() 
                 if doc.source == source), 0.0
            )
            print(f"  - {source} (Relevance: {relevance:.2f})")
    
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
        
        # Show ChromaDB stats
        stats = self.chroma_manager.get_collection_stats()
        print(f"\n🗃️ CHROMADB STATISTICS:")
        for collection, info in stats.items():
            print(f"  {collection}: {info.get('document_count', 0)} documents")

async def main():
    """Main demo execution"""
    print("🚀 MULTI-AGENT RAG SYSTEM WITH CHROMADB & AZURE BLOB STORAGE")
    print("=" * 70)
    
    # Check environment variables
    required_vars = [
        "BLOB_CONNECTION_STRING",
        "AZURE_TEXTGENERATOR_DEPLOYMENT_NAME", 
        "AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT",
        "AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        print("❌ Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease check your .env file")
        return
    
    # Initialize the multi-agent RAG system
    rag_system = MultiAgentRAGSystem()
    
    # Demo research topics
    # TODO: Add new research topics that leverage competitive intelligence
    research_topics = [
        "Company growth strategy and financial performance",
        "Technical architecture and AI platform development", 
        "Market competition and customer analysis",
        "Product roadmap and future initiatives",
        "Competitive landscape and market positioning"
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
                await asyncio.sleep(2)
                
        except Exception as e:
            print(f"❌ Error in analysis {i}: {e}")
            continue
    
    print(f"\n🎉 DEMO COMPLETED!")

if __name__ == "__main__":
    asyncio.run(main())
