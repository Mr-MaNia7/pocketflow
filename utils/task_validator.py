"""Task validation utilities for the research system."""

from typing import Dict, List, Any
import yaml
from utils.logger import research_logger as logger


class TaskValidator:
    """Validates task structure and content."""

    VALID_TASK_TYPES = ["web_research", "data_analysis", "code_execution"]

    @staticmethod
    def validate_task_structure(task: Dict[str, Any]) -> List[str]:
        """Validate the structure of a single task."""
        errors = []

        # Check required fields
        required_fields = ["type", "description", "parameters"]
        for field in required_fields:
            if field not in task:
                errors.append(f"Missing required field: {field}")

        # Validate task type
        if "type" in task and task["type"] not in TaskValidator.VALID_TASK_TYPES:
            errors.append(f"Invalid task type: {task['type']}")

        # Validate parameters
        if "parameters" in task:
            if (
                task["type"] == "web_research"
                and "search_terms" not in task["parameters"]
            ):
                errors.append("Web research task missing search_terms")
            elif (
                task["type"] == "data_analysis"
                and "data_sources" not in task["parameters"]
            ):
                errors.append("Data analysis task missing data_sources")
            elif (
                task["type"] == "code_execution"
                and "code_requirements" not in task["parameters"]
            ):
                errors.append("Code execution task missing code_requirements")

        return errors

    @staticmethod
    def validate_task_sequence(tasks: List[Dict[str, Any]]) -> List[str]:
        """Validate the sequence of tasks for logical flow."""
        errors = []

        # Check for empty task list
        if not tasks:
            errors.append("Task list is empty")
            return errors

        return errors

    @staticmethod
    def validate_tasks(tasks_yaml: str) -> Dict[str, List[str]]:
        """Validate a YAML string containing tasks."""
        try:
            tasks_data = yaml.safe_load(tasks_yaml)
            if not isinstance(tasks_data, dict) or "tasks" not in tasks_data:
                return {"errors": ["Invalid YAML structure: missing 'tasks' key"]}

            tasks = tasks_data["tasks"]
            if not isinstance(tasks, list):
                return {"errors": ["Invalid YAML structure: 'tasks' must be a list"]}

            # Validate each task
            task_errors = []
            for i, task in enumerate(tasks):
                errors = TaskValidator.validate_task_structure(task)
                if errors:
                    task_errors.extend([f"Task {i+1}: {error}" for error in errors])

            # Validate task sequence
            sequence_errors = TaskValidator.validate_task_sequence(tasks)

            return {
                "errors": task_errors + sequence_errors,
                "is_valid": len(task_errors) == 0 and len(sequence_errors) == 0,
            }

        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {str(e)}")
            return {"errors": [f"YAML parsing error: {str(e)}"], "is_valid": False}
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return {"errors": [f"Validation error: {str(e)}"], "is_valid": False}
