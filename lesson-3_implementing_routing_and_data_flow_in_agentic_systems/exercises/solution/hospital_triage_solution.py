import asyncio
import os
import pyodbc
from contextlib import contextmanager
from typing import Dict, List, Optional
from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
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
    
    @contextmanager
    def get_db_connection(self):
        """Database connection helper for Azure SQL Server"""
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

class MedicalAgentManager:
    """Complete medical triage system with intelligent routing and Azure SQL integration"""
    
    def __init__(self):
        # Shared kernel instance for optimal resource usage
        self.kernel = Kernel()
        
        # Azure OpenAI service configuration
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="azure_medical_chat",
                deployment_name=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
            )
        )
        
        # Initialize data connector with Azure SQL connection
        self.data_connector = PatientDataConnector()
        
        # Initialize specialized medical agents with detailed instructions
        self.agents = {
            "general": ChatCompletionAgent(
                kernel=self.kernel,
                name="General_Practitioner",
                description="Specialist in general health and routine care",
                instructions="""You are a general practitioner. Help patients with general health concerns.

                Always provide:
                - Professional symptom assessment and likely causes
                - Initial care recommendations and home remedies
                - Clear guidance on when to seek urgent care
                - Follow-up instructions and monitoring advice
                - Referral suggestions if specialist care is needed

                Use patient data from the database when available to provide personalized responses.
                Be empathetic, professional, and focus on patient safety."""
            ),
            "emergency": ChatCompletionAgent(
                kernel=self.kernel,
                name="Emergency_Specialist",
                description="Specialist in urgent and critical care situations",
                instructions="""You are an emergency medicine specialist. Handle urgent medical situations immediately.

                This is HIGH PRIORITY. Always provide:
                - Immediate action steps and first aid instructions
                - Clear emergency warning signs and red flags
                - Guidance on when to call emergency services
                - Urgent care facility recommendations
                - Critical monitoring instructions while waiting for help

                Respond with URGENCY and prioritize patient safety above all else.
                Focus on life-threatening conditions and immediate risks."""
            ),
            "pediatric": ChatCompletionAgent(
                kernel=self.kernel,
                name="Pediatric_Specialist",
                description="Specialist in children's health and development",
                instructions="""You are a pediatric specialist. Handle children's health concerns with age-appropriate care.

                Always provide:
                - Age-specific symptom assessment and considerations
                - Pediatric-appropriate care recommendations
                - Child-specific emergency warning signs
                - Growth and development context
                - Parent guidance and monitoring instructions

                Focus on child safety, developmental stages, and parent education."""
            ),
            "router": ChatCompletionAgent(
                kernel=self.kernel,
                name="Medical_Routing_Agent",
                description="Intelligent router for medical request distribution",
                instructions="""You are an intelligent medical routing agent. Analyze patient requests and route to appropriate specialists.

                Analyze each request and determine:
                1. Which specialist should handle it (general/emergency/pediatric)
                2. The urgency level (Routine/Urgent/Emergency)
                3. Brief medical reasoning for your decision

                Specialist Responsibilities:
                - general: Routine symptoms, chronic conditions, general health questions
                - emergency: Severe pain, injuries, breathing difficulties, chest pain, heavy bleeding
                - pediatric: Children's health issues, baby/toddler concerns, pediatric-specific conditions

                Urgency Guidelines:
                - Routine: Non-urgent symptoms, routine follow-ups, general health questions
                - Urgent: Needs medical attention within 24 hours, moderate symptoms
                - Emergency: Life-threatening, severe symptoms requiring immediate care

                Respond in this exact format:
                Specialist: [general/emergency/pediatric]
                Urgency: [Routine/Urgent/Emergency]
                Reasoning: [brief medical explanation]"""
            )
        }
        
        self.runtime = InProcessRuntime()

    async def route_patient_request(self, patient_request: str) -> dict:
        """Intelligent routing of patient requests to appropriate specialists"""
        print(f"📥 Patient Request: {patient_request}")
        print("🔄 Analyzing symptoms and determining routing...")
        
        # Use routing agent to analyze the request
        routing_prompt = f"PATIENT REQUEST: {patient_request}"
        
        routing_response = await self.agents["router"].get_response(routing_prompt)
        routing_content = str(routing_response.content)
        
        # Parse routing decision
        routing_decision = self._parse_routing_decision(routing_content)
        
        print(f"✅ Triage Decision:")
        print(f"   Specialist: {routing_decision['specialist']}")
        print(f"   Urgency: {routing_decision['urgency']}")
        print(f"   Reasoning: {routing_decision['reasoning']}")
        
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

    async def process_with_specialist(self, patient_request: str, specialist: str, urgency: str) -> str:
        """Process patient request with the appropriate specialist"""
        print(f"🔧 Connecting to {specialist} specialist...")
        
        # Try to extract patient name and get history using simple pattern matching
        patient_context = ""
        if "my name is" in patient_request.lower():
            try:
                name_part = patient_request.lower().split("my name is")[1].split(".")[0].strip()
                patient_name = name_part.title()
                patient_history = self.data_connector.get_patient_history(patient_name)
                patient_context = f"\n\nPATIENT CONTEXT: {patient_history}"
            except (IndexError, AttributeError):
                pass
        
        # Add urgency context for emergency situations
        urgency_context = ""
        if urgency in ["Urgent", "Emergency"]:
            urgency_context = f"\n\n🚨 URGENCY: {urgency} - Requiring immediate attention"
        
        # Process request with specialist agent
        full_request = f"PATIENT REQUEST: {patient_request}{patient_context}{urgency_context}"
        
        if specialist in self.agents:
            specialist_response = await self.agents[specialist].get_response(full_request)
            
            # Log the consultation in database
            patient_name = "Unknown Patient"
            if "my name is" in patient_request.lower():
                try:
                    name_part = patient_request.lower().split("my name is")[1].split(".")[0].strip()
                    patient_name = name_part.title()
                except (IndexError, AttributeError):
                    pass
            
            diagnosis = f"{specialist.capitalize()} Consultation - {urgency} Priority"
            self.data_connector.add_patient_visit(patient_name, patient_request, diagnosis)
            
            return f"🏥 **{specialist.capitalize()} Care**\n\n{specialist_response.content}"
        else:
            return f"❌ Specialist '{specialist}' not available for this request."

    async def handle_patient_request(self, patient_request: str) -> dict:
        """Complete processing of a patient request"""
        # Step 1: Route the request
        routing_decision = await self.route_patient_request(patient_request)
        
        # Step 2: Process with appropriate specialist
        if routing_decision["specialist"] in self.agents:
            specialist_response = await self.process_with_specialist(
                patient_request, 
                routing_decision["specialist"],
                routing_decision["urgency"]
            )
            
            return {
                "routing_decision": routing_decision,
                "specialist_response": specialist_response,
                "specialist_name": routing_decision["specialist"].capitalize() + " Specialist"
            }
        else:
            return {
                "routing_decision": routing_decision,
                "specialist_response": "❌ No suitable specialist found for this medical case.",
                "specialist_name": "Unknown"
            }

    def display_result(self, result: dict):
        """Display the processing result"""
        print(f"\n🎯 MEDICAL TRIAGE COMPLETE")
        print(f"Handled by: {result['specialist_name']}")
        print(f"Urgency: {result['routing_decision']['urgency']}")
        print("\n" + "=" * 60)
        print(f"{result['specialist_response']}")
        print("=" * 60)

async def main():
    """Main medical triage system demo"""
    print("🏥 MEDICAL TRIAGE MULTI-AGENT SYSTEM")
    print("Intelligent Routing and Patient Care with Azure SQL")
    print("Semantic Kernel 1.37.0 with Modern Agent Framework")
    print("=" * 70)
    
    # Validate environment setup
    required_vars = [
        "AZURE_TEXTGENERATOR_DEPLOYMENT_NAME",
        "AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT", 
        "AZURE_TEXTGENERATOR_DEPLOYMENT_KEY",
        "AZURE_SQL_CONNECTION_STRING"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please check your .env file")
        return
    
    manager = MedicalAgentManager()
    
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
    
    # Sample patient requests covering different scenarios
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
    for i, patient_request in enumerate(patient_requests[:6], 1):
        print(f"\n{'#' * 70}")
        print(f"PATIENT REQUEST #{i}")
        print(f"{'#' * 70}")
        
        try:
            result = await manager.handle_patient_request(patient_request)
            manager.display_result(result)
            
            # Brief pause between requests
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ Error processing request: {e}")
            continue
    
    print("\n✅ Medical triage system demo completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())