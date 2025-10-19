# 🏥 Hospital Triage System - Multi-Agent Routing Exercise

## 🎯 Exercise Overview

Transform this starter code into a complete **hospital triage system with Azure SQL Server integration**!
You’ll implement intelligent routing that directs patient requests to the appropriate medical specialists and integrates with a real database.

---

## 📋 Exercise Tasks

### Task 1: Azure SQL Database Integration

**File: `hospital_triage_starter.py`**

#### 1.1 Complete `PatientDataConnector`

* Implement `_load_patient_data()` to query Azure SQL database
* Implement `get_patient_info()` with actual SQL queries
* Implement `add_patient_visit()` to insert new patient records

#### 1.2 Initialize Data Connector in Agents

* Uncomment and initialize `self.data_connector` in **MedicalAgent base class**
* Ensure all agents can access patient data

---

### Task 2: Improve Existing Agents

**File: `hospital_triage_starter.py`**

#### 2.1 Enhance `GeneralPracticeAgent` Prompt

Include patient history from the database and provide:

* Assessment of general symptoms
* Initial care recommendations
* Urgency assessment
* Follow-up instructions

#### 2.2 Enhance `EmergencyAgent` Prompt

Provide:

* Immediate action steps
* Emergency warning signs
* First aid guidance (if applicable)
* Urgency assessment

---

### Task 3: Implement `PediatricAgent`

**File: `hospital_triage_starter.py`**

* Handles children’s health issues
* Integrates with patient database
* Provides **age-appropriate** medical advice

---

### Task 4: Complete `TriageRouter`

**File: `hospital_triage_starter.py`**

#### 4.1 Add `PediatricAgent` to Router

Register it in the `specialists` dictionary.

#### 4.2 Implement Routing Prompt

Create a comprehensive **medical triage routing prompt**.

#### 4.3 Implement Routing Parser

Complete the `_parse_routing_decision` method.

---

### Task 5: Test Database Connection

**File: `hospital_triage_starter.py`**

* Uncomment and implement DB connection testing in `handle_patient_requests`.

---

## 🛠️ Setup Instructions

### 1. Install Dependencies

```bash
pip install semantic-kernel==1.36.2 python-dotenv pyodbc
```

### 2. Environment Configuration

Create a `.env` file with your credentials:

```env
AZURE_TEXTGENERATOR_DEPLOYMENT_NAME=your-deployment-name
AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_TEXTGENERATOR_DEPLOYMENT_KEY=your-api-key
AZURE_SQL_CONNECTION_STRING=Driver={ODBC Driver 18 for SQL Server};Server=your-server.database.windows.net;Database=your-database;Uid=your-username;Pwd=your-password;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;
```

### 3. Database Schema Setup

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

-- Sample data
INSERT INTO patients (patient_id, name, age, last_visit, conditions) VALUES
(1, 'John Smith', 45, '2024-01-10', 'hypertension'),
(2, 'Maria Garcia', 32, '2024-01-15', 'asthma'),
(3, 'David Chen', 68, '2024-01-08', 'diabetes,arthritis'),
(4, 'Sarah Johnson', 28, '2023-12-20', '');
```

### 4. Run Starter Code

```bash
python hospital_triage_starter.py
```

---

## 💡 Implementation Hints

### For Database Integration

```python
def _load_patient_data(self) -> List[Dict]:
    with self.get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT patient_id, name, age, last_visit, conditions FROM patients")
        # Process rows and return formatted data
```

### For Patient Name Extraction

```python
if "my name is" in request.lower():
    name = request.lower().split("my name is")[1].split(".")[0].strip()
    patient_history = self.data_connector.get_patient_history(name)
```

### For Error Handling

* Always wrap DB operations in **try/except**
* Provide fallback to simulated data if DB fails
* Log errors for debugging

---

## 🧪 Testing Your Solution

After completing all tasks, your system should:

* ✅ Connect to Azure SQL Database and load patient data
* ✅ Route patients correctly to appropriate specialists
* ✅ Use patient history from DB in consultations
* ✅ Log new patient visits into the DB
* ✅ Handle all sample requests without errors

---

## 📊 Expected Database Operations

* `SELECT` queries → fetch patient info
* `INSERT` queries → log new patient visits
* Error handling for DB connection issues
* Parsing of patient conditions/history

---

## 🎯 Success Criteria

Your solution is complete when:

* ✅ Azure SQL Database connection works
* ✅ Patient data loads from DB
* ✅ All three agents (General, Emergency, Pediatric) provide advice
* ✅ Routing uses patient history effectively
* ✅ New visits are logged to DB
* ✅ System handles DB errors gracefully

---

## 🆘 Need Help?

* Check the **solution code** for DB integration examples
* Test DB connection separately
* Use simple SQL queries first
* Check **Azure SQL firewall settings**

---

🚑 Good luck building your hospital triage system!
