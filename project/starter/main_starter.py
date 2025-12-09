import asyncio
import os
import uuid
import logging
import pyodbc
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent, SequentialOrchestration
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.contents import ChatMessageContent
from rag_utils import extract_banking_policies, create_semantic_kernel_context        
from blob_connector import BlobStorageConnector
from chroma_manager import ChromaDBManager
from shared_state import SharedState
from dotenv import load_dotenv

load_dotenv()

# Global logger instance
logger = logging.getLogger(__name__)
# Global logger instance
logger = logging.getLogger(__name__)

def setup_logging():
    """Setup logging with unique file for each run - fixed encoding"""
    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # Create unique log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/banking_analysis_{timestamp}.log"
    
    # Configure logging - file only with UTF-8 encoding
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, mode='w', encoding='utf-8'),  # Fixed encoding
        ]
    )
    
    print(f"Logger started. Log file: {log_filename}")
    return log_filename

# ==============================
# AGENT ACTIVATION TRACKING SYSTEM
# ==============================

class AgentActivationTracker:
    """Tracks which agents are activated during processing"""
    
    def __init__(self):
        self.activated_agents = []
        self.agent_outputs = {}
        self.processing_start_time = None
        self.agent_performance = {}
        
    def reset(self):
        self.activated_agents = []
        self.agent_outputs = {}
        self.processing_start_time = None
        self.agent_performance = {}
        
    def record_agent_activation(self, agent_name: str, output: str = None, processing_time: float = None):
        """Record when an agent is activated"""
        if agent_name not in self.activated_agents:
            self.activated_agents.append(agent_name)
        
        if output:
            self.agent_outputs[agent_name] = output
            
        if processing_time:
            self.agent_performance[agent_name] = {
                'processing_time': processing_time,
                'timestamp': datetime.now().isoformat()
            }

class TestResult:
    """Represents the result of a single test case"""
    
    def __init__(self, query: str, customer_id: str, expected_agents: List[str], 
                 activated_agents: List[str], response: str, processing_time: float,
                 agent_outputs: Dict[str, str]):
        self.query = query
        self.customer_id = customer_id
        self.expected_agents = expected_agents
        self.activated_agents = activated_agents
        self.response = response
        self.processing_time = processing_time
        self.agent_outputs = agent_outputs
        
        # Calculate metrics
        self.all_expected_activated = all(agent in activated_agents for agent in expected_agents)
        self.missing_agents = [agent for agent in expected_agents if agent not in activated_agents]
        self.unexpected_agents = [agent for agent in activated_agents if agent not in expected_agents]
        
        # Response quality assessment
        self.response_quality = self._assess_response_quality()
        
        self.passed = self.all_expected_activated and self.response_quality["overall_score"] >= 0.7

    def _assess_response_quality(self):
        """Assess the quality of the response"""
        response_text = str(self.response).lower()
        
        quality_metrics = {
            "length_adequate": len(response_text) > 100,
            "contains_recommendations": any(keyword in response_text 
                                          for keyword in ['recommend', 'suggest', 'advise', 'should']),
            "contains_analysis": any(keyword in response_text 
                                   for keyword in ['analysis', 'assessment', 'evaluation', 'review']),
            "structured_output": any(keyword in response_text 
                                   for keyword in ['summary', 'conclusion', 'findings', 'next steps']),
            "customer_focused": any(keyword in response_text 
                                  for keyword in ['customer', 'you', 'your', 'we recommend']),
        }
        
        score = sum(quality_metrics.values()) / len(quality_metrics)
        
        return {
            "overall_score": score,
            "metrics": quality_metrics
        }

class DataConnector:
    """
    TODO: Implement Azure SQL Database connectivity
    HINT: Use pyodbc to connect to Azure SQL and fetch customer transaction data
    """
    def __init__(self, connection_string: Optional[str] = None):
        # TODO: Initialize connection string from environment variables
        # HINT: Use os.getenv("AZURE_SQL_CONNECTION_STRING")
        self.connection_string = None
        raise NotImplementedError("DataConnector initialization not implemented")
    
    def _test_connection(self):
        """TODO: Test database connection on initialization"""
        # HINT: Use pyodbc.connect() and execute a simple query like "SELECT 1"
        raise NotImplementedError("Connection testing not implemented")
    
    async def fetch_income(self, customer_id: str) -> Optional[float]:
        """TODO: Fetch customer income from Azure SQL database"""
        # HINT: Query the transactions table and aggregate income data
        # HINT: Use asyncio.sleep(0) to make it async compatible
        raise NotImplementedError("Income fetching not implemented")
    
    async def fetch_transactions(self, customer_id: str) -> List[Dict]:
        """TODO: Fetch customer transactions from Azure SQL database"""
        # HINT: Query transactions table for the specific customer
        # HINT: Convert SQL results to dictionary format
        raise NotImplementedError("Transaction fetching not implemented")
    
    @contextmanager
    def get_db_connection(self):
        """TODO: Create database connection context manager"""
        # HINT: Use pyodbc.connect() and yield the connection
        # HINT: Add proper error handling and connection cleanup
        raise NotImplementedError("Database connection not implemented")

