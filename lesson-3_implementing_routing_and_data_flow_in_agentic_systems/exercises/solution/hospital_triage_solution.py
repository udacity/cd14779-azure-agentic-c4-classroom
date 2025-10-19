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
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                patients = []
                
                # Query to get patient data
                cursor.execute("""
                    SELECT patient_id, name, age, last_visit, conditions 
                    FROM patients 
                    ORDER BY last_visit DESC
                """)
                
                for row in cursor.fetchall():
                    patient_id, name, age, last_visit, conditions_str = row
                    
                    # Parse conditions (assuming comma-separated string)
                    conditions = []
                    if conditions_str:
                        conditions = [cond.strip() for cond in conditions_str.split(',')]
                    
                    patients.append({
                        "id": patient_id,
                        "name": name,
                        "age": age,
                        "last_visit": last_visit.isoformat() if hasattr(last_visit, 'isoformat') else str(last_visit),
                        "conditions": conditions
                    })
                
                print(f"✅ Loaded {len(patients)} patients from database")
                return patients
                
        except Exception as e:
            print(f"❌ Error loading patient data: {e}")
            # Fallback to simulated data
            return [
                {"id": 1, "name": "John Smith", "age": 45, "last_visit": "2024-01-10", "conditions": ["hypertension"]},
                {"id": 2, "name": "Maria Garcia", "age": 32, "last_visit": "2024-01-15", "conditions": ["asthma"]},
                {"id": 3, "name": "David Chen", "age": 68, "last_visit": "2024-01-08", "conditions": ["diabetes", "arthritis"]},
                {"id": 4, "name": "Sarah Johnson", "age": 28, "last_visit": "2023-12-20", "conditions": []},
            ]
    
    def get_patient_info(self, patient_name: str) -> Optional[Dict]:
        """Get patient information by name from database"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT patient_id, name, age, last_visit, conditions 
                    FROM patients 
                    WHERE LOWER(name) = LOWER(?)
                """, patient_name)
                
                row = cursor.fetchone()
                if row:
                    patient_id, name, age, last_visit, conditions_str = row
                    
                    conditions = []
                    if conditions_str:
                        conditions = [cond.strip() for cond in conditions_str.split(',')]
                    
                    return {
                        "id": patient_id,
                        "name": name,
                        "age": age,
                        "last_visit": last_visit.isoformat() if hasattr(last_visit, 'isoformat') else str(last_visit),
                        "conditions": conditions
                    }
                
                return None
                
        except Exception as e:
            print(f"❌ Error fetching patient info: {e}")
            # Fallback to in-memory data
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
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Insert new visit record
                cursor.execute("""
                    INSERT INTO patient_visits (patient_name, symptoms, diagnosis, visit_date)
                    VALUES (?, ?, ?, GETDATE())
                """, patient_name, symptoms, diagnosis)
                
                conn.commit()
                print(f"✅ Added visit record for {patient_name}")
                return True
                
        except Exception as e:
            print(f"❌ Error adding patient visit: {e}")
            return False

class MedicalAgent:
    """Base class for all medical specialist agents"""
    
    def __init__(self, name: str, specialty: str):
        self.name = name
        self.specialty = specialty
        self.kernel = Kernel()
        self.data_connector = PatientDataConnector()
        
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
        
        prompt = """
        You are an experienced general practitioner. Analyze this patient's symptoms and provide professional medical advice.

        PATIENT REQUEST: {{$request}}

        PATIENT HISTORY: {{$patient_history}}

        Please provide:
        🩺 SYMPTOM ASSESSMENT:
        - Likely causes based on symptoms
        - Severity evaluation
        
        💊 INITIAL CARE RECOMMENDATIONS:
        - Home care instructions
        - Over-the-counter suggestions if appropriate
        - Self-monitoring advice
        
        🚨 WHEN TO SEEK URGENT CARE:
        - Red flag symptoms to watch for
        - When to contact healthcare provider
        
        📅 FOLLOW-UP INSTRUCTIONS:
        - Timeline for improvement
        - When to schedule follow-up

        Always include: "If symptoms worsen or you have concerns, contact your healthcare provider."
        """
        
        function = KernelFunctionFromPrompt(
            function_name="general_consultation",
            plugin_name="general_practice",
            prompt=prompt
        )
        
        # Try to extract patient name and get history
        patient_history = "No patient history available"
        # Simple name extraction (in real scenario, use more sophisticated NLP)
        if "my name is" in request.lower():
            name_part = request.lower().split("my name is")[1].split(".")[0].strip()
            patient_history = self.data_connector.get_patient_history(name_part)
        
        result = await self.kernel.invoke(
            function, 
            request=request,
            patient_history=patient_history
        )
        
        # Log the consultation
        self.data_connector.add_patient_visit("Unknown Patient", request, "General Consultation")
        
        return f"🩺 **General Practice Consultation**\n\n{result}"

