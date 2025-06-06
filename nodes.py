from pocketflow import Node
import yaml
from utils.llm import call_llm
from utils.logger import research_logger as logger
from utils.web_search import search_web_firecrawl
from utils.code_executor import execute_and_upload
from utils.task_validator import TaskValidator
from utils.task_history import TaskHistory
from prompts.planner import PLANNER_PROMPT
from prompts.data_analysis import DATA_ANALYSIS_PROMPT
from prompts.code_executor import CODE_EXECUTION_PROMPT
from prompts.reporter import REPORTER_PROMPT
from prompts.supervisor import CODE_EXECUTION_NEEDS_PROMPT, VALIDATION_PROMPT


class PlannerNode(Node):
    """Decomposes complex research queries into subtasks."""

    def __init__(self, max_retries=3, wait=10):
        """Initialize planner with task history and validator."""
        super().__init__(max_retries=max_retries, wait=wait)
        self.task_history = TaskHistory()
        self.task_validator = TaskValidator()

    def prep(self, shared):
        """Prepare for task planning by gathering context."""
        query = shared["query"]

        # Get similar queries from history
        similar_queries = self.task_history.get_similar_queries(query)

        # Get successful task templates
        task_templates = self.task_history.get_task_templates()

        # Get task metrics
        metrics = self.task_history.get_task_metrics()

        return {
            "query": query,
            "similar_queries": similar_queries,
            "task_templates": task_templates,
            "metrics": metrics,
        }

    def exec(self, context):
        """Execute task planning with validation."""
        logger.log_step("Planner", "exec", "Decomposing query into tasks")

        # Format prompt with context
        prompt = PLANNER_PROMPT.format(
            query=context["query"],
            similar_queries=context["similar_queries"],
            task_templates=context["task_templates"],
            metrics=context["metrics"],
        )

        response = call_llm(prompt)

        try:
            # Extract YAML from response
            yaml_str = response.split("```yaml")[1].split("```")[0].strip()

            # Validate tasks
            validation_result = self.task_validator.validate_tasks(yaml_str)
            if not validation_result["is_valid"]:
                logger.log_step(
                    "Planner",
                    "exec",
                    "Task validation failed",
                    validation_result["errors"],
                )
                raise ValueError(
                    "Task validation failed: " + "\n".join(validation_result["errors"])
                )

            tasks = yaml.safe_load(yaml_str)
            logger.log_step("Planner", "exec", "Successfully decomposed tasks", tasks)
            return tasks

        except Exception as e:
            logger.log_step(
                "Planner",
                "exec",
                f"Error parsing YAML: {str(e)}",
                {"response": response, "error": str(e)},
            )
            raise

    def post(self, shared, prep_res, exec_res):
        """Store tasks and update history."""
        shared["tasks"] = exec_res["tasks"]
        shared["current_task"] = exec_res["tasks"][0]
        shared["remaining_tasks"] = exec_res["tasks"][1:]

        # Add to task history
        self.task_history.add_execution(
            query=prep_res["query"],
            tasks=exec_res["tasks"],
            execution_results=[],  # Will be populated as tasks complete
            success=False,  # Will be updated by supervisor
            feedback=None,
        )

        return "default"


class WebResearchNode(Node):
    """Performs web research based on search terms using Firecrawl API."""

    def prep(self, shared):
        return shared["current_task"]

    def exec(self, task):
        if task["type"] != "web_research":
            logger.log_step(
                "WebResearch",
                "exec",
                "Skipping non-web-research task",
                {"task_type": task["type"]},
            )
            return {
                "status": "skipped",
                "reason": f"Task type {task['type']} is not a web research task",
            }

        search_terms = task["parameters"].get("search_terms", [])
        if not search_terms:
            search_terms = [task["description"]]

        all_results = []
        for term in search_terms[:1]:  # Limit to one search term for now
            try:
                search_results = search_web_firecrawl(term, max_results=1)
                all_results.append(
                    {
                        "term": term,
                        "findings": [search_results[0]["data"]],
                        "sources": ["Firecrawl Search"],
                        "status": "success",
                    }
                )
            except Exception as e:
                logger.log_step(
                    "WebResearch", "exec", f"Error searching for term {term}", str(e)
                )
                all_results.append(
                    {
                        "term": term,
                        "findings": [f"Error during search: {str(e)}"],
                        "sources": ["Error"],
                        "status": "error",
                    }
                )

        logger.log_step(
            "WebResearch",
            "exec",
            "Research completed",
            all_results[0]["findings"][0][:300],
        )

        return {"status": "success", "results": all_results}

    def post(self, shared, prep_res, exec_res):
        if "web_research_results" not in shared:
            shared["web_research_results"] = []
        shared["web_research_results"].append(
            {"task": shared["current_task"], "result": exec_res}
        )
        return "default"


