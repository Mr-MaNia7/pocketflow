from pocketflow import Node
from typing import Dict, List, Any
import yaml
from utils.llm import call_llm

class PlannerNode(Node):
    """Decomposes complex research queries into subtasks."""
    
    def prep(self, shared):
        return shared["query"]
    
    def exec(self, query):
        prompt = f"""
        Break down this research query into specific tasks:
        Query: {query}
        
        Return the tasks in YAML format:
        ```yaml
        tasks:
          - type: web_research
            description: <task description>
            parameters:
              search_terms: [<list of search terms>]
          - type: data_analysis
            description: <task description>
            parameters:
              data_sources: [<list of data sources>]
          - type: code_execution
            description: <task description>
            parameters:
              code_requirements: [<list of requirements>]
        ```
        """
        response = call_llm(prompt)
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()
        return yaml.safe_load(yaml_str)
    
    def post(self, shared, prep_res, exec_res):
        shared["tasks"] = exec_res["tasks"]
        # Set the first task as current
        if exec_res["tasks"]:
            shared["current_task"] = exec_res["tasks"][0]
            shared["remaining_tasks"] = exec_res["tasks"][1:]
        return "default"

class WebResearchNode(Node):
    """Performs web research based on search terms."""
    
    def prep(self, shared):
        return shared["current_task"]
    
    def exec(self, task):
        # Extract search terms based on task type
        if task["type"] == "web_research":
            # Handle web research task
            search_terms = task["parameters"].get("search_terms", [])
            if not search_terms:
                # If no search terms provided, use the task description
                search_terms = [task["description"]]
        else:
            # For other task types, use the task description as search term
            search_terms = [task["description"]]
        
        results = []
        for term in search_terms:
            # TODO: Implement actual web search
            results.append({
                "term": term,
                "results": f"Results for {term}",
                "task_type": task["type"]
            })
        return results
    
    def post(self, shared, prep_res, exec_res):
        # Store results for current task
        if "web_research_results" not in shared:
            shared["web_research_results"] = []
        shared["web_research_results"].append({
            "task": shared["current_task"],
            "results": exec_res
        })
        
        # Move to next task if available
        if shared["remaining_tasks"]:
            shared["current_task"] = shared["remaining_tasks"][0]
            shared["remaining_tasks"] = shared["remaining_tasks"][1:]
            return "default"
        return "next"

class DataAnalysisNode(Node):
    """Analyzes and synthesizes gathered information."""
    
    def prep(self, shared):
        return shared["web_research_results"]
    
    def exec(self, research_results):
        prompt = f"""
        Analyze and synthesize these research results:
        {research_results}
        
        Provide a structured analysis in YAML format:
        ```yaml
        analysis:
          key_findings:
            - <finding 1>
            - <finding 2>
          implications:
            - <implication 1>
            - <implication 2>
          confidence_score: <0-1>
        ```
        """
        response = call_llm(prompt)
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()
        return yaml.safe_load(yaml_str)
    
    def post(self, shared, prep_res, exec_res):
        shared["analysis_results"] = exec_res
        return "default"

class VisualizationNode(Node):
    """Creates visualizations based on analysis results."""
    
    def prep(self, shared):
        return shared["analysis_results"]
    
    def exec(self, analysis):
        # TODO: Implement actual visualization generation
        return {
            "charts": ["chart1.png", "chart2.png"],
            "diagrams": ["diagram1.png"]
        }
    
    def post(self, shared, prep_res, exec_res):
        shared["visualizations"] = exec_res
        return "default"

class ReporterNode(Node):
    """Generates final comprehensive report."""
    
    def prep(self, shared):
        return {
            "analysis": shared["analysis_results"],
            "visualizations": shared["visualizations"]
        }
    
    def exec(self, data):
        prompt = f"""
        Generate a comprehensive research report based on:
        Analysis: {data['analysis']}
        Visualizations: {data['visualizations']}
        
        Format the report in YAML:
        ```yaml
        report:
          executive_summary: |
            <summary>
          detailed_findings:
            - <finding 1>
            - <finding 2>
          recommendations:
            - <recommendation 1>
            - <recommendation 2>
          visualizations:
            - <visualization 1>
            - <visualization 2>
        ```
        """
        response = call_llm(prompt)
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()
        return yaml.safe_load(yaml_str)
    
    def post(self, shared, prep_res, exec_res):
        shared["final_report"] = exec_res
        return "default"

class SupervisorNode(Node):
    """Monitors and validates the overall workflow."""
    
    def prep(self, shared):
        return shared["final_report"]
    
    def exec(self, report):
        prompt = f"""
        Review this research report and determine if it meets quality standards:
        {report}
        
        Return your decision in YAML:
        ```yaml
        decision:
          approved: true/false
          feedback: <feedback if not approved>
          confidence: <0-1>
        ```
        """
        response = call_llm(prompt)
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()
        return yaml.safe_load(yaml_str)
    
    def post(self, shared, prep_res, exec_res):
        if exec_res["decision"]["approved"]:
            return "approved"
        shared["supervisor_feedback"] = exec_res["decision"]["feedback"]
        return "needs_revision"

class CodeExecutorNode(Node):
    """Executes code based on task requirements."""
    
    def prep(self, shared):
        return shared["current_task"]
    
    def exec(self, task):
        if task["type"] != "code_execution":
            return {"error": "Invalid task type for code execution"}
            
        # Extract code requirements from task
        code_requirements = task["parameters"].get("code_requirements", [])
        
        # Generate code based on requirements
        prompt = f"""
        Generate Python code to satisfy these requirements:
        {code_requirements}
        
        Return the code in YAML format:
        ```yaml
        code: |
            <your code here>
        explanation: |
            <explanation of what the code does>
        ```
        """
        response = call_llm(prompt)
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()
        result = yaml.safe_load(yaml_str)
        
        # Execute the generated code in a safe environment
        try:
            # Create a new namespace for execution
            namespace = {}
            exec(result["code"], namespace)
            execution_result = {
                "code": result["code"],
                "explanation": result["explanation"],
                "output": namespace.get("output", "No output generated"),
                "success": True
            }
        except Exception as e:
            execution_result = {
                "code": result["code"],
                "explanation": result["explanation"],
                "error": str(e),
                "success": False
            }
            
        return execution_result
    
    def post(self, shared, prep_res, exec_res):
        # Store execution results
        if "code_execution_results" not in shared:
            shared["code_execution_results"] = []
        shared["code_execution_results"].append({
            "task": shared["current_task"],
            "result": exec_res
        })
        
        # Move to next task if available
        if shared["remaining_tasks"]:
            shared["current_task"] = shared["remaining_tasks"][0]
            shared["remaining_tasks"] = shared["remaining_tasks"][1:]
            return "default"
        return "next" 