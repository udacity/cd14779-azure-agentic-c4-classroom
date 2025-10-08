import asyncio
import os
import pyodbc
from contextlib import contextmanager
from typing import Dict, List, Optional
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from dotenv import load_dotenv
load_dotenv("../../../.env")

class PatientDataConnector:
    """Data connector for patient records from Azure SQL Server"""
    
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or os.getenv("AZURE_SQL_CONNECTION_STRING")
        if not self.connection_string:
            raise ValueError("AZURE_SQL_CONNECTION_STRING environment variable not set")
        
        # Load initial data from database
        self.patient_records = self._load_patient_data()
    
    # Database connection helper for Azure SQL Server
    @contextmanager
    def get_db_connection(self):
        conn = pyodbc.connect(self.connection_string)
        try:
            yield conn
        finally:
            conn.close()

    def _load_patient_data(self) -> List[Dict]:
        """Load patient data from Azure SQL database"""
        # TODO: Implement database query to load patient records
        # You need to:
        # 1. Connect to Azure SQL using the connection string
        # 2. Execute a SELECT query on the patients table
        # 3. Format the data into the expected structure
        
        # Placeholder - replace with actual database query
        print("⚠️  Database connection not implemented - using simulated data")
        
        # Simulated data (remove this once database is connected)
        return [
            {"id": 1, "name": "John Smith", "age": 45, "last_visit": "2024-01-10", "conditions": ["hypertension"]},
            {"id": 2, "name": "Maria Garcia", "age": 32, "last_visit": "2024-01-15", "conditions": ["asthma"]},
            {"id": 3, "name": "David Chen", "age": 68, "last_visit": "2024-01-08", "conditions": ["diabetes", "arthritis"]},
            {"id": 4, "name": "Sarah Johnson", "age": 28, "last_visit": "2023-12-20", "conditions": []},
        ]
    
    def get_patient_info(self, patient_name: str) -> Optional[Dict]:
        """Get patient information by name from database"""
        # TODO: Implement database query to get specific patient info
        # This should query the database for the patient by name
        
        for patient in self.patient_records:
            if patient["name"].lower() == patient_name.lower():
                return patient
        return None
    
    def get_patient_history(self, patient_name: str) -> str:
        """Get patient medical history from database"""
        patient = self.get_patient_info(patient_name)
        if patient:
            return f"Patient: {patient['name']}, Age: {patient['age']}, Conditions: {', '.join(patient['conditions'])}, Last Visit: {patient['last_visit']}"
        return "Patient not found in database"
    
    def add_patient_visit(self, patient_name: str, symptoms: str, diagnosis: str) -> bool:
        """Add a new patient visit to the database"""
        # TODO: Implement database insert for new patient visit
        # This should insert a new record into the patient_visits table
        
        print(f"📝 Would add visit for {patient_name}: Symptoms: {symptoms}, Diagnosis: {diagnosis}")
        return True

