import logging
import json
import asyncio
from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Interface to interact with Gemini LLM models. Supports real calls and test mocks."""
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL

    async def generate_content(self, prompt: str, system_instruction: str = None) -> str:
        if not self.api_key or self.api_key == "mock" or "dummy" in self.api_key:
            # Mock AI response for testing and local dev
            return self._get_mock_response(prompt)
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction
            )
            loop = asyncio.get_running_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: model.generate_content(prompt)
                ),
                timeout=settings.GEMINI_TIMEOUT_SECONDS
            )
            return response.text
        except Exception as e:
            logger.warning(f"Gemini generation error or timeout: {str(e)}")
            raise

    def _get_mock_response(self, prompt: str) -> str:
        # Return a simulated list of tailored suggestions in JSON format
        suggestions = [
            {
                "section_name": "experience",
                "suggestion_type": "bullet_rewrite",
                "original_content": "Worked on software development and deployment.",
                "suggested_content": "Led development of high-throughput software systems, accelerating deployment efficiency by 25% using Docker/Kubernetes.",
                "confidence_score": 0.92,
                "reason": "Experience section lacks quantified achievements and modern DevOps tool stack representation."
            },
            {
                "section_name": "summary",
                "suggestion_type": "section_improvement",
                "original_content": "A software engineer with experience.",
                "suggested_content": "Results-oriented Software Engineer with 5+ years of experience specializing in Python, scalable web systems, and cloud architecture (AWS). Proven track record of optimizing ATS metrics.",
                "confidence_score": 0.88,
                "reason": "Professional summary can be made more punchy with quantified impact and target role alignment."
            }
        ]
        return json.dumps(suggestions)

