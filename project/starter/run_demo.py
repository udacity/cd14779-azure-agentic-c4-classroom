# bank_slim/run_demo.py
import asyncio
import os
import csv
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from shared_state import SharedState
from sk_wrapper import SKWrapper
from rag_utils import download_blobs_from_azure, load_documents, seed_collection_from_txt, print_collection_contents
from agents.banking_call import BankingCallAgent
from agents.coordinator import CoordinatorAgent, DataConnector
from agents.fraud import FraudAgent
from agents.loans import LoansAgent
from agents.support import SupportAgent
from agents.synthesis import SynthesisAgent
load_dotenv("../../.env")

class AgentContext:
    def __init__(self, customer_id: str, payload: dict):
        self.customer_id = customer_id
        self.payload = payload

class TestResult:
    def __init__(self, query, expected_agents, actual_agents, expected_keywords, response):
        self.query = query
        self.expected_agents = expected_agents
        self.actual_agents = actual_agents
        self.expected_keywords = expected_keywords
        self.response = response
        self.agents_match = bool([agent for agent in set(expected_agents.split(',')) if agent in actual_agents])
        # Check if expected keywords are in the response (case insensitive)
        self.keywords_match = any(
            keyword.lower() in response.lower() 
            for keyword in expected_keywords.split(',')
        ) if expected_keywords else True
        self.passed = self.agents_match and self.keywords_match

async def setup_system():
    """Set up the banking system with all agents"""
    # Read API config from environment variables.
    api_key = os.environ.get("AZURE_TEXTGENERATOR_DEPLOYMENT_KEY") or os.environ.get("OPENAI_API_KEY")
    conn_type = os.environ.get("SK_CONN", "openai")
    endpoint = os.environ.get("AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT")
    if not api_key:
        raise RuntimeError("API key not found in environment. Set SK_API_KEY or OPENAI_API_KEY before running demo.")

    shared = SharedState()
    sk = SKWrapper(api_key=api_key, endpoint=endpoint, model=os.environ.get("AZURE_TEXTGENERATOR_DEPLOYMENT_NAME", "gpt-4o-mini"), connection_type=conn_type)
    
    # Optional local persistence for Chroma
    CHROMA_PERSIST_DIR = "./chroma_data"
    # Initialize Chroma client
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    
    # Create or get Chroma collection with Azure embeddings
    azure_embedding_function = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.environ.get("AZURE_TEXTEMBEDDING_DEPLOYMENT_KEY"),
        api_base=os.environ.get("AZURE_TEXTEMBEDDING_DEPLOYMENT_ENDPOINT"),
        api_type=conn_type,
        api_version="2024-12-01-preview",
        deployment_id=os.environ.get("AZURE_TEXTEMBEDDING_DEPLOYMENT_NAME")
    )
    collection = client.get_or_create_collection(
        name="BankingDocs",
        embedding_function=azure_embedding_function
    )

    # Configuration - Replace these values with your own
    CONNECTION_STRING = os.getenv("BLOB_CONNECTION_STRING")
    CONTAINER_NAME = "udacityproject"
    DOCS_DIR = "./docs"
    
    print(f"Downloading docs to {DOCS_DIR}...")
    # Run the download
    download_blobs_from_azure(CONNECTION_STRING, CONTAINER_NAME, DOCS_DIR)

    # seed the vector DB with docs from Azure Blob Storage
    seed_collection_from_txt(collection, load_documents(DOCS_DIR))
    print("Collection seeded. Example contents:")
    print_collection_contents(client, collection_obj=collection, max_items=2)

    # Example in-memory datastore for demonstration (replace with real DB connector)
    # Mock customer data for educational purposes
    datastore = {
        "C12345": {
            "income": 4500,
            "transactions": [
                {"id": "t1", "amount": 49, "ts": "2025-08-01"},
                {"id": "t2", "amount": 6000, "ts": "2025-08-25"},
            ],
        },
        "C67890": {
            "income": 6500,
            "transactions": [
                {"id": "t3", "amount": 120, "ts": "2025-08-05"},
                {"id": "t4", "amount": 85, "ts": "2025-08-15"},
            ],
        }
    }
    
    data_connector = DataConnector(datastore=datastore,connection_string=os.getenv("AZURE_SQL_CONNECTION_STRING"))
    print("Data connector initialized.")
    # Construct agents with SK so they reason using the LLM
    fraud = FraudAgent(sk, azure_embedding_function, collection)
    loans = LoansAgent(sk, azure_embedding_function, collection)
    support = SupportAgent(sk, azure_embedding_function, collection)
    synthesis = SynthesisAgent(sk)

    workers = {
        "fraud": fraud,
        "loans": loans,
        "support": support,
        "synthesis": synthesis,
    }

    coord = CoordinatorAgent(workers, shared, sk, data_connector=data_connector)
    entry = BankingCallAgent(coord)
    
    return entry, shared