class MedicalAgent:
    """Base class for all medical specialist agents"""
    
    def __init__(self, name: str, specialty: str):
        self.name = name
        self.specialty = specialty
        self.kernel = Kernel()
        
        # TODO: Initialize the data connector with Azure SQL connection
        # self.data_connector = PatientDataConnector()
        self.data_connector = None  # Remove this once implemented
        
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="chat_completion",
                deployment_name=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
            )
        )
    
    async def process_request(self, request: str) -> str:
        """Process medical request - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement this method")

class GeneralPracticeAgent(MedicalAgent):
    """Agent specializing in general health concerns"""
    
    def __init__(self):
        super().__init__("General Practitioner", "General health and routine care")
    
    async def process_request(self, request: str) -> str:
        """Handle general health inquiries"""
        
        # TODO: Create a better prompt for general practice
        # The prompt should ask for:
        # - Assessment of general symptoms
        # - Initial care recommendations
        # - When to seek urgent care
        # - Follow-up instructions
        
        prompt = "You are a general practitioner. Help with this health concern: {{$request}}"
        
        function = KernelFunctionFromPrompt(
            function_name="general_consultation",
            plugin_name="general_practice",
            prompt=prompt
        )
        
        # TODO: Integrate patient data from database
        # patient_info = self.data_connector.get_patient_info(extracted_name)
        
        result = await self.kernel.invoke(function, request=request)
        return f"🩺 **General Practice Consultation**\n\n{result}"

class EmergencyAgent(MedicalAgent):
    """Agent specializing in emergency situations"""
    
    def __init__(self):
        super().__init__("Emergency Specialist", "Urgent and critical care")
    
    async def process_request(self, request: str) -> str:
        """Handle emergency medical situations"""
        
        # TODO: Create a better prompt for emergency care
        # The prompt should ask for:
        # - Immediate action steps
        # - Emergency warning signs
        # - First aid instructions if applicable
        # - Urgency assessment
        
        prompt = "You are an emergency specialist. Handle this urgent case: {{$request}}"
        
        function = KernelFunctionFromPrompt(
            function_name="emergency_care",
            plugin_name="emergency",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"🚨 **Emergency Care**\n\n{result}"

# TODO: Implement the PediatricAgent class
# This agent should handle children's health issues
# class PediatricAgent(MedicalAgent):
#     def __init__(self):
#         super().__init__("Pediatric Specialist", "Children's health and development")
    
#     async def process_request(self, request: str) -> str:
#         # TODO: Create a prompt for pediatric care
#         # The prompt should ask for:
#         # - Age-appropriate assessment
#         # - Pediatric warning signs
#         # - Child-specific care instructions
#         # - Growth and development considerations
#         pass

class TriageRouter:
    """Intelligent router that directs patient requests to appropriate specialists"""
    
    def __init__(self):
        self.specialists = {
            "general": GeneralPracticeAgent(),
            "emergency": EmergencyAgent()
            # TODO: Add PediatricAgent to the specialists dictionary
        }
        
        self.kernel = Kernel()
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="chat_completion",
                deployment_name=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
            )
        )
    
    async def route_patient_request(self, patient_request: str) -> dict:
        """Analyze patient request and route to appropriate specialist"""
        
        # TODO: Create a routing prompt for medical triage
        # The prompt should determine:
        # - Which specialist should handle the case
        # - The urgency level (Routine, Urgent, Emergency)
        # - Brief reasoning for the decision
        
        routing_prompt = """
        Analyze this patient request and suggest routing.

        PATIENT REQUEST: {{$request}}

        Available specialists:
        - general: General health concerns, routine symptoms
        - emergency: Critical symptoms, injuries, severe pain

        Respond with:
        Specialist: [general/emergency]
        Urgency: [Routine/Urgent/Emergency]
        Reasoning: [brief explanation]
        """
        
        routing_function = KernelFunctionFromPrompt(
            function_name="medical_routing",
            plugin_name="triage",
            prompt=routing_prompt
        )
        
        routing_result = await self.kernel.invoke(
            routing_function, 
            request=patient_request
        )
        
        # Parse the routing decision
        routing_text = str(routing_result)
        routing_decision = self._parse_routing_decision(routing_text)
        
        return routing_decision
    
    def _parse_routing_decision(self, routing_text: str) -> dict:
        """Parse the routing decision from the AI response"""
        # TODO: Implement parsing logic
        # Extract specialist, urgency, and reasoning from the response
        # Return a dictionary with these values
        
        return {
            "specialist": "general",  # placeholder
            "urgency": "Routine",     # placeholder
            "reasoning": "Parse logic not implemented",
            "raw_response": routing_text
        }
    
    async def process_patient_request(self, patient_request: str) -> dict:
        """Complete routing and processing of patient request"""
        
        print(f"📥 Patient Request: {patient_request}")
        print("🔄 Analyzing symptoms and determining routing...")
        
        # Step 1: Route the request
        routing_decision = await self.route_patient_request(patient_request)
        
        print(f"✅ Triage Decision:")
        print(f"   Specialist: {routing_decision['specialist']}")
        print(f"   Urgency: {routing_decision['urgency']}")
        print(f"   Reasoning: {routing_decision['reasoning']}")
        
        # Step 2: Process with appropriate specialist
        specialist_key = routing_decision["specialist"]
        if specialist_key in self.specialists:
            print(f"🔧 Connecting to {self.specialists[specialist_key].name}...")
            specialist_result = await self.specialists[specialist_key].process_request(patient_request)
            
            return {
                "routing_decision": routing_decision,
                "specialist_response": specialist_result,
                "specialist_name": self.specialists[specialist_key].name
            }
        else:
            return {
                "routing_decision": routing_decision,
                "specialist_response": "❌ No suitable specialist found for this case.",
                "specialist_name": "Unknown"
            }

class HospitalTriageSystem:
    """Main hospital triage system coordinating all agents"""
    
    def __init__(self):
        self.router = TriageRouter()
    
    async def handle_patient_requests(self, requests: list):
        """Process multiple patient requests"""
        
        print("🏥 HOSPITAL TRIAGE MULTI-AGENT SYSTEM")
        print("Intelligent Routing and Medical Triage Demo")
        print("=" * 60)
        print("Complete the TODOs to make this system work!")
        print()
        
        # TODO: Test database connection
        # try:
        #     data_connector = PatientDataConnector()
        #     print("✅ Azure SQL Database connection successful")
        # except Exception as e:
        #     print(f"❌ Database connection failed: {e}")
        
        for i, request in enumerate(requests, 1):
            print(f"\n{'#' * 60}")
            print(f"PATIENT REQUEST #{i}")
            print(f"{'#' * 60}")
            
            try:
                result = await self.router.process_patient_request(request)
                self.display_result(result)
                
                # Small pause between requests
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Error processing request: {e}")
                continue

    def display_result(self, result: dict):
        """Display the processing result"""
        print(f"\n🎯 MEDICAL TRIAGE COMPLETE")
        print(f"Handled by: {result['specialist_name']}")
        print(f"Urgency: {result['routing_decision']['urgency']}")
        print("\n" + "=" * 50)
        print(f"{result['specialist_response']}")
        print("=" * 50)

async def main():
    # Check environment
    required_vars = [
        "AZURE_TEXTGENERATOR_DEPLOYMENT_NAME", 
        "AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT", 
        "AZURE_TEXTGENERATOR_DEPLOYMENT_KEY",
        "AZURE_SQL_CONNECTION_STRING"  # Added requirement
    ]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("❌ Missing environment variables. Please check your .env file.")
        print(f"Missing: {missing_vars}")
        return
    
    hospital_system = HospitalTriageSystem()
    
    # Sample patient requests
    patient_requests = [
        "I have a mild cough and runny nose for 3 days",
        "Severe chest pain and difficulty breathing started 30 minutes ago",
        "My child has a fever of 102°F and is very sleepy",
        "I fell and hurt my wrist, there's swelling and pain",
        "Persistent headache for 2 weeks that won't go away",
        "Cut my finger while cooking and it's bleeding a lot"
    ]
    
    # Process patient requests
    await hospital_system.handle_patient_requests(patient_requests)

if __name__ == "__main__":
    asyncio.run(main())