class DataAnalysisNode(Node):
    """Analyzes and synthesizes gathered information, performing ETL and preparing data for visualization."""

    def prep(self, shared):
        return shared["web_research_results"]

    def exec(self, research_results):
        # First, extract and structure the data
        prompt = DATA_ANALYSIS_PROMPT.format(research_results=research_results)
        response = call_llm(prompt, model="gemini-1.5-flash", provider="google")
        yaml_str = response.split("```yaml")[1].split("```")[0].strip()
        analysis = yaml.safe_load(yaml_str)

        # Validate the analysis structure
        if not isinstance(analysis, dict) or "analysis" not in analysis:
            raise ValueError("Invalid analysis structure: missing 'analysis' key")

        analysis = analysis["analysis"]

        # Ensure we have at least some form of analysis
        if not any(
            key in analysis
            for key in ["key_findings", "metrics", "categories", "time_series"]
        ):
            raise ValueError(
                "Analysis must contain at least one of: key_findings, metrics, categories, or time_series"
            )

        # Log the analysis results
        logger.log_step(
            "DataAnalysis",
            "exec",
            "Analysis completed",
            {
                "metrics_count": len(analysis.get("metrics", [])),
                "categories_count": len(analysis.get("categories", [])),
                "time_series_count": len(analysis.get("time_series", [])),
                "visualizations_count": len(analysis.get("visualizations", [])),
            },
        )

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
                "reason": f"Task type {task['type']} is not a code execution task",
            }

        code_requirements = task["parameters"].get("code_requirements", [])

        prompt = CODE_EXECUTION_PROMPT.format(
            code_requirements=code_requirements, analysis=analysis
        )

        response = call_llm(
            prompt, model="claude-3-5-sonnet-20240620", provider="anthropic"
        )

        try:
            # Handle response based on its type
            if isinstance(response, list):
                # Extract text from TextBlock objects
                response = "\n".join(
                    item.text if hasattr(item, "text") else str(item)
                    for item in response
                )

            # Extract YAML from response
            if "```yaml" in response:
                yaml_str = response.split("```yaml")[1].split("```")[0].strip()
            else:
                yaml_str = response.strip()

            # Clean up the YAML string
            yaml_str = yaml_str.replace("\\n", "\n")  # Replace escaped newlines
            yaml_str = yaml_str.replace("\\", "")  # Remove any remaining backslashes

            result = yaml.safe_load(yaml_str)

            if not isinstance(result, dict) or "code" not in result:
                raise ValueError("Invalid response structure: missing 'code' field")

            # Execute the code using the code_executor utility
            metadata = {
                "task_description": task["description"],
                "visualization_type": result.get("visualization_type", "none"),
                "explanation": result.get("explanation", ""),
                "analysis_context": analysis,
            }

            logger.log_step("CodeExecutor", "exec", "Executing code", result["code"])

            # Execute and upload the visualization
            execution_result = execute_and_upload(result["code"], metadata)

            if not execution_result or not isinstance(execution_result, dict):
                raise ValueError(f"Invalid execution result: {execution_result}")

            if not execution_result.get("success", False):
                error_msg = execution_result.get("error", "Unknown error")
                logger.log_error("CodeExecutor", error_msg, "Code execution failed")
                raise Exception(f"Code execution failed: {error_msg}")

            # Verify URLs are accessible
            urls = execution_result.get("urls", [])
            if not urls:
                raise Exception("No visualization URLs were generated")

            logger.log_step(
                "CodeExecutor",
                "exec",
                "Code execution completed",
                {
                    "status": execution_result["success"],
                    "output": urls,
                    "error": execution_result.get("error"),
                },
            )

            return {
                "status": "success",
                "code": result["code"],
                "explanation": result.get("explanation", ""),
                "visualization_type": result.get("visualization_type", "none"),
                "visualization_urls": urls,
                "output": execution_result.get(
                    "output", "Visualization generated and uploaded successfully"
                ),
            }

        except Exception as e:
            error_msg = str(e)
            logger.log_error("CodeExecutor", e, "Failed to process code execution")
            return {
                "status": "error",
                "error": error_msg,
                "code": result.get("code") if "result" in locals() else None,
                "explanation": (
                    result.get("explanation") if "result" in locals() else None
                ),
            }

    def post(self, shared, prep_res, exec_res):
        if "code_execution_results" not in shared:
            shared["code_execution_results"] = []
        shared["code_execution_results"].append(
            {"task": shared["current_task"], "result": exec_res}
        )
        return "default"


