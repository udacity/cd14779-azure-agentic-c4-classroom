# 🏥 Hospital Triage Multi-Agent System - Complete Solution

## 🌟 Overview

This solution **adapts the banking routing demo to healthcare**, demonstrating how intelligent routing patterns transfer across domains. Built with **Semantic Kernel 1.37.0** and **Azure SQL**, it shows AI-powered medical triage with specialized healthcare agents and patient record integration.

**Key Adaptations from Banking Demo:**
- **Three Medical Specialists** (General, Emergency, Pediatric) vs four banking specialists
- **Medical Urgency Levels** (Routine/Urgent/Emergency) vs banking priorities
- **Patient Data Integration** (medical history, conditions) vs transaction data
- **Healthcare Context** (symptoms, diagnoses) vs financial context

---

## 🏗️ System Architecture

![Medical Routing Architecture](architecture_routing.png)

The medical triage architecture demonstrates **domain adaptation of routing**:

- **Medical Routing Agent** analyzes patient symptoms using AI to determine specialist and urgency
- Routes to appropriate **Medical Specialist** (General, Emergency, or Pediatric)
- **PatientDataConnector** provides real-time patient history from Azure SQL
- Specialist agents process requests with enriched medical context
- Responses include personalized care with patient history consideration

**Key Pattern:** Same AI-powered routing architecture as banking demo, but adapted for healthcare domain with medical terminology, urgency classification, and patient data.

---

## 🏗️ Complete System Architecture

### 🔹 Modern Agent Management

* **MedicalAgentManager**
  * Shared kernel instance with Azure OpenAI optimization
  * `InProcessRuntime` for efficient resource management
  * Coordinated multi-agent orchestration
  * Production-grade error handling and monitoring

### 🔹 AI-Powered Medical Triage

* **Intelligent Routing System**
  * Advanced NLP analysis of patient symptoms
  * Specialist assignment with medical reasoning
  * Urgency classification (Routine/Urgent/Emergency)
  * Context-aware routing decisions

### 🔹 Specialized Medical Agents

1. **🩺 General Practitioner** - Routine care, chronic conditions, general health
2. **🚨 Emergency Specialist** - Critical care, severe symptoms, immediate actions
3. **👶 Pediatric Specialist** - Children's health, age-appropriate care, parent guidance

### 🔹 Real-Time Data Integration

* **PatientDataConnector** with Azure SQL Server
  * Live database connections with connection pooling
  * Real-time patient history retrieval
  * Automated consultation logging
  * Comprehensive error handling with fallbacks

---

## ✅ Implemented Features

### Database Integration
- ✅ **Azure SQL Server connectivity** with proper connection management
- ✅ **Patient data loading** from `patients` table with condition parsing
- ✅ **Patient information retrieval** by name with case-insensitive search
- ✅ **Automated visit logging** to `patient_visits` table with timestamps
- ✅ **Error handling** with graceful fallback to simulated data

### Medical Specialist Agents
- ✅ **General Practice Agent** with comprehensive symptom assessment
- ✅ **Emergency Specialist** with urgent care protocols
- ✅ **Pediatric Specialist** with child-specific medical guidance
- ✅ **Routing Agent** with intelligent triage decision-making

### Patient Context Integration
- ✅ **Automatic name extraction** from patient requests
- ✅ **Patient history retrieval** when names are provided
- ✅ **Context-aware consultations** using medical records
- ✅ **Personalized medical advice** based on patient conditions

---

## 🚀 Enhanced Workflow

### Step 1: AI-Powered Request Analysis

```
Patient Request → Routing Agent (Medical AI Analysis) → Specialist + Urgency + Medical Reasoning
```

**Advanced Medical Analysis:**
- Natural language understanding of medical terminology
- Symptom severity assessment and urgency classification
- Multi-factor specialist assignment
- Detailed medical reasoning for routing decisions

### Step 2: Intelligent Dynamic Routing

**Routing Decision → Directs to Optimal Specialist:**

* **General Practitioner** → Routine symptoms, chronic conditions, general health
* **Emergency Specialist** → Critical care, severe pain, injuries, breathing issues
* **Pediatric Specialist** → Children's health, baby/toddler concerns, pediatric conditions

### Step 3: Data-Enhanced Specialist Processing

**Specialist Agent + Azure SQL Data → Personalized Medical Response:**

* Real-time patient history integration
* Condition-specific medical advice
* Contextual treatment recommendations
* Automated consultation logging

