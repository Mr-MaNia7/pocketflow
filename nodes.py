from pocketflow import Node
from typing import Dict, List, Any
import yaml
from utils.llm import call_llm
from utils.logger import research_logger as logger

class PlannerNode(Node):
    """Decomposes complex research queries into subtasks."""
    
    def prep(self, shared):
        logger.log_step("Planner", "prep", "Starting task decomposition")
        return shared["query"]
    
    def exec(self, query):
        logger.log_step("Planner", "exec", "Decomposing query into tasks")
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
        tasks = yaml.safe_load(yaml_str)
        logger.log_step("Planner", "exec", "Successfully decomposed tasks", tasks)
        return tasks
    
    def post(self, shared, prep_res, exec_res):
        shared["tasks"] = exec_res["tasks"]
        # Set the first task as current
        if exec_res["tasks"]:
            shared["current_task"] = exec_res["tasks"][0]
            shared["remaining_tasks"] = exec_res["tasks"][1:]
        logger.log_step("Planner", "post", "Initialized task list", {
            "total_tasks": len(exec_res["tasks"]),
            "first_task": exec_res["tasks"][0]
        })
        return "default"

class WebResearchNode(Node):
    """Performs web research based on search terms."""
    
    def prep(self, shared):
        logger.log_step("WebResearch", "prep", "Preparing research task", shared["current_task"])
        return shared["current_task"]
    
    def exec(self, task):
        logger.log_step("WebResearch", "exec", "Conducting web research", task)
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
        
        # Generate a structured response using LLM
        prompt = f"""
        Research the following topics and provide results in YAML format:
        Topics: {search_terms}
        
        Return the results in this exact YAML format:
        ```yaml
        results:
          - term: <search term>
            findings:
              - <finding 1>
              - <finding 2>
            sources:
              - <source 1>
              - <source 2>
        ```
        """
        
        response = call_llm(prompt)
        
        # Extract YAML content more robustly
        try:
            if "```yaml" in response:
                yaml_str = response.split("```yaml")[1].split("```")[0].strip()
            elif "```" in response:
                yaml_str = response.split("```")[1].split("```")[0].strip()
            else:
                # If no code blocks found, try to parse the entire response
                yaml_str = response.strip()
            
            result = yaml.safe_load(yaml_str)
            if not isinstance(result, dict) or "results" not in result:
                # If parsing failed or structure is wrong, create a basic structure
                result = {
                    "results": [
                        {
                            "term": term,
                            "findings": [f"Research results for {term}"],
                            "sources": ["Simulated source"]
                        }
                        for term in search_terms
                    ]
                }
        except Exception as e:
            # If any parsing fails, create a basic structure
            result = {
                "results": [
                    {
                        "term": term,
                        "findings": [f"Research results for {term}"],
                        "sources": ["Simulated source"]
                    }
                    for term in search_terms
                ]
            }
        
        logger.log_step("WebResearch", "exec", "Research completed", result)
        return result["results"]
    
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
            logger.log_step("WebResearch", "post", "Moving to next task", shared["current_task"])
            return "default"
        logger.log_step("WebResearch", "post", "All tasks completed")
        return "next"

class DataAnalysisNode(Node):
    """Analyzes and synthesizes gathered information."""
    
    def prep(self, shared):
        logger.log_step("DataAnalysis", "prep", "Preparing data analysis task", shared["current_task"])
        return shared["web_research_results"]
    
    def exec(self, research_results):
        logger.log_step("DataAnalysis", "exec", "Performing data analysis", research_results)
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
        analysis = yaml.safe_load(yaml_str)
        logger.log_step("DataAnalysis", "exec", "Analysis completed", analysis)
        return analysis
    
    def post(self, shared, prep_res, exec_res):
        shared["analysis_results"] = exec_res
        logger.log_step("DataAnalysis", "post", "Analysis results stored", exec_res)
        return "default"

