# Simple Travel Planning System - Multi-Agent Orchestration Demo

## 🌟 Overview

A clean, easy-to-understand demo showing three different ways to coordinate multiple AI agents for travel planning:

- **Sequential Pattern**: Agents work one after another
- **Parallel Pattern**: All agents work at the same time  
- **Conditional Pattern**: Only relevant agents are used

## 🎯 What You'll Learn

- How to create multiple specialized AI agents
- Three different orchestration patterns
- When to use each pattern
- Basic multi-agent system design

## 🏗️ System Architecture

### Three Specialist Agents

1. **🗺️ Destination Agent** - Recommends where to go
2. **✈️ Flight Agent** - Finds flight options  
3. **🏨 Accommodation Agent** - Suggests places to stay

### Three Orchestration Patterns

#### 1. Sequential Pattern
Request → Destination Agent → Flight Agent → Accommodation Agent

text
- Each agent completes before next one starts
- Good for step-by-step planning

#### 2. Parallel Pattern  
Request → [All Agents Simultaneously] → Combined Results

text
- All agents work at the same time
- Fastest for getting all recommendations

#### 3. Conditional Pattern
Request → Analysis → [Only Relevant Agents]

text
- Smart selection based on request content
- Efficient use of resources

## 🚀 Quick Start

### 1. Installation
```bash
pip install semantic-kernel==1.36.2 python-dotenv
2. Setup Environment
Create .env file:

env
AZURE_TEXTGENERATOR_DEPLOYMENT_NAME=your-deployment-name
AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_TEXTGENERATOR_DEPLOYMENT_KEY=your-api-key
3. Run the Demo
bash
python simple_travel_demo.py
📊 How It Works
1. System Setup
Loads Azure OpenAI configuration

Creates three specialist agents

Prepares the orchestrator

2. Pattern Execution
Sequential Pattern:
text
1. 🗺️ Destination Expert analyzes request → suggests places
2. ✈️ Flight Expert uses likely destinations → finds flights  
3. 🏨 Accommodation Expert → suggests hotels
Parallel Pattern:
text
[All 3 agents process simultaneously]
→ Destination: finding destinations
→ Flights: researching flights  
→ Accommodation: finding hotels
[Wait for all to finish]
Conditional Pattern:
text
1. 🤖 Analyzes request: "Europe trip, history, medium budget"
2. 🔍 Determines: needs all three agents
3. 🗺️✈️🏨 Calls Destination, Flight, and Accommodation agents
3. Results Display
Each pattern shows:

Which agents were called

Their recommendations

Clear, formatted output

🎪 Demo Output Example
text
🌍 SIMPLIFIED TRAVEL PLANNING DEMO
==================================================

📝 TRAVEL REQUEST: I want to go to Europe for 2 weeks...

🔧 Testing SEQUENTIAL Pattern:
==================================================
🚀 Starting SEQUENTIAL Orchestration
Pattern: Destination → Flights → Accommodation
--------------------------------------------------
1. 🗺️ Consulting Destination Expert...
2. ✈️ Consulting Flight Expert...
3. 🏨 Consulting Accommodation Expert...

🎉 SEQUENTIAL ORCHESTRATION RESULTS
============================================================

🗺️ **Destination Recommendations**

Top 2-3 destinations for your Europe trip...
- Rome, Italy: Rich history, perfect for culture lovers
- Paris, France: Museums, architecture, summer festivals
- Barcelona, Spain: Beach access, Gothic Quarter, Gaudí architecture

Best time: June-August | Budget: Mid-range
----------------------------------------

✈️ **Flight Recommendations**

Best airlines: Delta, Lufthansa, British Airways
Flight duration: 8-10 hours from East Coast
Price range: $800-1200 roundtrip
Booking tips: Book 2-3 months early, be flexible with dates
----------------------------------------
🛠️ Code Structure
Agent Base Class
python
class TravelAgent:
    def __init__(self, name, specialty):
        self.name = name
        self.specialty = specialty
        # Sets up AI connection
    
    async def process_request(self, request):
        # Each agent implements this
Specialist Agents
DestinationAgent: Where to go

FlightAgent: How to get there

AccommodationAgent: Where to stay

Orchestrator Class
python
class TravelOrchestrator:
    def __init__(self):
        self.agents = {}  # Holds all agents
    
    async def sequential_orchestration(self, request):
        # Calls agents one by one
    
    async def parallel_orchestration(self, request):
        # Calls all agents simultaneously
    
    async def conditional_orchestration(self, request):
        # Calls only relevant agents
🏆 Pattern Comparison
Pattern	Best For	Speed	Coordination
Sequential	Complex planning	🐢 Slow	High
Parallel	Quick overview	🐇 Fast	Low
Conditional	Specific requests	🚗 Medium	Smart
💡 When to Use Each Pattern
Use Sequential When:
You need step-by-step planning

Later steps depend on earlier results

Planning complex, multi-stop trips

Use Parallel When:
You want fastest possible response

Agents don't depend on each other

Getting broad overview quickly

Use Conditional When:
Requests are very specific

You want to save resources

Some agents aren't needed