---

## 📊 Modern Data Flow

```text
Patient Request (Natural Language)
↓
Routing Agent (Azure OpenAI Medical Analysis)
    ├── Specialist Determination
    ├── Urgency Classification (Routine/Urgent/Emergency)
    └── Medical Reasoning
↓
Specialist Agent + Azure SQL Data Connector
    ├── Real-time Patient History
    ├── Medical Condition Context
    └── Previous Visit Information
↓
Data-Driven Medical Response
    ├── Personalized Treatment Advice
    ├── Urgency-Specific Recommendations
    └── Automated Database Logging
```

---

## 🛠️ Setup Instructions

### 1. Installation with Latest Dependencies

```bash
pip install semantic-kernel==1.37.0 python-dotenv pyodbc
```

### 2. Environment Configuration

Create a `.env` file with your Azure services:

```env
# Azure OpenAI Configuration
AZURE_DEPLOYMENT_NAME=your-deployment-name
AZURE_DEPLOYMENT_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_DEPLOYMENT_KEY=your-api-key

# Azure SQL Database Configuration
AZURE_SQL_CONNECTION_STRING=Driver={ODBC Driver 18 for SQL Server};Server=your-server.database.windows.net;Database=your-database;Uid=your-username;Pwd=your-password;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;
```

### 3. Database Schema Setup

Execute the SQL schema in your Azure SQL database:

```sql
-- Patients table
CREATE TABLE patients (
    patient_id INT PRIMARY KEY,
    name NVARCHAR(100),
    age INT,
    last_visit DATE,
    conditions NVARCHAR(500)
);

-- Patient visits table
CREATE TABLE patient_visits (
    visit_id INT IDENTITY(1,1) PRIMARY KEY,
    patient_name NVARCHAR(100),
    symptoms NVARCHAR(1000),
    diagnosis NVARCHAR(500),
    visit_date DATETIME DEFAULT GETDATE()
);

-- Sample patient data
INSERT INTO patients (patient_id, name, age, last_visit, conditions) VALUES
(1, 'John Smith', 45, '2024-01-10', 'hypertension'),
(2, 'Maria Garcia', 32, '2024-01-15', 'asthma'),
(3, 'David Chen', 68, '2024-01-08', 'diabetes,arthritis'),
(4, 'Sarah Johnson', 28, '2023-12-20', '');
```

### 4. Run the Complete System

```bash
python medical_triage_system.py
```

---

## 🎯 Demo Scenarios

### **General Health Cases**
* "I have a mild cough and runny nose for 3 days"
* "Persistent headache for 2 weeks that won't go away"
* "My name is John Smith and I have a sore throat"

### **Emergency Situations**
* "Severe chest pain and difficulty breathing started 30 minutes ago"
* "Cut my finger while cooking and it's bleeding a lot"
* "I fell and hurt my wrist, there's swelling and pain"

### **Pediatric Cases**
* "My child has a fever of 102°F and is very sleepy"
* "My 2-year-old has diarrhea and vomiting since yesterday"

---

## 🔧 Advanced Features

### Modern Semantic Kernel 1.37.0
* **ChatCompletionAgent Framework**: Latest agent patterns with medical instructions
* **Shared Kernel Architecture**: Single Azure OpenAI instance for all agents
* **InProcessRuntime Management**: Proper lifecycle and resource handling
* **Async/Await Optimization**: Concurrent medical request processing

### Intelligent Medical Routing
* **Content-Based Medical Analysis**: Advanced NLP for medical terminology
* **Multi-Factor Urgency Detection**: Context-aware priority classification
* **Reasoning-Based Decisions**: Transparent medical routing logic
* **Dynamic Specialist Matching**: Optimal agent selection based on medical expertise

### Real-Time Data Integration
* **Azure SQL Live Connection**: Real-time patient data access
* **Automatic Patient Context**: Current medical status and history
* **Consultation Logging**: Comprehensive audit trail of all interactions
* **Database Operation Monitoring**: Error tracking and fallback mechanisms

### Production-Ready Architecture
* **Comprehensive Error Handling**: Graceful degradation for all components
* **Resource Optimization**: Shared connections and efficient memory usage
* **Scalable Agent Framework**: Easy addition of new medical specialists
* **Professional Logging**: Detailed progress tracking and decision visibility

---

## 📋 Sample Output