class ReporterNode(Node):
    """Generates final comprehensive report."""

    def prep(self, shared):
        return {
            "analysis": shared["analysis_results"],
            "code_results": shared.get("code_execution_results", []),
            "web_research": shared.get("web_research_results", []),
        }

    def exec(self, data):
        # Extract visualization URLs from code execution results
        visualization_urls = []
        for result in data["code_results"]:
            if result["result"].get("status") == "success":
                urls = result["result"].get("visualization_urls", [])
                if urls:
                    visualization_urls.extend(urls)

        # Extract sources from web research results
        sources = []
        for research in data["web_research"]:
            if research["result"].get("status") == "success":
                for result in research["result"].get("results", []):
                    if "sources" in result:
                        sources.extend(result["sources"])

        prompt = REPORTER_PROMPT.format(
            analysis=data["analysis"],
            code_results=data["code_results"],
            web_research=data["web_research"],
            visualization_urls=visualization_urls,
            sources=sources,
        )
        response = call_llm(prompt, model="gemini-1.5-flash", provider="google")

        try:
            # Extract YAML from response
            if "```yaml" in response:
                yaml_str = response.split("```yaml")[1].split("```")[0].strip()
            else:
                yaml_str = response.strip()

            # Clean up the YAML string
            yaml_str = yaml_str.replace("\\n", "\n")  # Replace escaped newlines
            yaml_str = yaml_str.replace("\\", "")  # Remove any remaining backslashes
            yaml_str = yaml_str.replace("...", "")  # Remove YAML document end markers
            yaml_str = yaml_str.replace("---", "")  # Remove YAML document start markers

            # Ensure the YAML has the correct structure
            if not yaml_str.startswith("report:"):
                yaml_str = "report:\n" + yaml_str

            report = yaml.safe_load(yaml_str)

            # Validate the report structure
            if not isinstance(report, dict) or "report" not in report:
                raise ValueError("Invalid report structure: missing 'report' key")

            logger.log_step("Reporter", "exec", "Report generated", report)
            return report["report"]  # Return just the report content

        except Exception as e:
            logger.log_error("Reporter", e, "Failed to parse report YAML")
            # Return a basic report structure if YAML parsing fails
            return {
                "executive_summary": "Error generating report",
                "detailed_findings": [],
                "recommendations": [],
                "visualizations": [],
                "sources": [],
                "next_steps": [],
            }

    def post(self, shared, prep_res, exec_res):
        shared["final_report"] = exec_res
        return "default"


