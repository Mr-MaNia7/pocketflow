from pocketflow import Node
from typing import Dict, List, Any
import yaml
from utils.llm import call_llm
from utils.logger import research_logger as logger
from utils.web_search import search_web_firecrawl
from utils.code_executor import execute_and_upload

class PlannerNode(Node):
    """Decomposes complex research queries into subtasks."""
    
    def prep(self, shared):
        return shared["query"]
    
    def exec(self, query):
        logger.log_step("Planner", "exec", "Decomposing query into tasks")
        prompt = f"""
        Break down this research query into specific tasks. Return ONLY the YAML structure below, replacing the placeholders with actual values:

        Query: {query}

        ```yaml
        tasks:
          - type: web_research
            description: <specific research task>
            parameters:
              search_terms:
                - <specific search term 1>
                - <specific search term 2>
          - type: data_analysis
            description: <specific analysis task>
            parameters:
              data_sources:
                - <specific data source 1>
                - <specific data source 2>
          - type: code_execution
            description: <specific code task>
            parameters:
              code_requirements:
                - <specific requirement 1>
                - <specific requirement 2>
        ```

        Rules:
        1. Return ONLY the YAML structure above, nothing else
        2. Replace ALL placeholders with specific values
        3. Keep the exact same indentation (2 spaces)
        4. Each task must have all fields (type, description, parameters)
        5. Each parameters field must have its required list (search_terms, data_sources, or code_requirements)
        """
        response = call_llm(prompt)
        
        try:
            # Extract YAML from response
            yaml_str = response.split("```yaml")[1].split("```")[0].strip()
            tasks = yaml.safe_load(yaml_str)
            
            # Basic validation
            if not isinstance(tasks, dict) or "tasks" not in tasks:
                raise ValueError("Invalid YAML structure: missing 'tasks' key")
            if not isinstance(tasks["tasks"], list):
                raise ValueError("Invalid YAML structure: 'tasks' must be a list")
            
            # Validate each task
            for task in tasks["tasks"]:
                if not isinstance(task, dict):
                    raise ValueError("Each task must be a dictionary")
                if "type" not in task or "description" not in task or "parameters" not in task:
                    raise ValueError("Each task must have type, description, and parameters")
                if task["type"] not in ["web_research", "data_analysis", "code_execution"]:
                    raise ValueError(f"Invalid task type: {task['type']}")
            
            logger.log_step("Planner", "exec", "Successfully decomposed tasks", tasks)
            return tasks
            
        except Exception as e:
            logger.log_step("Planner", "exec", f"Error parsing YAML: {str(e)}", {
                "response": response,
                "error": str(e)
            })
            raise
    
    def post(self, shared, prep_res, exec_res):
        shared["tasks"] = exec_res["tasks"]
        shared["current_task"] = exec_res["tasks"][0]
        shared["remaining_tasks"] = exec_res["tasks"][1:]
        return "default"

class WebResearchNode(Node):
    """Performs web research based on search terms using Firecrawl API."""
    
    def prep(self, shared):
        return shared["current_task"]
    
    def exec(self, task):
        if task["type"] != "web_research":
            logger.log_step("WebResearch", "exec", "Skipping non-web-research task", {
                "task_type": task["type"]
            })
            return {
                "status": "skipped",
                "reason": f"Task type {task['type']} is not a web research task"
            }
            
        search_terms = task["parameters"].get("search_terms", [])
        if not search_terms:
            search_terms = [task["description"]]
        
        all_results = []
        for term in search_terms[:1]:  # Limit to one search term for now
            try:
                search_results = search_web_firecrawl(term, max_results=1)
                all_results.append({
                    "term": term,
                    "findings": [search_results[0]['data']],
                    "sources": ["Firecrawl Search"],
                    "status": "success"
                })
            except Exception as e:
                logger.log_step("WebResearch", "exec", f"Error searching for term {term}", str(e))
                all_results.append({
                    "term": term,
                    "findings": [f"Error during search: {str(e)}"],
                    "sources": ["Error"],
                    "status": "error"
                })
        
        logger.log_step("WebResearch", "exec", "Research completed", all_results[0]['findings'][0][:300])
        
        return {
            "status": "success",
            "results": all_results
        }
    
    def post(self, shared, prep_res, exec_res):
        if "web_research_results" not in shared:
            shared["web_research_results"] = []
        shared["web_research_results"].append({
            "task": shared["current_task"],
            "result": exec_res
        })
        return "default"

