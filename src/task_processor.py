#!/usr/bin/env python3
"""
Task Processor for Gemini Autonomous Agent
Handles task execution and processing logic
"""

from pathlib import Path
from typing import Any, Dict

import structlog

logger = structlog.get_logger()


class TaskProcessor:
    """Processes tasks using Gemini AI"""

    def __init__(self, gemini_client):
        self.gemini_client = gemini_client
        self.task_handlers = {
            "analysis": self._handle_analysis_task,
            "data_processing": self._handle_data_processing_task,
            "file_analysis": self._handle_file_analysis_task,
            "general": self._handle_general_task,
        }

    async def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task based on its type"""
        try:
            task_type = task_data.get("type", "general")
            task_id = task_data.get("id", "unknown")

            logger.info("Executing task", task_id=task_id, task_type=task_type)

            # Get appropriate handler
            handler = self.task_handlers.get(task_type, self._handle_general_task)

            # Execute task
            result = await handler(task_data)

            logger.info(
                "Task execution completed",
                task_id=task_id,
                success=result.get("success"),
            )
            return result

        except Exception as e:
            logger.error(
                "Task execution failed", task_id=task_data.get("id"), error=str(e)
            )
            return {"success": False, "error": str(e), "task_id": task_data.get("id")}

    async def _handle_analysis_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analysis tasks"""
        prompt = f"Analysis Task: {task_data['task']}"

        context = {
            "task_type": "analysis",
            "priority": task_data.get("priority", "normal"),
            "deadline": task_data.get("deadline"),
        }

        return await self.gemini_client.generate_response(prompt, context)

    async def _handle_data_processing_task(
        self, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle data processing tasks"""
        # Get available data files
        data_files = list(Path("/app/data/input").glob("*"))
        file_names = [f.name for f in data_files if f.is_file()]

        return await self.gemini_client.process_data_task(task_data["task"], file_names)

    async def _handle_file_analysis_task(
        self, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle file analysis tasks"""
        file_path = task_data.get("file_path")
        analysis_type = task_data.get("analysis_type", "general")

        if file_path:
            return await self.gemini_client.analyze_file(file_path, analysis_type)
        else:
            return {
                "success": False,
                "error": "No file path specified for file analysis task",
            }

    async def _handle_general_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general tasks"""
        return await self.gemini_client.generate_response(task_data["task"])