```text
🏥 MEDICAL TRIAGE MULTI-AGENT SYSTEM
Intelligent Routing and Patient Care with Azure SQL
Semantic Kernel 1.37.0 with Modern Agent Framework
======================================================================

📥 Patient Request: My name is John Smith and I have a sore throat
🔄 Analyzing symptoms and determining routing...
✅ Triage Decision:
   Specialist: general
   Urgency: Routine
   Reasoning: Sore throat is a common symptom best handled by general practice

🔧 Connecting to general specialist...

🎯 MEDICAL TRIAGE COMPLETE
Handled by: General Specialist
Urgency: Routine
======================================================================
🏥 **General Care**

Based on your symptoms and patient history, here's my assessment:

🩺 SYMPTOM ASSESSMENT:
- Likely causes: Viral infection, strep throat, or allergies
- Severity: Mild to moderate

💊 INITIAL CARE RECOMMENDATIONS:
- Gargle with warm salt water
- Stay hydrated with warm fluids
- Use throat lozenges for temporary relief

🚨 WHEN TO SEEK URGENT CARE:
- Difficulty breathing or swallowing
- Fever over 101°F lasting more than 2 days
- Severe pain that prevents eating or drinking

Patient Context: Patient: John Smith, Age: 45, Conditions: hypertension, Last Visit: 2024-01-10
======================================================================
```

---

## 🎪 Medical Routing Logic

### AI-Powered Content Analysis

| Symptom Pattern | Specialist | AI Detection Keywords | Data Integration |
|-----------------|------------|----------------------|------------------|
| Routine Symptoms | General Practitioner | "cough", "cold", "headache", "sore throat", "fatigue" | Patient history & conditions |
| Emergency Signs | Emergency Specialist | "chest pain", "difficulty breathing", "severe", "bleeding", "unconscious" | Emergency protocols & immediate actions |
| Pediatric Issues | Pediatric Specialist | "child", "baby", "toddler", "pediatric", "my son", "my daughter" | Age-appropriate care guidelines |

### Sophisticated Urgency Classification

* **🟢 Routine**: Non-urgent symptoms, routine follow-ups, general health questions
* **🟡 Urgent**: Needs medical attention within 24 hours, moderate symptoms
* **🔴 Emergency**: Life-threatening, severe symptoms requiring immediate care

### Context-Aware Data Enhancement

* **General Requests**: Patient history + condition context
* **Emergency Cases**: Immediate action protocols + urgency context
* **Pediatric Consultations**: Age-specific guidance + parent education

---

## 🔄 Extension Opportunities

### Additional Medical Specialists
* **🫀 Cardiology Specialist**: Heart conditions, chest pain evaluation
* **🧠 Neurology Specialist**: Headaches, neurological symptoms
* **🦴 Orthopedics Specialist**: Bone and joint injuries
* **👁️ Ophthalmology Specialist**: Eye-related concerns

### Advanced Integration Features
* **Symptom Checker API**: Integration with medical symptom databases
* **Drug Interaction Checker**: Medication safety verification
* **Telehealth Integration**: Video consultation capabilities
* **Medical Imaging Analysis**: AI-assisted diagnostic support

### Enterprise Enhancements
* **Multi-hospital Architecture**: Support for multiple medical facilities
* **HIPAA Compliance**: Enhanced security and privacy measures
* **Performance Analytics**: Agent performance and routing efficiency metrics
* **Disaster Recovery**: High availability and backup systems

---

## 🚀 Performance Benefits

### Modern Architecture Advantages
* **Real-time Response**: Shared kernel and optimized async processing
* **Data Accuracy**: Live Azure SQL integration ensures current patient information
* **Scalable Management**: Easy addition of new medical specialists
* **Production Reliability**: Comprehensive error handling and graceful degradation

### Medical Value
* **Improved Patient Care**: Accurate, data-driven medical responses
* **Reduced Triage Time**: AI-powered routing eliminates manual assessment
* **Enhanced Safety**: Immediate emergency detection and response
* **Operational Efficiency**: Automated routine inquiries free medical staff for complex cases

---

## ✅ Successfully Implemented

* 🏥 **Complete Medical Triage System** with AI-powered routing
* 🗃️ **Azure SQL Database Integration** with real-time patient data
* 🤖 **Three Specialized Medical Agents** with domain expertise
* 🔄 **Intelligent Request Routing** with urgency classification
* 📊 **Automated Consultation Logging** and patient history
* 🛡️ **Production-Ready Architecture** with comprehensive error handling

---