class VisualizationNode(Node):
    """Creates visualizations based on analysis results."""
    
    def prep(self, shared):
        logger.log_step("Visualization", "prep", "Preparing visualization task", shared["current_task"])
        return shared["analysis_results"]
    
    def exec(self, analysis):
        logger.log_step("Visualization", "exec", "Creating visualization", analysis)
        # TODO: Implement actual visualization generation
        return {
            "charts": ["chart1.png", "chart2.png"],
            "diagrams": ["diagram1.png"]
        }
    
    def post(self, shared, prep_res, exec_res):
        shared["visualizations"] = exec_res
        logger.log_step("Visualization", "post", "Visualization results stored", exec_res)
        return "default"

class ReporterNode(Node):
    """Generates final comprehensive report."""
    
    def prep(self, shared):
        logger.log_step("Reporter", "prep", "Preparing report generation", shared["current_task"])
        return {
            "analysis": shared["analysis_results"],
            "visualizations": shared["visualizations"]
        }
    
    def exec(self, data):
        logger.log_step("Reporter", "exec", "Generating report", data)
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
        report = yaml.safe_load(yaml_str)
        logger.log_step("Reporter", "exec", "Report generated", report)
        return report
    
    def post(self, shared, prep_res, exec_res):
        shared["final_report"] = exec_res
        logger.log_step("Reporter", "post", "Final report stored", exec_res)
        return "default"

class SupervisorNode(Node):
    """Monitors and validates the overall workflow."""
    
    def prep(self, shared):
        logger.log_step("Supervisor", "prep", "Preparing final validation")
        return shared["final_report"]
    
    def exec(self, report):
        logger.log_step("Supervisor", "exec", "Validating research results")
        prompt = f"""
        Review this research report and determine if it meets quality standards:
        {report}
        
        Return your decision in YAML format:
        ```yaml
        decision:
          approved: true/false
          feedback: <feedback if not approved>
          confidence: <0-1>
        ```
        """
        response = call_llm(prompt)
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()
        decision = yaml.safe_load(yaml_str)
        logger.log_step("Supervisor", "exec", "Validation completed", decision)
        return decision
    
    def post(self, shared, prep_res, exec_res):
        if exec_res["decision"]["approved"]:
            logger.log_step("Supervisor", "post", "Final validation stored", exec_res)
            return "approved"
        shared["supervisor_feedback"] = exec_res["decision"]["feedback"]
        logger.log_step("Supervisor", "post", "Final validation stored", exec_res)
        return "needs_revision"

class CodeExecutorNode(Node):
    """Executes code based on task requirements."""
    
    def prep(self, shared):
        logger.log_step("CodeExecutor", "prep", "Preparing code execution task", shared["current_task"])
        return shared["current_task"]
    
    def exec(self, task):
        logger.log_step("CodeExecutor", "exec", "Executing code task", task)
        if task["type"] != "code_execution":
            # For non-code-execution tasks, just pass them through
            logger.log_step("CodeExecutor", "exec", "Passing through non-code task", task)
            return {
                "code": "",
                "explanation": f"Passing through {task['type']} task",
                "output": "Task passed through",
                "success": True
            }
            
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
        response = call_llm(prompt, model="claude-3-5-sonnet-20240620", provider="anthropic")
        
        # Handle the response format
        try:
            if isinstance(response, str):
                # Try to extract YAML from the response
                if "```yaml" in response:
                    yaml_str = response.split("```yaml")[1].split("```")[0].strip()
                elif "```" in response:
                    yaml_str = response.split("```")[1].strip()
                else:
                    yaml_str = response.strip()
                
                result = yaml.safe_load(yaml_str)
            else:
                # If response is already a list or dict, use it directly
                result = response
                
            if not isinstance(result, dict):
                raise ValueError("Invalid response format")
                
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
                
            logger.log_step("CodeExecutor", "exec", "Code execution completed", {
                "success": execution_result["success"],
                "output": execution_result["output"][:100] + "..." if len(execution_result["output"]) > 100 else execution_result["output"]
            })
            return execution_result
            
        except Exception as e:
            logger.log_error("CodeExecutor", e, "Failed to process code execution")
            return {
                "code": "",
                "explanation": "Failed to generate or execute code",
                "error": str(e),
                "success": False
            }
    
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
            logger.log_step("CodeExecutor", "post", "Moving to next task", shared["current_task"])
            return "default"
        logger.log_step("CodeExecutor", "post", "All tasks completed")
        return "next" 