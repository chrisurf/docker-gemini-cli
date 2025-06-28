#!/usr/bin/env python3
"""
Autonomous Agent for Gemini CLI
Continuously monitors for tasks and executes them using Gemini AI
"""

import asyncio
import json
import os
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from config_manager import ConfigManager
from gemini_client import GeminiClient
from task_processor import TaskProcessor

# Initialize structured logging
logger = structlog.get_logger()


class TaskFileHandler(FileSystemEventHandler):
    """Handles new task files in the input directory"""

    def __init__(self, agent):
        self.agent = agent
        super().__init__()

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".json"):
            asyncio.create_task(self.agent.process_task_file(event.src_path))


class AutonomousAgent:
    """Main autonomous agent class"""

    def __init__(self):
        self.config = ConfigManager()
        self.gemini_client = GeminiClient()
        self.task_processor = TaskProcessor(self.gemini_client)
        self.running = False
        self.observer = None

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # Ensure directories exist
        self._setup_directories()

    def _setup_directories(self):
        """Create necessary directories"""
        directories = [
            Path("/app/data/input"),
            Path("/app/data/output"),
            Path("/app/data/processed"),
            Path("/app/data/temp"),
            Path("/app/logs"),
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info("Received shutdown signal", signal=signum)
        self.running = False

    async def start(self):
        """Start the autonomous agent"""
        logger.info("Starting Autonomous Agent")
        self.running = True

        # Start file system monitoring
        self._start_file_monitoring()

        # Process any existing tasks
        await self._process_existing_tasks()

        # Main event loop
        await self._main_loop()

    def _start_file_monitoring(self):
        """Start monitoring the input directory for new task files"""
        self.observer = Observer()
        event_handler = TaskFileHandler(self)
        self.observer.schedule(
            event_handler, str(Path("/app/data/input")), recursive=False
        )
        self.observer.start()
        logger.info("File monitoring started")

    async def _process_existing_tasks(self):
        """Process any existing task files in the input directory"""
        input_dir = Path("/app/data/input")
        for task_file in input_dir.glob("*.json"):
            await self.process_task_file(str(task_file))

    async def process_task_file(self, file_path: str):
        """Process a single task file"""
        try:
            logger.info("Processing task file", file_path=file_path)

            with open(file_path, "r") as f:
                task_data = json.load(f)

            # Validate task data
            if not self._validate_task_data(task_data):
                logger.error("Invalid task data", file_path=file_path)
                return

            # Execute task
            result = await self.task_processor.execute_task(task_data)

            # Save result
            await self._save_task_result(task_data, result, file_path)

            # Move processed file
            self._move_processed_file(file_path)

            logger.info(
                "Task completed successfully", task_id=task_data.get("id", "unknown")
            )

        except Exception as e:
            logger.error(
                "Error processing task file", file_path=file_path, error=str(e)
            )

    def _validate_task_data(self, task_data: Dict[str, Any]) -> bool:
        """Validate task data structure"""
        required_fields = ["id", "task", "type"]
        return all(field in task_data for field in required_fields)

    async def _save_task_result(
        self, task_data: Dict[str, Any], result: Dict[str, Any], original_file: str
    ):
        """Save task execution result"""
        output_file = Path("/app/data/output") / f"{task_data['id']}_result.json"

        result_data = {
            "task_id": task_data["id"],
            "original_task": task_data,
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "completed" if result.get("success") else "failed",
        }

        with open(output_file, "w") as f:
            json.dump(result_data, f, indent=2)

        logger.info("Task result saved", output_file=str(output_file))

    def _move_processed_file(self, file_path: str):
        """Move processed file to processed directory"""
        source = Path(file_path)
        destination = Path("/app/data/processed") / source.name
        source.rename(destination)

    async def _main_loop(self):
        """Main event loop"""
        logger.info("Agent main loop started")

        while self.running:
            try:
                # Perform periodic health checks
                await self._health_check()

                # Sleep for a short interval
                await asyncio.sleep(5)

            except Exception as e:
                logger.error("Error in main loop", error=str(e))
                await asyncio.sleep(10)

    async def _health_check(self):
        """Perform health checks"""
        # Check Gemini API connectivity
        if not await self.gemini_client.health_check():
            logger.warning("Gemini API health check failed")

        # Check disk space
        import psutil

        disk_usage = psutil.disk_usage("/app/data")
        if disk_usage.percent > 90:
            logger.warning("Low disk space", usage_percent=disk_usage.percent)

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down agent")
        self.running = False

        if self.observer:
            self.observer.stop()
            self.observer.join()

        await self.gemini_client.close()
        logger.info("Agent shutdown complete")


async def main():
    """Main entry point"""
    agent = AutonomousAgent()

    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        await agent.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