class EmergencyAgent(MedicalAgent):
    """Agent specializing in emergency situations"""
    
    def __init__(self):
        super().__init__("Emergency Specialist", "Urgent and critical care")
    
    async def process_request(self, request: str) -> str:
        """Handle emergency medical situations"""
        
        prompt = """
        You are an emergency medicine specialist. Evaluate this urgent medical situation and provide emergency guidance.

        URGENT REQUEST: {{$request}}

        Please provide:
        🚨 IMMEDIATE ACTION ASSESSMENT:
        - Severity level (Mild/Moderate/Severe/Critical)
        - Time sensitivity
        
        🆘 EMERGENCY RESPONSE:
        - Immediate first steps
        - When to call emergency services
        - What to do while waiting for help
        
        ⚠️ WARNING SIGNS:
        - Critical symptoms to monitor
        - When situation becomes life-threatening
        
        🏥 URGENT CARE RECOMMENDATIONS:
        - Where to seek care (ER, urgent care, telehealth)
        - Timeline for seeking medical attention

        Always start with: "THIS IS URGENT MEDICAL ADVICE:"
        """
        
        function = KernelFunctionFromPrompt(
            function_name="emergency_care",
            plugin_name="emergency",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        
        # Log emergency consultation
        self.data_connector.add_patient_visit("Emergency Patient", request, "Emergency Consultation")
        
        return f"🚨 **Emergency Care**\n\n{result}"

class PediatricAgent(MedicalAgent):
    """Agent specializing in children's health issues"""
    
    def __init__(self):
        super().__init__("Pediatric Specialist", "Children's health and development")
    
    async def process_request(self, request: str) -> str:
        """Handle pediatric health inquiries"""
        
        prompt = """
        You are a pediatric specialist. Provide age-appropriate medical advice for this child's health concern.

        PEDIATRIC REQUEST: {{$request}}

        Please provide:
        👶 PEDIATRIC ASSESSMENT:
        - Age-specific considerations
        - Common childhood illness evaluation
        - Developmental stage relevance
        
        🌡️ PEDIATRIC CARE GUIDANCE:
        - Child-appropriate home care
        - Dosing considerations if mentioned
        - Comfort measures for children
        
        🚨 PEDIATRIC RED FLAGS:
        - Emergency signs in children
        - When to seek immediate care
        - Dehydration warning signs
        
        📞 PEDIATRIC FOLLOW-UP:
        - When to contact pediatrician
        - Monitoring guidelines for parents
        - Expected recovery timeline

        Focus on child-specific concerns and parent guidance.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="pediatric_consultation",
            plugin_name="pediatrics",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        
        # Log pediatric consultation
        self.data_connector.add_patient_visit("Pediatric Patient", request, "Pediatric Consultation")
        
        return f"👶 **Pediatric Consultation**\n\n{result}"

class TriageRouter:
    """Intelligent router that directs patient requests to appropriate specialists"""
    
    def __init__(self):
        self.specialists = {
            "general": GeneralPracticeAgent(),
            "emergency": EmergencyAgent(),
            "pediatric": PediatricAgent()
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
        
        routing_prompt = """
        You are a medical triage specialist. Analyze this patient request and determine the appropriate routing.

        PATIENT REQUEST: {{$request}}

        Available specialists:
        - general: Routine symptoms, chronic conditions, general health concerns
        - pediatric: Children's health (mentions of child, baby, toddler, pediatric)
        - emergency: Severe pain, injuries, breathing difficulties, chest pain, bleeding

        Urgency levels:
        - Routine: Non-urgent symptoms, routine follow-ups
        - Urgent: Needs attention within 24 hours
        - Emergency: Needs immediate medical attention

        Consider:
        - Patient age mentions (child, baby, pediatric → pediatric)
        - Symptom severity (severe, intense, unbearable → emergency)
        - Specific concerning symptoms (chest pain, difficulty breathing → emergency)

        Respond in this exact format:
        Specialist: [general/pediatric/emergency]
        Urgency: [Routine/Urgent/Emergency]
        Reasoning: [brief medical reasoning for this decision]
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
        lines = routing_text.strip().split('\n')
        decision = {
            "specialist": "general",  # default
            "urgency": "Routine",     # default
            "reasoning": "Unable to parse routing decision",
            "raw_response": routing_text
        }
        
        for line in lines:
            line = line.strip()
            if line.startswith('Specialist:'):
                decision["specialist"] = line.split(':')[1].strip().lower()
            elif line.startswith('Urgency:'):
                decision["urgency"] = line.split(':')[1].strip()
            elif line.startswith('Reasoning:'):
                decision["reasoning"] = line.split(':')[1].strip()
        
        return decision
    
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
        
        # Test database connection
        try:
            data_connector = PatientDataConnector()
            print("✅ Azure SQL Database connection successful")
            
            # Show sample patient data
            sample_patient = data_connector.get_patient_info("John Smith")
            if sample_patient:
                print(f"📊 Sample patient data: {sample_patient['name']}, {sample_patient['age']} years old")
                
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
        
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
        "AZURE_SQL_CONNECTION_STRING"
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
        "Cut my finger while cooking and it's bleeding a lot",
        "My 2-year-old has diarrhea and vomiting since yesterday",
        "I have mild back pain after gardening yesterday",
        "My name is John Smith and I have a sore throat"
    ]
    
    # Process patient requests
    await hospital_system.handle_patient_requests(patient_requests)

if __name__ == "__main__":
    asyncio.run(main())