class SupervisorNode(Node):
    """Monitors and validates the overall workflow."""

    def __init__(self, max_retries=3, wait=10):
        """Initialize supervisor with task history."""
        super().__init__(max_retries=max_retries, wait=wait)
        self.task_history = TaskHistory()

    def prep(self, shared):
        return {
            "current_task": shared.get("current_task"),
            "remaining_tasks": shared.get("remaining_tasks", []),
            "final_report": shared.get("final_report"),
            "analysis_results": shared.get("analysis_results"),
            "web_research_results": shared.get("web_research_results", []),
            "code_execution_results": shared.get("code_execution_results", []),
        }

    def exec(self, data):
        # If we have a final report, validate it
        if data["final_report"]:
            prompt = VALIDATION_PROMPT.format(final_report=data["final_report"])
            response = call_llm(prompt)
            yaml_str = response.split("```yaml")[1].split("```")[0].strip()
            decision = yaml.safe_load(yaml_str)

            if decision["decision"]["approved"]:
                logger.log_step("Supervisor", "exec", "Report approved")
                return {"action": "complete"}
            logger.log_step("Supervisor", "exec", "Report not approved")
            return {
                "action": "needs_revision",
                "feedback": decision["decision"]["feedback"],
            }

        # If we have analysis results, check if we need code execution
        if data["analysis_results"]:
            analysis = data["analysis_results"]

            # Check if we already have code execution results
            if data["code_execution_results"]:
                logger.log_step(
                    "Supervisor", "exec", "Code execution already completed"
                )
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
                logger.log_step(
                    "Supervisor", "exec", "Visualization needed based on analysis"
                )
                # Create a code execution task if none exists
                if (
                    not data["current_task"]
                    or data["current_task"]["type"] != "code_execution"
                ):
                    code_task = {
                        "type": "code_execution",
                        "description": "Generate visualizations based on analysis results",
                        "parameters": {
                            "code_requirements": [
                                "Create visualizations for the analyzed data",
                                "Use appropriate chart types based on data characteristics",
                                "Include proper labels and titles",
                                "Ensure visualizations are clear and informative",
                            ]
                        },
                        "template": "Visualization",
                        "success_criteria": [
                            "All required visualizations are generated",
                            "Visualizations are clear and properly labeled",
                            "Data is accurately represented",
                        ],
                        "required_tools": ["matplotlib", "seaborn", "plotly"],
                    }
                    return {"action": "execute_code", "task": code_task}
                return {"action": "execute_code"}

            # Check for other code execution needs
            prompt = CODE_EXECUTION_NEEDS_PROMPT.format(analysis=analysis)
            response = call_llm(prompt)
            yaml_str = response.split("```yaml")[1].split("```")[0].strip()
            decision = yaml.safe_load(yaml_str)

            if decision["decision"]["needs_code"]:
                logger.log_step(
                    "Supervisor",
                    "exec",
                    "Code execution needed",
                    decision["decision"]["reason"],
                )
                # Create a code execution task if none exists
                if (
                    not data["current_task"]
                    or data["current_task"]["type"] != "code_execution"
                ):
                    code_task = {
                        "type": "code_execution",
                        "description": decision["decision"]["reason"],
                        "parameters": {
                            "code_requirements": [
                                "Process and analyze the data as needed",
                                "Implement the required functionality",
                                "Ensure proper error handling",
                                "Include appropriate documentation",
                            ]
                        },
                        "template": "Algorithm Implementation",
                        "success_criteria": [
                            "Code successfully processes the data",
                            "All requirements are implemented",
                            "Error handling is in place",
                            "Documentation is clear and complete",
                        ],
                        "required_tools": ["pandas", "numpy", "scikit-learn"],
                    }
                    return {"action": "execute_code", "task": code_task}
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

        # Update task history with execution results
        if action in ["complete", "needs_revision"]:
            # Get all execution results
            execution_results = []
            if shared.get("web_research_results"):
                execution_results.extend(shared["web_research_results"])
            if shared.get("analysis_results"):
                execution_results.append(shared["analysis_results"])
            if shared.get("code_execution_results"):
                execution_results.extend(shared["code_execution_results"])

            # Update history with success/failure
            success = action == "complete"
            feedback = exec_res.get("feedback") if action == "needs_revision" else None

            self.task_history.add_execution(
                query=shared["query"],
                tasks=shared["tasks"],
                execution_results=execution_results,
                success=success,
                feedback=feedback,
            )

        # Handle task creation for code execution
        if action == "execute_code" and "task" in exec_res:
            shared["current_task"] = exec_res["task"]
            return action

        # Update task tracking if needed
        if action == "needs_revision" and shared["remaining_tasks"]:
            shared["current_task"] = shared["remaining_tasks"][0]
            shared["remaining_tasks"] = shared["remaining_tasks"][1:]

        return action