class DataAnalysisNode(Node):
    """Analyzes and synthesizes gathered information, performing ETL and preparing data for visualization."""
    
    def prep(self, shared):
        return shared["web_research_results"]
    
    def exec(self, research_results):
        # First, extract and structure the data
        prompt = f"""
        Analyze these research results and extract structured data. Return the following YAML with both qualitative and quantitative analysis (if possible):

        Research Results: {research_results}

        ```yaml
        analysis:
          key_findings:
            - <finding 1>
            - <finding 2>
          implications:
            - <implication 1>
            - <implication 2>
          
          metrics:
            - name: <metric name>
              value: <numeric value>
              unit: <unit of measurement>
              source: <where this metric came from>
              confidence: <0-1>
          
          categories:
            - name: <category name>
              items:
                - name: <item name>
                  count: <number of occurrences>
                  percentage: <percentage of total>
          
          time_series:
            - year: <year>
              metrics:
                - name: <metric name>
                  value: <value>
          
          relationships:
            - from: <entity 1>
              to: <entity 2>
              type: <relationship type>
              strength: <0-1>
          
          data_quality:
            completeness: <0-1>
            reliability: <0-1>
            sources_used: <number>
          
          visualizations:
            - type: <chart type>
              data_source: <which data to use>
              purpose: <what it shows>
              priority: <1-5>
          
          next_steps:
            - <suggested next step 1>
            - <suggested next step 2>
        ```

        Rules:
        1. `analysis` is required while the rest of the fields are optional.
        2. Extract ALL possible numerical and/or qualitative data from the research
        3. Create categories where patterns emerge
        4. Identify time-based trends if present
        5. Note relationships between entities
        6. Assess data quality
        7. Recommend appropriate visualizations
        8. Only include sections where data is available
        9. Use consistent units and formats
        10. Strictly follow the provided YAML structure
        11. Do not add any additional text or explanations outside the YAML
        """
        response = call_llm(prompt, model="gemini-1.5-flash", provider="google")
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()
        analysis = yaml.safe_load(yaml_str)
        
        # Validate the analysis structure
        if not isinstance(analysis, dict) or "analysis" not in analysis:
            raise ValueError("Invalid analysis structure: missing 'analysis' key")
        
        analysis = analysis["analysis"]
        
        # Ensure we have at least some form of analysis
        if not any(key in analysis for key in ["key_findings", "metrics", "categories", "time_series"]):
            raise ValueError("Analysis must contain at least one of: key_findings, metrics, categories, or time_series")
        
        # Log the analysis results
        logger.log_step("DataAnalysis", "exec", "Analysis completed", {
            "metrics_count": len(analysis.get("metrics", [])),
            "categories_count": len(analysis.get("categories", [])),
            "time_series_count": len(analysis.get("time_series", [])),
            "visualizations_count": len(analysis.get("visualizations", []))
        })
        
        return analysis
    
    def post(self, shared, prep_res, exec_res):
        shared["analysis_results"] = exec_res
        return "default"

