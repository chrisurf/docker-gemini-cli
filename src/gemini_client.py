#!/usr/bin/env python3
"""
Gemini API Client
Handles all interactions with Google's Gemini AI
"""

import asyncio
import os
from typing import Any, Dict, List, Optional

import google.generativeai as genai
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()


class GeminiClient:
    """Client for interacting with Gemini AI"""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        # Initialize model
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
        self.model = genai.GenerativeModel(self.model_name)

        # Configuration
        self.generation_config = {
            "temperature": float(os.getenv("GEMINI_TEMPERATURE", "0.7")),
            "top_p": float(os.getenv("GEMINI_TOP_P", "0.8")),
            "top_k": int(os.getenv("GEMINI_TOP_K", "40")),
            "max_output_tokens": int(os.getenv("GEMINI_MAX_TOKENS", "2048")),
        }

        logger.info("Gemini client initialized", model=self.model_name)

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_response(
        self, prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate response from Gemini AI"""
        try:
            # Prepare the full prompt with context
            full_prompt = self._prepare_prompt(prompt, context)

            logger.info("Generating response", prompt_length=len(full_prompt))

            # Generate response
            response = await asyncio.to_thread(
                self.model.generate_content,
                full_prompt,
                generation_config=self.generation_config,
            )

            # Process response
            result = {
                "success": True,
                "response": response.text,
                "model": self.model_name,
                "finish_reason": (
                    response.candidates[0].finish_reason.name
                    if response.candidates
                    else None
                ),
                "safety_ratings": self._extract_safety_ratings(response),
            }

            logger.info(
                "Response generated successfully", response_length=len(response.text)
            )

            return result

        except Exception as e:
            logger.error("Error generating response", error=str(e))
            return {"success": False, "error": str(e), "model": self.model_name}

    def _prepare_prompt(
        self, prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Prepare the full prompt with context and instructions"""
        system_prompt = """You are an autonomous AI agent running in a Docker container.
Your role is to complete tasks efficiently and accurately. You have access to:
- File system operations in /app/data/
- Various data processing capabilities
- The ability to generate reports and analysis

Always provide detailed, actionable responses. When working with files or data,
be explicit about your actions and results."""

        context_section = ""
        if context:
            context_section = f"\nContext:\n{self._format_context(context)}\n"

        full_prompt = f"{system_prompt}{context_section}\nTask: {prompt}"

        return full_prompt

    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context information for the prompt"""
        formatted_lines = []

        for key, value in context.items():
            if isinstance(value, (list, dict)):
                formatted_lines.append(f"- {key}: {str(value)[:200]}...")
            else:
                formatted_lines.append(f"- {key}: {value}")

        return "\n".join(formatted_lines)

    def _extract_safety_ratings(self, response) -> List[Dict[str, Any]]:
        """Extract safety ratings from response"""
        safety_ratings = []

        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "safety_ratings"):
                for rating in candidate.safety_ratings:
                    safety_ratings.append(
                        {
                            "category": rating.category.name,
                            "probability": rating.probability.name,
                        }
                    )

        return safety_ratings

    async def analyze_file(
        self, file_path: str, analysis_type: str = "general"
    ) -> Dict[str, Any]:
        """Analyze a specific file"""
        try:
            # Read file content (basic text files only for now)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            context = {
                "task_type": "file_analysis",
                "analysis_type": analysis_type,
                "file_path": file_path,
                "content_length": len(content),
            }

            prompt = f"""
            File Analysis Task ({analysis_type}):

            File: {file_path}
            Content:
            {content[:2000]}...  # Truncate for API limits

            Please provide a comprehensive analysis including:
            1. Content summary
            2. Key insights
            3. Data patterns
            4. Recommendations
            """

            return await self.generate_response(prompt, context)

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to analyze file: {str(e)}",
            }

    async def process_data_task(
        self, task_description: str, file_names: List[str]
    ) -> Dict[str, Any]:
        """Process a data-related task"""
        context = {
            "task_type": "data_processing",
            "available_files": ", ".join(file_names),
            "file_count": len(file_names),
        }

        prompt = f"""
        Data Processing Task: {task_description}

        Available data files: {', '.join(file_names)}

        Please provide:
        1. Analysis approach
        2. Expected insights
        3. Processing steps
        4. Output format recommendations
        """

        return await self.generate_response(prompt, context)

    async def health_check(self) -> bool:
        """Check if Gemini API is accessible with minimal API usage"""
        try:
            # Use a very short test prompt to minimize API usage
            test_prompt = "Hi"
            response = await self.generate_response(test_prompt)
            success = response.get("success", False)

            if success:
                logger.info("Health check passed", model=self.model_name)
            else:
                logger.warning("Health check failed", error=response.get("error"))

            return success
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return False

    async def close(self):
        """Clean up resources"""
        logger.info("Gemini client cleanup complete")
