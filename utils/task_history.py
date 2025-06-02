"""Task history tracking and learning system."""

from typing import Dict, List, Any, Optional
from utils.logger import research_logger as logger
from utils.db import Database
from utils.vector_search import VectorSearch


class TaskHistory:
    """Tracks and learns from task execution history."""

    def __init__(self):
        """Initialize task history with database and vector search."""
        self.db = Database()
        self.vector_search = VectorSearch()

    def add_execution(
        self,
        query: str,
        tasks: List[Dict[str, Any]],
        execution_results: List[Dict[str, Any]],
        success: bool,
        feedback: Optional[str] = None,
    ):
        """Add a new task execution to history."""
        try:
            # Add to database
            self.db.add_execution(
                query=query,
                tasks=tasks,
                execution_results=execution_results,
                success=success,
                feedback=feedback,
            )

            # Add to vector search with metadata
            metadata = {
                "success": success,
                "feedback": feedback or "",  # Convert None to empty string
                "task_count": len(tasks),
                "task_types": [task["type"] for task in tasks],
            }
            self.vector_search.add_query(query, metadata)

        except Exception as e:
            logger.log_error("TaskHistory", e, "Error adding execution to history")
            raise

    def get_similar_queries(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get similar queries from history."""
        try:
            # 1. Find similar queries using Pinecone
            similar_queries = self.vector_search.search_similar(query, limit)

            # 2. Get full execution details from PostgreSQL for each similar query
            results = []
            for similar in similar_queries:
                # Get the specific execution using the query from Pinecone
                execution = self.db.get_execution_by_query(similar["query"])
                if execution:
                    # Add similarity score from Pinecone to the result
                    execution["similarity_score"] = similar["score"]
                    results.append(execution)

            return results
        except Exception as e:
            logger.log_error("TaskHistory", e, "Error getting similar queries")
            return []

    def get_successful_tasks(self, task_type: str) -> List[Dict[str, Any]]:
        """Get successful tasks of a specific type."""
        try:
            return self.db.get_successful_tasks(task_type)
        except Exception as e:
            logger.log_error(
                "TaskHistory", e, f"Error getting successful tasks for type {task_type}"
            )
            return []

    def get_task_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get successful task templates by type."""
        templates = {"web_research": [], "data_analysis": [], "code_execution": []}

        try:
            # Get successful tasks for each type
            for task_type in templates:
                successful_tasks = self.get_successful_tasks(task_type)
                for task_data in successful_tasks:
                    task = task_data["task"]
                    template = {
                        "template": task["template"],
                        "description": task["description"],
                        "parameters": task["parameters"],
                        "success_criteria": task["success_criteria"],
                        "required_tools": task["required_tools"],
                        "query": task_data["query"],
                    }
                    if template not in templates[task_type]:
                        templates[task_type].append(template)

            return templates
        except Exception as e:
            logger.log_error("TaskHistory", e, "Error getting task templates")
            return templates

    def get_task_metrics(self) -> Dict[str, Any]:
        """Get metrics about task execution history."""
        try:
            return self.db.get_task_metrics()
        except Exception as e:
            logger.log_error("TaskHistory", e, "Error getting task metrics")
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "task_type_counts": {
                    "web_research": 0,
                    "data_analysis": 0,
                    "code_execution": 0,
                },
                "success_rate_by_type": {
                    "web_research": 0,
                    "data_analysis": 0,
                    "code_execution": 0,
                },
            }
