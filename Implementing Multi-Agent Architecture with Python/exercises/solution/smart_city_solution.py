import asyncio
import os
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from dotenv import load_dotenv
load_dotenv("../../../.env")

class Cityworker:
    def __init__(self, name: str, expertise: str):
        self.name = name
        self.expertise = expertise
        self.kernel = Kernel()
        
        self.kernel.add_service(
            AzureChatCompletion(
                service_id="chat_completion",
                deployment_name=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_NAME"],
                endpoint=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_ENDPOINT"],
                api_key=os.environ["AZURE_TEXTGENERATOR_DEPLOYMENT_KEY"]
            )
        )
    
    async def process_request(self, request: str) -> str:
        raise NotImplementedError("Subclasses must implement this method")

class Trafficworker(Cityworker):
    def __init__(self):
        super().__init__("Traffic Manager", "Urban traffic flow and congestion management")
    
    async def process_request(self, request: str) -> str:
        prompt = """
        You are an expert traffic management specialist. Analyze the following traffic situation and provide a comprehensive analysis.

        REQUEST: {{$request}}

        Please provide analysis in this structured format:
        
        🚦 CURRENT CONDITIONS:
        - Describe the current traffic situation
        - Identify affected areas and severity
        
        🔍 ROOT CAUSE ANALYSIS:
        - Identify primary causes of the issue
        - Contributing factors
        
        🚨 IMMEDIATE ACTIONS:
        - Short-term solutions (next 24 hours)
        - Emergency measures if needed
        
        🏗️ LONG-TERM SOLUTIONS:
        - Infrastructure improvements
        - Policy recommendations
        
        📊 IMPACT ASSESSMENT:
        - Expected outcomes of recommendations
        - Cost-benefit analysis
        
        Focus on data-driven, practical solutions that can be implemented in a smart city context.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="traffic_analysis",
            plugin_name="traffic",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"🚦 **Traffic Analysis by {self.name}**\n\n{result}"

class Energyworker(Cityworker):
    def __init__(self):
        super().__init__("Energy Analyst", "City energy consumption and distribution")
    
    async def process_request(self, request: str) -> str:
        prompt = """
        You are an expert energy management specialist. Analyze the following energy situation and provide comprehensive recommendations.

        REQUEST: {{$request}}

        Please provide analysis in this structured format:
        
        ⚡ CURRENT ENERGY PATTERNS:
        - Describe current energy consumption
        - Identify peak usage periods
        
        💡 EFFICIENCY OPPORTUNITIES:
        - Areas for energy savings
        - Technology upgrades available
        
        💰 COST-SAVING MEASURES:
        - Immediate cost reduction strategies
        - Long-term financial benefits
        
        🌱 SUSTAINABILITY IMPROVEMENTS:
        - Renewable energy options
        - Carbon reduction strategies
        
        🗓️ IMPLEMENTATION TIMELINE:
        - Short-term actions (0-3 months)
        - Medium-term projects (3-12 months)
        - Long-term initiatives (1+ years)
        
        Focus on practical, scalable solutions with clear ROI.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="energy_analysis",
            plugin_name="energy",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"⚡ **Energy Analysis by {self.name}**\n\n{result}"

class Safetyworker(Cityworker):
    def __init__(self):
        super().__init__("Safety Officer", "Public safety and emergency response")
    
    async def process_request(self, request: str) -> str:
        prompt = """
        You are an expert public safety specialist. Analyze the following safety situation and provide comprehensive recommendations.

        REQUEST: {{$request}}

        Please provide analysis in this structured format:
        
        🚨 RISK ASSESSMENT:
        - Current safety risks identified
        - Risk level classification (Low/Medium/High/Critical)
        
        ⚠️ IMMEDIATE SAFETY CONCERNS:
        - Urgent issues requiring immediate attention
        - Potential emergency situations
        
        🛡️ PREVENTIVE MEASURES:
        - Proactive safety improvements
        - Crime prevention strategies
        
        🚒 EMERGENCY RESPONSE PLANS:
        - Response protocols for incidents
        - Coordination with emergency services
        
        👥 COMMUNITY SAFETY RECOMMENDATIONS:
        - Public awareness campaigns
        - Community engagement strategies
        - Partnership opportunities
        
        Focus on creating a safe, secure environment for all citizens.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="safety_analysis",
            plugin_name="safety",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"🚨 **Safety Analysis by {self.name}**\n\n{result}"

class EnvironmentWorker(Cityworker):
    def __init__(self):
        super().__init__("Environment Specialist", "Environmental monitoring and sustainability")
    
    async def process_request(self, request: str) -> str:
        prompt = """
        You are an expert environmental specialist. Analyze the following environmental situation and provide comprehensive recommendations.

        REQUEST: {{$request}}

        Please provide analysis in this structured format:
        
        🌍 ENVIRONMENTAL IMPACT ASSESSMENT:
        - Current environmental conditions
        - Key pollutants or concerns identified
        
        🌱 SUSTAINABILITY RECOMMENDATIONS:
        - Green infrastructure solutions
        - Sustainable development practices
        
        🏭 POLLUTION CONTROL MEASURES:
        - Emission reduction strategies
        - Waste management improvements
        
        🌳 GREEN INFRASTRUCTURE SUGGESTIONS:
        - Urban greening initiatives
        - Biodiversity enhancement
        
        📋 COMPLIANCE AND REGULATIONS:
        - Regulatory requirements
        - Compliance strategies
        - Monitoring and reporting
        
        Focus on creating a sustainable, environmentally friendly urban environment.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="environment_analysis",
            plugin_name="environment",
            prompt=prompt
        )
        
        result = await self.kernel.invoke(function, request=request)
        return f"🌍 **Environmental Analysis by {self.name}**\n\n{result}"