async def run_single_test(entry, customer_id, query):
    """Run a single test case"""
    ctx = AgentContext(customer_id, {"query": query})
    result = await entry.receive_call(ctx)
    return result

async def run_test_suite():
    """Run all test cases from the CSV file"""
    entry, shared = await setup_system()
    
    test_results = []
    
    # Read test cases from CSV
    with open('synthetic_queries.csv', 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader):
            print(f"\n=== Running Test Case {i+1} ===")
            print(f"Query: {row['query']}")
            print(f"Expected Agents: {row['expected_agents']}")
            
            # Reset shared state between tests
            shared.activated_agents = []
            
            # Run the test
            result = await run_single_test(entry, row['customer_id'], row['query'])
            print(result)
            # Record which agents were activated
            activated_agents = ",".join(shared.activated_agents)
            print(f"Activated Agents: {activated_agents}")
            print(f"Expected Keywords: {row['expected_response_keywords']}")
            # Create test result
            test_result = TestResult(
                query=row['query'],
                expected_agents=row['expected_agents'],
                actual_agents=activated_agents,
                expected_keywords=row['expected_response_keywords'],
                response=str(result)
            )
            
            test_results.append(test_result)
            
            print(f"Agents Match: {test_result.agents_match}")
            print(f"Keywords Match: {test_result.keywords_match}")
            print(f"Test Passed: {test_result.passed}")
            print("Response:")
            print(result[:200] + "..." if len(result) > 200 else result)
    
    # Print summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed_count = sum(1 for r in test_results if r.passed)
    total_count = len(test_results)
    
    print(f"Passed: {passed_count}/{total_count} ({passed_count/total_count*100:.1f}%)")
    
    # Print failed tests
    failed_tests = [r for r in test_results if not r.passed]
    if failed_tests:
        print("\nFAILED TESTS:")
        for i, result in enumerate(failed_tests):
            print(f"{i+1}. Query: {result.query}")
            if not result.agents_match:
                print(f"   Expected agents: {result.expected_agents}")
                print(f"   Actual agents: {result.actual_agents}")
            if not result.keywords_match:
                print(f"   Expected keywords: {result.expected_keywords}")
            print()
    
    return test_results

async def demo():
    """Run the original demo"""
    entry, _ = await setup_system()
    
    # The only input to the entire system is the single dict with customer_id and query:
    user_input = {"customer_id": "C12345", "query": "I saw an unexpected large debit and I'd like to apply for a 2,000 USD personal loan."}
    
    
    result = await run_single_test(entry, user_input["customer_id"], user_input["query"])

    print("\n==== FINAL RESULT ====")
    print(result)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run the banking AI system')
    parser.add_argument('--test', action='store_true', help='Run test suite instead of demo')
    args = parser.parse_args()
    
    if args.test:
        test_results=asyncio.run(run_test_suite())
        # Save test results to a file
        with open("logs/test_results.txt", "w", encoding="utf-8") as f:
            for i, result in enumerate(test_results):
                f.write(f"Test Case {i+1}:\n")
                f.write(f"Query: {result.query}\n")
                f.write(f"Expected Agents: {result.expected_agents}\n")
                f.write(f"Actual Agents: {result.actual_agents}\n")
                f.write(f"Agents Match: {result.agents_match}\n")
                f.write(f"Expected Keywords: {result.expected_keywords}\n")
                f.write(f"Keywords Match: {result.keywords_match}\n")
                f.write(f"Test Passed: {result.passed}\n")
                f.write(f"Response: {result.response}\n")
                f.write("\n" + "="*40 + "\n\n")
    else:
        asyncio.run(demo())