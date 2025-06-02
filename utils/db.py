"""Database utilities for the research system."""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    JSON,
    Boolean,
    DateTime,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from utils.logger import research_logger as logger

# Create base class for declarative models
Base = declarative_base()


class TaskExecution(Base):
    """SQLAlchemy model for task executions."""

    __tablename__ = "task_executions"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    query = Column(Text, nullable=False)
    tasks = Column(JSON, nullable=False)
    execution_results = Column(JSON, nullable=False)
    success = Column(Boolean, nullable=False)
    feedback = Column(Text, nullable=True)


class Database:
    """Database connection and operations manager."""

    def __init__(self):
        """Initialize database connection."""
        self.engine = create_engine(os.getenv("POSTGRES_URL"))
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_execution(
        self,
        query: str,
        tasks: List[Dict[str, Any]],
        execution_results: List[Dict[str, Any]],
        success: bool,
        feedback: Optional[str] = None,
    ):
        """Add a new task execution to database."""
        session = self.Session()
        try:
            execution = TaskExecution(
                query=query,
                tasks=tasks,
                execution_results=execution_results,
                success=success,
                feedback=feedback,
            )
            session.add(execution)
            session.commit()
        except Exception as e:
            logger.error(f"Error adding execution to database: {str(e)}")
            session.rollback()
            raise
        finally:
            session.close()

    def get_execution_by_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Get task execution by exact query match."""
        session = self.Session()
        try:
            execution = (
                session.query(TaskExecution)
                .filter(TaskExecution.query == query)
                .order_by(TaskExecution.timestamp.desc())
                .first()
            )
            if execution:
                return {
                    "timestamp": execution.timestamp.isoformat(),
                    "query": execution.query,
                    "tasks": execution.tasks,
                    "execution_results": execution.execution_results,
                    "success": execution.success,
                    "feedback": execution.feedback,
                }
            return None
        finally:
            session.close()

    def get_recent_executions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most recent task executions."""
        session = self.Session()
        try:
            executions = (
                session.query(TaskExecution)
                .order_by(TaskExecution.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "query": e.query,
                    "tasks": e.tasks,
                    "execution_results": e.execution_results,
                    "success": e.success,
                    "feedback": e.feedback,
                }
                for e in executions
            ]
        finally:
            session.close()

    def get_successful_tasks(self, task_type: str) -> List[Dict[str, Any]]:
        """Get successful tasks of a specific type."""
        session = self.Session()
        try:
            executions = (
                session.query(TaskExecution).filter(TaskExecution.success == True).all()
            )

            successful_tasks = []
            for execution in executions:
                for task, result in zip(execution.tasks, execution.execution_results):
                    if task["type"] == task_type and result.get("status") == "success":
                        successful_tasks.append(
                            {"task": task, "result": result, "query": execution.query}
                        )
            return successful_tasks
        finally:
            session.close()

    def get_task_metrics(self) -> Dict[str, Any]:
        """Get metrics about task execution history."""
        session = self.Session()
        try:
            total_executions = session.query(TaskExecution).count()
            successful_executions = (
                session.query(TaskExecution)
                .filter(TaskExecution.success == True)
                .count()
            )

            metrics = {
                "total_executions": total_executions,
                "successful_executions": successful_executions,
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

            # Get all executions for task type counting
            executions = session.query(TaskExecution).all()
            for execution in executions:
                for task in execution.tasks:
                    task_type = task["type"]
                    metrics["task_type_counts"][task_type] += 1
                    if execution.success:
                        metrics["success_rate_by_type"][task_type] += 1

            # Calculate success rates
            for task_type in metrics["task_type_counts"]:
                count = metrics["task_type_counts"][task_type]
                if count > 0:
                    metrics["success_rate_by_type"][task_type] /= count

            return metrics
        finally:
            session.close()


if __name__ == "__main__":
    db = Database()
    print(db.get_task_metrics())