class CityCoordinator:
    def __init__(self):
        self.workers = {
            "traffic": Trafficworker(),
            "energy": Energyworker(),
            "safety": Safetyworker(),
            "environment": EnvironmentWorker()
        }
    
    async def coordinate_monitoring(self, monitoring_request: str) -> dict:
        """Coordinate monitoring across all workers"""
        results = {}
        
        tasks = [worker.process_request(monitoring_request) for worker in self.workers.values()]
        worker_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for (worker_name, worker), result in zip(self.workers.items(), worker_results):
            if isinstance(result, Exception):
                results[worker_name] = f"❌ Error: {result}"
            else:
                results[worker_name] = result
        
        return results
    
    async def analyze_relevance(self, request: str) -> dict:
        """Use LLM to determine which workers are most relevant for the request"""
        relevance_prompt = """
        Analyze this smart city monitoring request and determine which specialists are most relevant.

        REQUEST: {{$request}}

        Available specialists:
        - traffic: Traffic flow, congestion, transportation, road infrastructure
        - energy: Power consumption, energy distribution, utilities, sustainability
        - safety: Public safety, emergency response, crime prevention, risk assessment
        - environment: Air quality, pollution, environmental impact, sustainability

        For each specialist, provide:
        - Relevance score (1-10, where 10 is most relevant)
        - Brief reasoning
        - Whether they should be involved (Yes/No)

        Format your response clearly for each specialist.
        """
        
        function = KernelFunctionFromPrompt(
            function_name="relevance_analysis",
            plugin_name="coordinator",
            prompt=relevance_prompt
        )
        
        result = await self.workers["traffic"].kernel.invoke(function, request=request)
        return {"relevance_analysis": str(result)}
    
    async def coordinate_smart_monitoring(self, monitoring_request: str) -> dict:
        """Only use relevant workers based on request analysis"""
        print("🔍 Analyzing request relevance...")
        relevance = await self.analyze_relevance(monitoring_request)
        print(f"Relevance Analysis:\n{relevance['relevance_analysis']}\n")
        
        print("🔄 Invoking relevant workers...")
        # For this demo, we'll still use all workers but in a real scenario
        # you would filter based on the relevance analysis
        results = await self.coordinate_monitoring(monitoring_request)
        
        return results

async def main():
    print("Enhanced Smart City Monitoring System - Solution")
    print("=" * 60)
    print("Featuring: Structured Analysis, Environment Worker & Smart Coordination")
    print()
    
    coordinator = CityCoordinator()
    
    scenarios = [
        "Heavy traffic congestion on Main Street during rush hour with average speeds below 10 mph, leading to increased vehicle emissions",
        "Energy consumption peaks in downtown offices between 2-5 PM, 40% above normal levels, with high HVAC usage reported",
        "Safety concerns in Central Park after dark due to poor lighting and limited security patrols, with multiple incident reports",
        "High air pollution levels reported in industrial district exceeding safety standards, with PM2.5 levels at 150 μg/m³"
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"🎯 Scenario {i}: {scenario}")
        print("-" * 80)
        
        results = await coordinator.coordinate_smart_monitoring(scenario)
        
        for worker_type, analysis in results.items():
            print(f"\n{analysis}")
            print("─" * 60)
        
        print("\n" + "=" * 80)
        print()

if __name__ == "__main__":
    asyncio.run(main())