# Enhanced Pydantic Models - TODO: Add proper validation and additional fields
class EnhancedBankingReport(KernelBaseModel):
    """
    TODO: Enhance this model with comprehensive banking analytics:
    report_id: str
    customer_id: str
    query: str
    summary: str
    key_findings:  []
    risk_assessment: str = "medium"
    risk_score: float = 0.5
    recommendations: []
    actions_taken:  []
    policy_references: []
    agent_contributions:  {}
    processing_metrics:  {}
    generated_by: str = "EnhancedBankingOrchestration"
    generated_at: datetime = datetime.now()
    """
    

class CustomerProfile(KernelBaseModel):
    """
    TODO: Enhance this model with comprehensive customer profiling :
    customer_id: str
    income: float = 0.0
    credit_score: int = 0
    account_type: str = "standard"
    customer_since: str = ""
    risk_tier: str = "medium"
    recent_transactions:   []
    banking_products:  []
    last_review_date: str 
    """
    

class EnhancedBankingSequentialOrchestration:
    """Enhanced banking system with advanced features"""
    
    def __init__(self, enable_tracking: bool = True):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing EnhancedBankingSequentialOrchestration")
        # Initialize agent activation tracking
        self.enable_tracking = enable_tracking
        self.tracker = AgentActivationTracker() if enable_tracking else None
        
        # Initialize enhanced storage components
        self.blob_connector = BlobStorageConnector()
        self.chroma_store = ChromaDBManager()
        self.shared_state = SharedState()
        
        # TODO: Initialize Azure SQL Data Connector
        # HINT: Use the DataConnector class you implemented above
        self.data_connector = None
        raise NotImplementedError("DataConnector initialization not implemented")
        
        # Initialize enhanced kernel
        self.kernel = Kernel()
        
        # TODO: Configure Azure AI Foundry service properly
        # HINT: Use AzureChatCompletion with proper service_id and parameters
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="enhanced_banking_chat",
                # TODO: Add proper deployment configuration
                # HINT: Use environment variables for deployment details
                deployment_name=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
            )
        )
        
        # Load enhanced banking policies
        self.banking_policies = self._load_enhanced_policies()
        self.customer_profiles = {}
        
        # Performance tracking
        self.performance_metrics = {
            "total_requests": 0,
            "successful_analyses": 0,
            "average_processing_time": 0,
            "agent_performance": {}
        }

    def _load_enhanced_policies(self) -> Dict[str, Any]:
        """TODO: Enhance policy loading with better error handling and metadata"""
        # HINT: Add more comprehensive error handling
        # HINT: Enhance metadata extraction from documents
        try:
            if not self.blob_connector.list_documents():
                self.blob_connector.upload_sample_documents()
            
            enhanced_docs = []
            for doc_name in self.blob_connector.list_documents():
                content = self.blob_connector.get_document_content(doc_name)
                metadata = self.blob_connector.get_document_metadata(doc_name)
                
                # TODO: Enhance metadata with document analysis
                # HINT: Extract key topics, compliance levels, update frequency
                enhanced_docs.append({
                    "filename": doc_name,
                    "id": f"{metadata.get('type', 'general')}_{doc_name}",
                    "meta": {
                        **metadata,
                        "priority": "high" if metadata.get('type') in ['fraud', 'risk'] else "medium",
                        "review_frequency": "quarterly" if metadata.get('type') in ['fraud', 'compliance'] else "annually"
                    },
                    "text": content
                })
            
            policies = extract_banking_policies(enhanced_docs)
            return policies
        except Exception as e:
            self.logger.error(f"Could not load enhanced banking policies: {e}")
            return {}

    async def _load_customer_profiles(self) -> Dict[str, CustomerProfile]:
        """TODO: Implement comprehensive customer profile loading from Azure SQL"""
        # HINT: Use DataConnector to fetch real customer's transactions data
        # HINT: Enhance with fallback to sample data when SQL is unavailable
        
        # TODO: Replace this with actual Azure SQL data loading <OPTIONAL>
        # HINT: Use self.data_connector.fetch_income() and self.data_connector.fetch_transactions()
        # Default profiles
        default_profiles = {
            "12345": CustomerProfile(
                customer_id="12345",
                income=75000.0,
                credit_score=780,
                account_type="premium_plus",
                customer_since="2019-05-15",
                risk_tier="low",
                banking_products=["checking", "savings", "mortgage", "investment", "credit_card"],
                last_review_date="2024-01-10"
            ),
            "67890": CustomerProfile(
                customer_id="67890",
                income=45000.0,
                credit_score=680,
                account_type="standard",
                customer_since="2022-08-22",
                risk_tier="medium",
                banking_products=["checking", "savings", "student_loan"],
                last_review_date="2024-02-15"
            ),
            "11111": CustomerProfile(
                customer_id="11111",
                income=28000.0,
                credit_score=620,
                account_type="basic",
                customer_since="2023-11-05",
                risk_tier="high",
                banking_products=["checking", "debit_card"],
                last_review_date="2024-03-01"
            )
        }

        # TODO: Implement real data loading from Azure SQL
        # HINT: Iterate through customer IDs and fetch their data
        # HINT: Handle exceptions and fall back to sample data
        
        raise NotImplementedError("Customer profile loading not implemented")

    def create_enhanced_agents(self) -> List[ChatCompletionAgent]:
        """
        TODO: Implement specialized banking agents with Azure AI Foundry reasoning
        
        HINT: Each agent should have:
        - Clear, specialized instructions for banking domain
        - Proper service configuration using self.kernel.get_service()
        - Banking-specific expertise and response formats
        """
        
        # TODO: Enhanced Data Gathering Agent
        # HINT: Focus on customer data analysis and policy relevance
        data_agent = ChatCompletionAgent(
            name="Enhanced_Data_Gatherer",
            instructions="""
            TODO: Write comprehensive instructions for data gathering agent
            HINT: Include banking-specific data analysis, policy matching, and data quality assessment
            """,
            service=self.kernel.get_service("enhanced_banking_chat")
        )
        
        # TODO: Enhanced Fraud Detection Agent  
        # HINT: Focus on transaction patterns, anomaly detection, and risk scoring
        fraud_agent = ChatCompletionAgent(
            name="Enhanced_Fraud_Analyst",
            instructions="""
            TODO: Write comprehensive instructions for fraud detection agent
            HINT: Include fraud patterns, risk assessment, and mitigation strategies
            """,
            service=self.kernel.get_service("enhanced_banking_chat")
        )
        
        # TODO: Enhanced Loan Evaluation Agent
        # HINT: Focus on credit risk, eligibility criteria, and product recommendations
        loan_agent = ChatCompletionAgent(
            name="Enhanced_Loan_Analyst",
            instructions="""
            TODO: Write comprehensive instructions for loan evaluation agent
            HINT: Include credit assessment, debt analysis, and product suitability
            """,
            service=self.kernel.get_service("enhanced_banking_chat")
        )
        
        # TODO: Enhanced Customer Support Agent
        # HINT: Focus on customer experience, service gaps, and retention strategies
        support_agent = ChatCompletionAgent(
            name="Enhanced_Support_Specialist",
            instructions="""
            TODO: Write comprehensive instructions for customer support agent
            HINT: Include service optimization, customer journey mapping, and issue resolution
            """,
            service=self.kernel.get_service("enhanced_banking_chat")
        )
        
        # TODO: Enhanced Risk Assessment Agent
        # HINT: Focus on enterprise risk, compliance, and regulatory requirements
        risk_agent = ChatCompletionAgent(
            name="Enhanced_Risk_Analyst",
            instructions="""
            TODO: Write comprehensive instructions for risk assessment agent
            HINT: Include risk categorization, compliance checking, and mitigation planning
            """,
            service=self.kernel.get_service("enhanced_banking_chat")
        )
        
        # TODO: Enhanced Synthesis Coordinator Agent
        # HINT: Focus on integrating all analyses and creating executive reports
        synthesis_agent = ChatCompletionAgent(
            name="Enhanced_Synthesis_Coordinator",
            instructions="""
            TODO: Write comprehensive instructions for synthesis coordinator agent
            HINT: Include analysis integration, strategic recommendations, and executive reporting
            """,
            service=self.kernel.get_service("enhanced_banking_chat")
        )
        
        agents = [data_agent, fraud_agent, loan_agent, support_agent, risk_agent, synthesis_agent]
        return agents

    async def run_enhanced_analysis(self, customer_id: str, customer_query: str) -> EnhancedBankingReport:
        """TODO: Implement the main banking analysis workflow"""
        self.logger.info(f"Starting enhanced banking analysis for customer {customer_id}")
        self.logger.info(f"Customer query: {customer_query}")
        
        print(f"\nENHANCED BANKING ANALYSIS INITIATED")
        print(f"Customer: {customer_id}")
        print(f"Query: {customer_query}")
        print("=" * 70)
        
        start_time = datetime.now()
        self.performance_metrics["total_requests"] += 1
        
        # Reset tracker for new analysis
        if self.tracker:
            self.tracker.reset()
            self.tracker.processing_start_time = start_time
        
        # TODO: Ensure customer profiles are loaded with real data
        if not self.customer_profiles:
            self.customer_profiles = await self._load_customer_profiles()
        
        # TODO: Load enhanced documents to ChromaDB 
        await self.load_enhanced_documents()
        
        # Get customer data and perform semantic search
        customer_profile = self.customer_profiles.get(customer_id, CustomerProfile(customer_id=customer_id))
        search_results = await self.chroma_store.hybrid_search(customer_query, [
            "fraud_detection", "loan_policies", "customer_support", 
            "risk_assessment", "transaction_monitoring", "compliance"
        ], top_k=4)
        
        # TODO: Prepare enhanced context for orchestration
        banking_context = self._prepare_enhanced_context(customer_profile, search_results, customer_query)
        
        # Create enhanced agents
        agents = self.create_enhanced_agents()
        agent_contributions = {}
        
        def enhanced_agent_callback(message: ChatMessageContent) -> None:
            """TODO: Enhance callback with proper agent output tracking"""
            # Basic emoji/special character removal for logging
            import re
            safe_content = re.sub(r'[^\w\s.,!?;:()\-]', '', safe_content)
            
            agent_contributions[message.name] = message.content
            print(f"\n# {message.name}")
            print(f"{message.content}\n")
            # Record agent activation
            if self.tracker:
                self.tracker.record_agent_activation(message.name, message.content)
            
        # Create SequentialOrchestration
        sequential_orchestration = SequentialOrchestration(
            members=agents,
            agent_response_callback=enhanced_agent_callback,
        )
        
        # Set up runtime
        runtime = InProcessRuntime()
        
        try:
            runtime.start()
            
            # TODO: Prepare enhanced orchestration task with banking context
            orchestration_task = f"""
            ENHANCED BANKING CUSTOMER ANALYSIS REQUEST
            
            {banking_context}
            
            TODO: Create comprehensive orchestration instructions
            HINT: Guide each agent through their specialized analysis sequence
            """
            
            # Invoke the orchestration
            orchestration_result = await sequential_orchestration.invoke(
                task=orchestration_task,
                runtime=runtime
            )
            
            # Get the final result
            final_output = await asyncio.wait_for(orchestration_result.get(), timeout=180.0)
            processing_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Enhanced banking orchestration completed in {processing_time:.2f} seconds")
            print(f"Enhanced banking orchestration completed in {processing_time:.2f} seconds")
            
            # TODO: Calculate enhanced risk score with multiple factors
            risk_score = self._calculate_enhanced_risk_score(customer_profile, search_results)
            risk_assessment = self._determine_risk_tier(risk_score)
            #TODO: Update shared state with enhanced data
            self.shared_state.update_interaction(customer_id, {})
            # Update performance metrics
            self.performance_metrics["successful_analyses"] += 1
            self.performance_metrics["average_processing_time"] = (
                self.performance_metrics["average_processing_time"] * 
                (self.performance_metrics["successful_analyses"] - 1) + processing_time
            ) / self.performance_metrics["successful_analyses"]
            
            # TODO: Create comprehensive banking report
            report = EnhancedBankingReport(
                report_id=f"enhanced_{uuid.uuid4().hex[:8]}",
                customer_id=customer_id,
                query=customer_query,
                summary=str(final_output),
                key_findings=self._generate_enhanced_findings(customer_profile, search_results, agent_contributions),
                risk_assessment=risk_assessment,
                risk_score=risk_score,
                recommendations=self._generate_enhanced_recommendations(customer_profile, risk_score),
                actions_taken=[
                    "Enhanced multi-agent sequential analysis completed",
                    "Comprehensive policy compliance verification performed",
                    "Enterprise risk assessment conducted"
                ],
                policy_references=[],  # TODO: Extract from search results
                agent_contributions=agent_contributions,
                processing_metrics={
                    "total_processing_time": 0,  # TODO: Calculate actual time
                    "agents_used": len(agents),
                    "policies_referenced": 0,  # TODO: Count actual policies
                    "risk_score": risk_score,
                },
                generated_by="EnhancedBankingSequentialOrchestration"
            )
            
            return report
            
        except asyncio.TimeoutError:
            self.logger.error("Enhanced orchestration timed out")
            #TODO: Create enhanced timeout report
            return await self._create_enhanced_timeout_report(customer_id, customer_query, customer_profile, search_results)
        except Exception as e:
            self.logger.error(f"Error in enhanced orchestration: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            #TODO: Create enhanced fallback report
            return await self._create_enhanced_fallback_report(customer_id, customer_query, customer_profile, search_results)
        finally:
            await runtime.stop_when_idle()

    def _calculate_enhanced_risk_score(self, customer_profile: CustomerProfile, search_results: List[Dict]) -> float:
        """TODO: Implement comprehensive risk scoring algorithm"""
        # HINT: Consider multiple factors:
        # - Income stability and level
        # - Credit score and history
        # - Transaction patterns
        # - Customer tenure
        # - Product usage
        # - Policy compliance
        
        base_score = 0.5
        
        # TODO: Add income-based risk factors
        # Income factor
        if customer_profile.income < 30000:
            base_score += 0.3
        # TODO: Add credit score-based factors  
        # TODO: Add transaction pattern analysis
        # TODO: Add customer tenure considerations
        # TODO: Add product usage analysis
        
        return max(0.0, min(1.0, base_score))
    
    # Determine risk tier based on score 
    # Use it in _calculate_enhanced_risk_score
    def _determine_risk_tier(self, risk_score: float) -> str:
        """Determine risk tier from enhanced risk score"""
        if risk_score >= 0.7:
            return "high"
        elif risk_score >= 0.4:
            return "medium"
        else:
            return "low"

    def _generate_enhanced_findings(self, customer_profile: CustomerProfile, search_results: List[Dict], agent_contributions: Dict) -> List[str]:
        """TODO: Generate comprehensive findings based on analysis"""
        findings = [
            f"Enhanced analysis completed for customer {customer_profile.customer_id}",
            # TODO: Add specific findings based on customer profile and agent outputs
            #Customer risk profile
            #Financial standing
            #Banking relationship
            #Policy compliance
            #Analysis depth
        ]
        
        # TODO: Add findings based on income analysis
        # TODO: Add findings based on credit assessment
        # TODO: Add findings based on transaction patterns
        # TODO: Add findings based on risk assessment
        
        return findings

    def _generate_enhanced_recommendations(self, customer_profile: CustomerProfile, risk_score: float) -> List[str]:
        """TODO: Generate strategic recommendations based on comprehensive analysis"""
        self.logger.info("Generating enhanced recommendations")
        recommendations = [
            "Implement enhanced monitoring based on risk assessment",
            "Review and optimize customer banking product portfolio",
            "Schedule follow-up based on risk tier and customer needs",
            "Update customer risk profile in central system",
            "Consider proactive outreach for relationship enhancement"
        ]
        if risk_score > 0.7:
            recommendations.extend([])
        # TODO: Add recommendations based on risk tier
        # TODO: Add product suitability recommendations
        # TODO: Add customer relationship enhancement suggestions
        # You can add Product-based recommendations
        #if "investment" not in customer_profile.banking_products
    
        return recommendations
        
    # TODO: Create enhanced timeout report
    async def _create_enhanced_timeout_report(self, customer_id: str, query: str, customer_profile: CustomerProfile, search_results: List[Dict]) -> EnhancedBankingReport:
        """Create enhanced timeout report when the main analysis process times out"""
        
        # Step 1: Log the timeout event
        self.logger.warning(f"Creating timeout report for customer {customer_id}")
        print("Enhanced orchestration timed out - creating comprehensive timeout report...")
        
        # Step 2: Extract unique policy references from search results
        # HINT: Use list comprehension to extract 'filename' from each result's metadata
        # HINT: Use .get() with default value 'Unknown' to handle missing data
        policy_references = None # YOUR CODE HERE

        # Step 3: Calculate risk metrics
        # HINT: Call the helper methods that are already implemented
        risk_score = None # YOUR CODE HERE
        risk_assessment = None # YOUR CODE HERE
        
        # Step 4: Create the summary string
        # HINT: Use f-string formatting to insert variables
        # HINT: customer_profile.risk_tier and customer_profile.income are available
        summary = f"""
        ENHANCED BANKING ANALYSIS REPORT: {query}
        
        EXECUTIVE SUMMARY:
        Enhanced analysis initiated for customer {customer_id} but the sequential orchestration process timed out.
        Comprehensive customer profile and policy analysis were completed before the timeout.
        
        STATUS: Enhanced analysis incomplete due to timeout
        CUSTOMER PROFILE: {customer_profile.risk_tier.upper()} risk, ${customer_profile.income:,.2f} income
        POLICY REFERENCES: {len(policy_references)} relevant documents identified
        RISK ASSESSMENT: {risk_assessment.upper()} (Score: {risk_score:.3f})
        
        PARTIAL FINDINGS:
        • Customer data gathering and policy identification completed successfully
        • Initial risk assessment calculated: {risk_score:.3f}
        • {len(policy_references)} policy documents matched for comprehensive analysis
        • Enhanced multi-agent framework initialized but not completed
        
        RECOMMENDATIONS:
        1. Review completed customer profile and policy analysis manually
        2. Consider system optimization for complex multi-agent workflows
        3. Validate risk assessment findings with alternative methods
        4. Retry analysis with adjusted parameters if needed
        """
        
        # Step 5: Create and return the EnhancedBankingReport object
        # HINT: Fill in all the required fields for the data class
        # HINT: For key_findings and recommendations, use lists of strings
        return EnhancedBankingReport(
            report_id=f"enhanced_timeout_{uuid.uuid4().hex[:8]}",
            customer_id=customer_id,
            query=query,
            summary=summary,
            key_findings=[
                "Enhanced orchestration timed out during multi-agent processing",
                f"Customer risk assessment: {risk_assessment.upper()} (Score: {risk_score:.3f})",
                f"Policy analysis completed: {len(policy_references)} documents referenced",
                "Partial analysis available for manual review",
                "Enhanced data gathering and initial assessment completed successfully"
            ],
            risk_assessment=risk_assessment,
            risk_score=risk_score,
            recommendations=[
                "Review system configuration for complex multi-agent workflows",
                "Validate partial findings through manual analysis",
                "Consider staged analysis approach for complex queries",
                "Monitor system performance and resource allocation"
            ],
            actions_taken=["Enhanced data gathering completed", "Policy identification performed", "Initial risk assessment calculated"],
            policy_references=policy_references,
            agent_contributions={"Timeout": "Enhanced analysis incomplete due to timeout"},
            processing_metrics={"analysis_completeness": "partial", "timeout_occurred": True},
            generated_by="EnhancedTimeoutHandler"
        )

    #TODO: Create enhanced fallback report
    async def _create_enhanced_fallback_report(self, customer_id: str, query: str, customer_profile: CustomerProfile, search_results: List[Dict]) -> EnhancedBankingReport:
        """Create enhanced fallback report when primary analysis fails"""
        
        # Step 1: Log that we're using the fallback method
        self.logger.warning(f"Creating fallback report for customer {customer_id}")
        print("Using enhanced fallback banking analysis method...")
        
        # Step 2: Extract unique policy references from search results
        # HINT: Each search_result is a dict. Extract the 'filename' from 'metadata'
        # HINT: Use list comprehension with .get() and default value 'Unknown'
        # HINT: Use set() to remove duplicates, then convert back to list
        policy_references = None# TODO: Implement this line
        
        # Step 3: Calculate risk metrics using helper methods
        # HINT: Call the existing methods in this class
        risk_score = None# TODO: Calculate enhanced risk score
        risk_assessment = None# TODO: Determine risk tier from score
        
        # Step 4: Create the comprehensive summary string
        # HINT: This is a multi-line f-string - insert variables where indicated
        # HINT: Use string formatting for numbers: :,.2f for currency, :.3f for risk score
        # HINT: Access customer_profile attributes: income, credit_score, banking_products, customer_since
        summary = f"""
        COMPREHENSIVE ENHANCED BANKING ANALYSIS: {query}
        
        EXECUTIVE SUMMARY:
        This enhanced analysis examines banking request for customer {customer_id} using 
        comprehensive customer profiling and advanced policy matching. The analysis leverages
        {len(policy_references)} relevant policy documents and complete customer financial data.
        
        CUSTOMER PROFILE ANALYSIS:
        - Income: ${customer_profile.income:,.2f}
        - Credit Score: {customer_profile.credit_score}
        - Risk Tier: {risk_assessment.upper()} (Score: {risk_score:.3f})
        - Banking Products: {len(customer_profile.banking_products)} active products
        - Customer Tenure: Since {customer_profile.customer_since}
        
        ENHANCED METHODOLOGY:
        • Multi-dimensional customer profiling
        • Advanced policy matching and relevance scoring
        • Comprehensive risk assessment with weighted factors
        • Strategic recommendation development
        • Enhanced fallback analysis protocols
        
        STRATEGIC INSIGHTS:
        • Customer represents {risk_assessment} risk profile with {risk_score:.3f} risk score
        • {len(policy_references)} policy documents provide comprehensive guidance
        • Enhanced analysis framework ensures thorough assessment
        • Strategic recommendations based on complete profile analysis
        
        NOTE: This report was generated using enhanced fallback analysis methods.
        """
        
        # Step 5: Create and return the EnhancedBankingReport object
        # HINT: Fill in all parameters for the EnhancedBankingReport constructor
        # HINT: Use helper methods for key_findings and recommendations
        # HINT: Some fields have fixed values as shown below
        return EnhancedBankingReport(
            report_id=None# TODO: Generate unique ID starting with "enhanced_fallback_"
            ,customer_id=None# TODO: Use provided customer_id
            ,query=None# TODO: Use provided query
            ,summary=None# TODO: Use the summary string created above
            ,key_findings=None# TODO: Call _generate_enhanced_findings() helper method
            ,risk_assessment=None# TODO: Use calculated risk_assessment
            ,risk_score=None# TODO: Use calculated risk_score
            ,recommendations=None# TODO: Call _generate_enhanced_recommendations() helper method
            ,actions_taken=[
                "Enhanced customer profile analysis completed",
                "Comprehensive policy matching and relevance assessment",
                "Multi-factor risk assessment executed",
                "Strategic recommendation development performed",
                "Enhanced fallback analysis framework utilized"
            ],
            policy_references=None# TODO: Use the policy_references list created above
            ,agent_contributions={"FallbackAnalyzer": "Comprehensive enhanced fallback analysis performed"},
            processing_metrics={"analysis_completeness": "comprehensive", "fallback_used": True},
            generated_by="EnhancedFallbackBankingAnalyzer"
        )
    

    def _prepare_enhanced_context(self, customer_profile: CustomerProfile, search_results: List[Dict], customer_query: str) -> str:
        """TODO: Prepare comprehensive context for banking orchestration"""
        # HINT: Include customer profile, relevant policies, and query context
        
        customer_context = f"""
        CUSTOMER PROFILE:
        - Customer ID: {customer_profile.customer_id}
        - Income: ${customer_profile.income:,.2f}
        - Credit Score: {customer_profile.credit_score}
        - TODO: Add more customer profile details
        """
        
        # TODO: Add policy context from search results
        # TODO: Add banking policy framework context
        # TODO: Add query-specific context
        
        return f"""
        BANKING ANALYSIS REQUEST: {customer_query}
        {customer_context}
        TODO: Add comprehensive policy and analysis context
        """
    
    async def run_test_analysis(self, customer_id: str, customer_query: str, expected_agents: List[str]) -> TestResult:
        """Run analysis specifically for testing with agent activation tracking"""
        print(f"\n🧪 TEST ANALYSIS: {customer_query}")
        
        # Run the enhanced analysis
        report = await self.run_enhanced_analysis(customer_id, customer_query)
        
        # Get activation data from tracker
        activated_agents = self.tracker.activated_agents if self.tracker else []
        agent_outputs = self.tracker.agent_outputs if self.tracker else {}
        processing_time = self.tracker.agent_performance.get('total_processing_time', 0) if self.tracker else 0
        
        # Create test result
        test_result = TestResult(
            query=customer_query,
            customer_id=customer_id,
            expected_agents=expected_agents,
            activated_agents=activated_agents,
            response=report.summary,
            processing_time=processing_time,
            agent_outputs=agent_outputs
        )
        
        return test_result
    
    def display_enhanced_report(self, report: EnhancedBankingReport):
        """Display the enhanced banking report"""
        self.logger.info(f"Displaying enhanced report: {report.report_id}")
        print(f"\nENHANCED COMPREHENSIVE BANKING ANALYSIS REPORT")
        print("=" * 80)
        print(f"Report ID: {report.report_id}")
        print(f"Customer: {report.customer_id}")
        print(f"Query: {report.query}")
        print(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"By: {report.generated_by}")
        print(f"Risk Assessment: {report.risk_assessment.upper()} (Score: {report.risk_score:.3f})")
        
        print(f"\nPROCESSING METRICS:")
        for key, value in report.processing_metrics.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        
        print(f"\nEXECUTIVE SUMMARY:")
        summary_lines = str(report.summary).split('\n')
        for line in summary_lines:
            if line.strip():
                print(f"  {line.strip()}")
        
        print(f"\nKEY FINDINGS:")
        for i, finding in enumerate(report.key_findings, 1):
            print(f"  {i}. {finding}")
        
        print(f"\nSTRATEGIC RECOMMENDATIONS:")
        for i, recommendation in enumerate(report.recommendations, 1):
            print(f"  {i}. {recommendation}")
        
        print(f"\nACTIONS TAKEN:")
        for i, action in enumerate(report.actions_taken, 1):
            print(f"  {i}. {action}")
        
        print(f"\nPOLICY REFERENCES ({len(report.policy_references)} documents):")
        for policy in report.policy_references:
            print(f"  - {policy}")
        
        print(f"\nAGENT CONTRIBUTIONS:")
        for agent, contribution in report.agent_contributions.items():
            print(f"  {agent}: {contribution[:100]}...")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get enhanced performance metrics"""
        return {
            **self.performance_metrics,
            "success_rate": (
                self.performance_metrics["successful_analyses"] / 
                self.performance_metrics["total_requests"] * 100
                if self.performance_metrics["total_requests"] > 0 else 0
            ),
            "timestamp": datetime.now().isoformat()
        }

    
# ==============================
# TEST SUITE IMPLEMENTATION
# ==============================

async def run_agent_activation_test_suite():
    """Run comprehensive test suite for agent activation"""
    log_filename = setup_logging()
    
    print("🧪 AGENT ACTIVATION TEST SUITE")
    print("With Enhanced Banking Multi-Agent System")
    print("=" * 80)
    
    # Initialize the enhanced system with tracking enabled
    print("Initializing EnhancedBankingSequentialOrchestration with agent tracking...")
    enhanced_banking_system = EnhancedBankingSequentialOrchestration(enable_tracking=True)
    
    # Pre-load enhanced documents
    print("Pre-loading enhanced banking documents to ChromaDB...")
    await enhanced_banking_system.load_enhanced_documents()
    print("Enhanced banking documents ready for testing\n")
    
    # Test scenarios with expected agent activations
    test_scenarios = [
        {
            "customer_id": "12345",
            "query": "I need comprehensive financial planning including investments and retirement options",
            "expected_agents": ["Enhanced_Data_Gatherer", "Enhanced_Loan_Analyst", "Enhanced_Risk_Analyst", "Enhanced_Synthesis_Coordinator"]
        },
        {
            "customer_id": "67890", 
            "query": "I'm concerned about potential fraud - I see multiple unfamiliar small transactions",
            "expected_agents": ["Enhanced_Data_Gatherer", "Enhanced_Fraud_Analyst", "Enhanced_Risk_Analyst", "Enhanced_Synthesis_Coordinator"]
        },
        {
            "customer_id": "11111",
            "query": "I want to apply for a mortgage and need to understand my eligibility and options",
            "expected_agents": ["Enhanced_Data_Gatherer", "Enhanced_Loan_Analyst", "Enhanced_Risk_Analyst", "Enhanced_Synthesis_Coordinator"]
        },
        {
            "customer_id": "12345",
            "query": "Can you help me optimize my banking relationship and reduce fees?",
            "expected_agents": ["Enhanced_Data_Gatherer", "Enhanced_Support_Specialist", "Enhanced_Risk_Analyst", "Enhanced_Synthesis_Coordinator"]
        }
    ]
    
    test_results = []
    
    print(f"🧪 Running {len(test_scenarios)} test scenarios...")
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{'='*80}")
        print(f"TEST CASE {i}/{len(test_scenarios)}")
        print(f"Customer: {scenario['customer_id']}")
        print(f"Query: {scenario['query']}")
        print(f"Expected Agents: {', '.join(scenario['expected_agents'])}")
        print(f"{'='*80}")
        
        try:
            # Run test analysis
            test_result = await enhanced_banking_system.run_test_analysis(
                scenario["customer_id"],
                scenario["query"],
                scenario["expected_agents"]
            )
            
            test_results.append(test_result)
            
            # Display test results
            print(f"✅ Activated Agents: {', '.join(test_result.activated_agents)}")
            print(f"⏱️  Processing Time: {test_result.processing_time:.2f}s")
            print(f"📈 Response Quality: {test_result.response_quality['overall_score']:.2f}")
            print(f"🎯 Test Passed: {test_result.passed}")
            
            if not test_result.all_expected_activated:
                print(f"❌ Missing agents: {test_result.missing_agents}")
            
            if test_result.unexpected_agents:
                print(f"⚠️  Unexpected agents: {test_result.unexpected_agents}")
            
            if i < len(test_scenarios):
                print(f"\nPreparing next test...")
                await asyncio.sleep(2)
                
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    # Generate test report
    await generate_comprehensive_test_report(test_results, log_filename)
    
    return test_results

async def generate_comprehensive_test_report(test_results: List[TestResult], log_filename: str):
    """Generate comprehensive test report"""
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE TEST REPORT")
    print(f"{'='*80}")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r.passed)
    activation_success_rate = sum(1 for r in test_results if r.all_expected_activated) / total_tests * 100
    avg_processing_time = sum(r.processing_time for r in test_results) / total_tests if total_tests > 0 else 0
    avg_response_quality = sum(r.response_quality['overall_score'] for r in test_results) / total_tests if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed Tests: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"Agent Activation Success: {activation_success_rate:.1f}%")
    print(f"Average Processing Time: {avg_processing_time:.2f}s")
    print(f"Average Response Quality: {avg_response_quality:.2f}")
    
    # Agent activation statistics
    agent_activation_counts = {}
    for result in test_results:
        for agent in result.activated_agents:
            agent_activation_counts[agent] = agent_activation_counts.get(agent, 0) + 1
    
    print(f"\n🤖 AGENT ACTIVATION STATISTICS:")
    for agent, count in sorted(agent_activation_counts.items()):
        percentage = (count / total_tests) * 100
        print(f"  {agent}: {count}/{total_tests} ({percentage:.1f}%)")
    
    # Failed tests analysis
    failed_tests = [r for r in test_results if not r.passed]
    if failed_tests:
        print(f"\n❌ FAILED TESTS ANALYSIS:")
        for i, result in enumerate(failed_tests, 1):
            print(f"{i}. Query: {result.query}")
            if not result.all_expected_activated:
                print(f"   Missing agents: {result.missing_agents}")
            print(f"   Response quality: {result.response_quality['overall_score']:.2f}")
            print()
    
    # Save detailed report
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "activation_success_rate": activation_success_rate,
            "avg_processing_time": avg_processing_time,
            "avg_response_quality": avg_response_quality
        },
        "agent_activation": agent_activation_counts,
        "test_details": [
            {
                "query": r.query,
                "customer_id": r.customer_id,
                "expected_agents": r.expected_agents,
                "activated_agents": r.activated_agents,
                "processing_time": r.processing_time,
                "passed": r.passed,
                "response_quality": r.response_quality,
                "missing_agents": r.missing_agents,
                "unexpected_agents": r.unexpected_agents
            }
            for r in test_results
        ]
    }
    
    report_filename = f"logs/agent_activation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Detailed report saved: {report_filename}")
    print(f"📝 Execution log: {log_filename}")

async def enhanced_main():
    """Enhanced main demo execution"""
    # Setup logging first
    log_filename = setup_logging()
    
    print("ENHANCED BANKING MULTI-AGENT RAG SYSTEM")
    print("With Advanced ChromaDB Integration and Azure SQL Connectivity")
    print("=" * 80)
    
    # Initialize the enhanced system
    print("Initializing EnhancedBankingSequentialOrchestration...")
    enhanced_banking_system = EnhancedBankingSequentialOrchestration()
    
    # Pre-load enhanced documents
    print("Pre-loading enhanced banking documents to ChromaDB...")
    await enhanced_banking_system.load_enhanced_documents()
    print("Enhanced banking documents ready for analysis\n")
    
    # Enhanced test scenarios
    enhanced_scenarios = [
        {
            "customer_id": "12345",
            "query": "I need comprehensive financial planning including investments and retirement options"
        },
        {
            "customer_id": "67890",
            "query": "I'm concerned about potential fraud - I see multiple unfamiliar small transactions"
        },
        {
            "customer_id": "11111", 
            "query": "I want to apply for a mortgage and need to understand my eligibility and options"
        },
        {
            "customer_id": "12345",
            "query": "Can you help me optimize my banking relationship and reduce fees?"
        }
    ]
    
    # Run enhanced analysis for each scenario
    enhanced_reports = []
    
    for i, scenario in enumerate(enhanced_scenarios, 1):
        print(f"\n{'='*80}")
        print(f"ENHANCED BANKING ANALYSIS {i}/{len(enhanced_scenarios)}")
        print(f"Customer: {scenario['customer_id']}")
        print(f"Query: {scenario['query']}")
        print(f"{'='*80}")
        
        try:
            # Run enhanced sequential analysis
            report = await enhanced_banking_system.run_enhanced_analysis(
                scenario["customer_id"],
                scenario["query"]
            )
            enhanced_reports.append(report)
            
            # Display this enhanced report immediately
            enhanced_banking_system.display_enhanced_report(report)
            
            if i < len(enhanced_scenarios):
                print(f"\nPreparing next enhanced analysis...")
                await asyncio.sleep(3)
                
        except Exception as e:
            print(f"Error in enhanced banking analysis {i}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Display enhanced performance metrics
    performance_metrics = enhanced_banking_system.get_performance_metrics()
    print(f"\nENHANCED PERFORMANCE METRICS:")
    print(f"  Total Requests: {performance_metrics['total_requests']}")
    print(f"  Successful Analyses: {performance_metrics['successful_analyses']}")
    print(f"  Success Rate: {performance_metrics['success_rate']:.1f}%")
    print(f"  Average Processing Time: {performance_metrics['average_processing_time']:.2f} seconds")
    
    print(f"\nENHANCED BANKING SEQUENTIAL ORCHESTRATION DEMO COMPLETED!")
    print(f"Total enhanced scenarios processed: {len(enhanced_reports)}")
    print(f"Log file: {log_filename}")
    
    # Display enhanced summary
    if enhanced_reports:
        print(f"\nENHANCED ANALYSIS SUMMARY:")
        for i, report in enumerate(enhanced_reports, 1):
            print(f"  {i}. Customer {report.customer_id}: {report.risk_assessment.upper()} risk - {report.query[:40]}...")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run enhanced banking system with agent activation testing')
    parser.add_argument('--test', action='store_true', help='Run agent activation test suite')
    parser.add_argument('--demo', action='store_true', help='Run demo scenarios')
    parser.add_argument('--all', action='store_true', help='Run both test and demo')
    
    args = parser.parse_args()
    
    if args.test or args.all:
        print("Starting agent activation test suite...")
        test_results = asyncio.run(run_agent_activation_test_suite())
    
    if args.demo or args.all or (not args.test and not args.demo and not args.all):
        print("Starting enhanced banking demo...")
        asyncio.run(enhanced_main())