class CodeExecutorNode(Node):
    """Executes code based on task requirements."""
    
    def prep(self, shared):
        return shared["current_task"], shared.get("analysis_results", {})
    
    def exec(self, inputs):
        task, analysis = inputs
        if task["type"] != "code_execution":
            return {
                "status": "skipped",
                "reason": f"Task type {task['type']} is not a code execution task"
            }
            
        code_requirements = task["parameters"].get("code_requirements", [])
        
        prompt = f"""
        Generate Python code to satisfy these requirements:
        Requirements: {code_requirements}
        Context from analysis: {analysis}
        
        You MUST return ONLY the following YAML structure, with no additional text or explanations:
        ```yaml
        code: |
            # Your Python code here
            # Must be valid Python code
            # Must include proper imports
            # Must save ALL visualizations to temp_dir using plt.savefig()
            # Example: plt.savefig(os.path.join(temp_dir, 'visualization.png'))
            # Must set 'output' variable with the result
        explanation: |
            Brief explanation of what the code does
        visualization_type: |
            Type of visualization if applicable, or 'none'
        ```
        
        Rules:
        1. Return ONLY the YAML structure above
        2. Do not add any text before or after the YAML
        3. The code must be valid Python code
        4. The code must save ALL visualizations to temp_dir using plt.savefig()
        5. The code must set an 'output' variable
        6. Keep the exact same indentation (2 spaces)
        7. Do not modify the structure or add/remove fields
        """
        response = call_llm(prompt, model="claude-3-5-sonnet-20240620", provider="anthropic")
        
        try:
            # Handle response based on its type
            if isinstance(response, list):
                # Extract text from TextBlock objects
                response = "\n".join(item.text if hasattr(item, 'text') else str(item) for item in response)
            
            # Extract YAML from response
            if "```yaml" in response:
                yaml_str = response.split("```yaml")[1].split("```")[0].strip()
            else:
                yaml_str = response.strip()
            
            # Clean up the YAML string
            yaml_str = yaml_str.replace("\\n", "\n")  # Replace escaped newlines
            yaml_str = yaml_str.replace("\\", "")     # Remove any remaining backslashes
            
            result = yaml.safe_load(yaml_str)
            
            if not isinstance(result, dict) or "code" not in result:
                raise ValueError("Invalid response structure: missing 'code' field")
            
            # Execute the code using the code_executor utility
            metadata = {
                "task_description": task["description"],
                "visualization_type": result.get("visualization_type", "none"),
                "explanation": result.get("explanation", ""),
                "analysis_context": analysis
            }
            
            logger.log_step("CodeExecutor", "exec", "Executing code", result["code"])
            
            # Execute and upload the visualization
            execution_result = execute_and_upload(result["code"], metadata)
            
            if not execution_result or not isinstance(execution_result, dict):
                raise ValueError(f"Invalid execution result: {execution_result}")
            
            if not execution_result.get("success", False):
                error_msg = execution_result.get("error", "Unknown error")
                raise Exception(f"Code execution failed: {error_msg}")
            
            logger.log_step("CodeExecutor", "exec", "Code execution completed", {
                "status": execution_result["success"],
                "output": execution_result.get("urls", []),
                "error": execution_result.get("error")
            })
            
            return {
                "status": "success",
                "code": result["code"],
                "explanation": result.get("explanation", ""),
                "visualization_type": result.get("visualization_type", "none"),
                "visualization_urls": execution_result.get("urls", []),
                "output": execution_result.get("output", "Visualization generated and uploaded successfully")
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.log_error("CodeExecutor", e, "Failed to process code execution")
            return {
                "status": "error",
                "error": error_msg,
                "code": result.get("code") if 'result' in locals() else None,
                "explanation": result.get("explanation") if 'result' in locals() else None
            }
    
    def post(self, shared, prep_res, exec_res):
        if "code_execution_results" not in shared:
            shared["code_execution_results"] = []
        shared["code_execution_results"].append({
            "task": shared["current_task"],
            "result": exec_res
        })
        return "default"

class ReporterNode(Node):
    """Generates final comprehensive report."""
    
    def prep(self, shared):
        return {
            "analysis": shared["analysis_results"],
            "code_results": shared.get("code_execution_results", []),
            "web_research": shared.get("web_research_results", [])
        }
    
    def exec(self, data):
        # Extract visualization URLs from code execution results
        visualization_urls = []
        for result in data['code_results']:
            if result['result'].get('status') == 'success':
                urls = result['result'].get('visualization_urls', [])
                if urls:
                    visualization_urls.extend(urls)
        
        # Extract sources from web research results
        sources = []
        for research in data['web_research']:
            if research['result'].get('status') == 'success':
                for result in research['result'].get('results', []):
                    if 'sources' in result:
                        sources.extend(result['sources'])
        
        prompt = f"""
        Generate a comprehensive research report based on:
        Analysis: {data['analysis']}
        Code Execution Results: {data['code_results']}
        Web Research: {data['web_research']}
        Visualization URLs: {visualization_urls}
        Sources: {sources}
        
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
            - url: <visualization_url>
              description: <description of what the visualization shows>
              type: <type of visualization>
          sources:
            - url: <source_url>
              description: <brief description of the source>
          next_steps:
            - <next step 1>
            - <next step 2>
        ```
        """
        response = call_llm(prompt, model="gemini-1.5-flash", provider="google")
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()
        report = yaml.safe_load(yaml_str)
        
        logger.log_step("Reporter", "exec", "Report generated", report)
        return report
    
    def post(self, shared, prep_res, exec_res):
        shared["final_report"] = exec_res
        return "default"

class SupervisorNode(Node):
    """Monitors and validates the overall workflow."""
    
    def prep(self, shared):
        return {
            "current_task": shared.get("current_task"),
            "remaining_tasks": shared.get("remaining_tasks", []),
            "final_report": shared.get("final_report"),
            "analysis_results": shared.get("analysis_results"),
            "web_research_results": shared.get("web_research_results", []),
            "code_execution_results": shared.get("code_execution_results", [])
        }
    
    def exec(self, data):
        # If we have a final report, validate it
        if data["final_report"]:
            prompt = f"""
            Review this research report and determine if it meets quality standards:
            {data['final_report']}
            
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
            
            if decision["decision"]["approved"]:
                logger.log_step("Supervisor", "exec", "Report approved")
                return {"action": "complete"}
            logger.log_step("Supervisor", "exec", "Report not approved")
            return {"action": "needs_revision", "feedback": decision["decision"]["feedback"]}
        
        # If we have analysis results, check if we need code execution
        if data["analysis_results"]:
            analysis = data["analysis_results"]
            
            # Check if we already have code execution results
            if data["code_execution_results"]:
                logger.log_step("Supervisor", "exec", "Code execution already completed")
                return {"action": "report"}
            
            # Check for visualization needs
            needs_visualization = False
            if isinstance(analysis, dict):
                # Check if there are visualization recommendations
                if "visualizations" in analysis and analysis["visualizations"]:
                    needs_visualization = True
                # Check if there are metrics that could be visualized
                if "metrics" in analysis and analysis["metrics"]:
                    needs_visualization = True
                # Check if there are categories that could be visualized
                if "categories" in analysis and analysis["categories"]:
                    needs_visualization = True
                # Check if there is time series data that could be visualized
                if "time_series" in analysis and analysis["time_series"]:
                    needs_visualization = True

            if needs_visualization:
                logger.log_step("Supervisor", "exec", "Visualization needed based on analysis")
                # Create a code execution task if none exists
                if not data["current_task"] or data["current_task"]["type"] != "code_execution":
                    code_task = {
                        "type": "code_execution",
                        "description": "Generate visualizations based on analysis results",
                        "parameters": {
                            "code_requirements": [
                                "Create visualizations for the analyzed data",
                                "Use appropriate chart types based on data characteristics",
                                "Include proper labels and titles",
                                "Ensure visualizations are clear and informative"
                            ]
                        }
                    }
                    return {
                        "action": "execute_code",
                        "task": code_task
                    }
                return {"action": "execute_code"}
            
            # Check for other code execution needs
            prompt = f"""
            Based on the analysis results, determine if code execution is needed for data processing or other tasks:
            {analysis}
            
            Return your decision in YAML format:
            ```yaml
            decision:
              needs_code: true/false
              reason: <explanation>
            ```
            """
            response = call_llm(prompt)
            yaml_str = response.split("```yaml")[1].split("```")[0].strip()
            decision = yaml.safe_load(yaml_str)
            
            if decision["decision"]["needs_code"]:
                logger.log_step("Supervisor", "exec", "Code execution needed", decision["decision"]["reason"])
                # Create a code execution task if none exists
                if not data["current_task"] or data["current_task"]["type"] != "code_execution":
                    code_task = {
                        "type": "code_execution",
                        "description": decision["decision"]["reason"],
                        "parameters": {
                            "code_requirements": [
                                "Process and analyze the data as needed",
                                "Implement the required functionality",
                                "Ensure proper error handling",
                                "Include appropriate documentation"
                            ]
                        }
                    }
                    return {
                        "action": "execute_code",
                        "task": code_task
                    }
                return {"action": "execute_code"}
            
            logger.log_step("Supervisor", "exec", "No code execution needed")
            return {"action": "report"}
        
        # If we have web research results, proceed to analysis
        if data["web_research_results"]:
            logger.log_step("Supervisor", "exec", "Web research results available")
            return {"action": "analyze"}
        
        # If we have a current task, determine next step
        if data["current_task"]:
            task_type = data["current_task"]["type"]
            logger.log_step("Supervisor", "exec", "Current task type", task_type)
            if task_type == "web_research":
                return {"action": "research"}
            elif task_type == "code_execution":
                return {"action": "execute_code"}
        
        # If we have remaining tasks, move to the next one
        if data["remaining_tasks"]:
            logger.log_step("Supervisor", "exec", "Remaining tasks available")
            return {"action": "needs_revision"}
        
        # Default to reporting if no other conditions met
        logger.log_step("Supervisor", "exec", "No other conditions met -> reporting")
        return {"action": "report"}
    
    def post(self, shared, prep_res, exec_res):
        action = exec_res["action"]
        
        # Handle task creation for code execution
        if action == "execute_code" and "task" in exec_res:
            shared["current_task"] = exec_res["task"]
            return action
        
        # Update task tracking if needed
        if action == "needs_revision" and shared["remaining_tasks"]:
            shared["current_task"] = shared["remaining_tasks"][0]
            shared["remaining_tasks"] = shared["remaining_tasks"][1:]
        
        return action 
