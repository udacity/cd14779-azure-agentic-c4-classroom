# 🏦 Bank Office Multi-Agent Routing System

## 🌟 Overview

This demo showcases an **intelligent routing system** for a bank office that automatically directs customer requests to the most appropriate **specialist agent** based on **content analysis** and **urgency detection**.

---

## 🏗️ System Architecture

### 🔹 Intelligent Router

* **RoutingAgent**

  * Analyzes customer requests
  * Determines:

    * Which specialist should handle the request
    * Urgency level (Low, Medium, High, Emergency)
    * Reasoning for routing decision

### 🔹 Specialist Agents

1. **🏦 Account Agent** — Balance checks, transactions, account info
2. **💰 Loan Agent** — Loan applications and inquiries
3. **💳 Card Agent** — Credit/debit card services
4. **🚨 Emergency Agent** — Urgent banking issues

### 🔹 Data Integration

* **BankDataConnector**

  * Simulated Azure SQL Server connection
  * Provides transaction data and account information
  * In real-world use, connects to **Azure SQL Database**

---

## 🚀 How It Works

### Step 1: Request Analysis

Customer Request → **Routing Agent** analyzes:

* Request content (account, loan, card, emergency)
* Urgency level
* Appropriate specialist

---

### Step 2: Intelligent Routing

Routing decision → Directs to the appropriate agent:

* **Account Specialist** → balance inquiries
* **Loan Specialist** → loan applications
* **Card Specialist** → card issues
* **Emergency Specialist** → urgent matters

---

### Step 3: Specialist Processing

Specialist Agent → Provides:

* Domain-specific assistance
* Data-informed responses
* Actionable next steps

---

## 📊 Data Flow

```text
Customer Request
↓
Routing Agent (AI Analysis)
↓
Routing Decision + Urgency
↓
Specialist Agent + Data Connector
↓
Personalized Response
```

---

## 🛠️ Setup Instructions

### 1. Installation

```bash
pip install semantic-kernel==1.36.2 python-dotenv
```

### 2. Environment Configuration

Create a `.env` file with Azure OpenAI credentials:

```env
AZURE_TEXTGENERATOR_DEPLOYMENT_NAME=your-deployment-name
AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_TEXTGENERATOR_DEPLOYMENT_KEY=your-api-key
```

### 3. Run the Demo

```bash
python bank_routing_demo.py
```

---

## 🎯 Demo Scenarios

The system can handle various customer requests:

**Account Inquiries**

* "I want to check my account balance"
* "Show me recent transactions"
* "What's my current account status?"

**Loan Services**

* "I want to apply for a home loan"
* "What are personal loan requirements?"
* "Current mortgage interest rates?"

**Card Services**

* "My card was lost/stolen"
* "I need a new debit card"
* "Card transaction issues"

**Emergency Situations**

* "Fraudulent transactions detected"
* "Urgent account security issues"
* "Immediate card cancellation"

---

## 🔧 Key Features

### Intelligent Routing

* **Content-based**: Analyzes request topics
* **Priority-based**: Detects urgency levels
* **AI-powered**: Uses OpenAI for smart routing decisions

### Data Integration

* **Simulated SQL Database** with transaction records
* **Account balance calculations** in real-time
* **Transaction history** retrieval

### Specialist Expertise

* Each agent has domain-specific knowledge
* Tailored responses for different request types
* Handles urgency appropriately

---

## 📋 Sample Output

```text
🏦 BANK OFFICE MULTI-AGENT SYSTEM
============================================================

############################################################
CUSTOMER REQUEST #1
############################################################
📥 Customer Request: I want to check my account balance and recent transactions
🔄 Analyzing request and determining routing...
✅ Routing Decision:
   Specialist: Account
   Urgency: Low
   Reasoning: Customer is asking about account balance and transactions

🔧 Connecting to Account Specialist...

🎯 REQUEST PROCESSING COMPLETE
Handled by: Account Specialist
Urgency: Low
==================================================
🏦 Account Assistance

I can help you check your account balance and review recent transactions.

Based on your account ACC001:
- Current Balance: $649.50
- Recent Transactions:
  * Jan 15: Deposit $1000.00 ✅
  * Jan 16: Withdrawal $250.50 ✅
  * Jan 18: Transfer $100.00 ⏳

Would you like more details about any specific transaction?
==================================================
```

---

## 🎪 Routing Logic

### Content-Based Routing Rules

| Request Type   | Specialist      | Examples                                 |
| -------------- | --------------- | ---------------------------------------- |
| Account Info   | Account Agent   | "balance", "transactions", "account"     |
| Loan Services  | Loan Agent      | "loan", "mortgage", "interest rate"      |
| Card Issues    | Card Agent      | "card", "debit", "credit", "stolen"      |
| Urgent Matters | Emergency Agent | "fraud", "stolen", "emergency", "urgent" |

### Urgency Detection

* **Low**: General information requests
* **Medium**: Service applications, status checks
* **High**: Payment issues, time-sensitive matters
* **Emergency**: Security breaches, fraud, lost cards

---
