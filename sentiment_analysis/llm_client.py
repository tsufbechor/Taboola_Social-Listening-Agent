"""
LLM client abstractions for the Reddit sentiment analysis project.
Provides provider-agnostic interface plus OpenAI and Gemini clients.
"""
import json
import os
import time
from typing import Protocol, Dict, Any, List, Optional

import openai
import requests

from config import MAX_RETRIES, RETRY_DELAY, OPENAI_API_KEY, LLM_TIMEOUT


class LLMClient(Protocol):
    """Provider-agnostic interface for language model clients."""

    def generate(self, prompt: str) -> Dict:
        """Execute the prompt and return a JSON-compatible dictionary."""
        ...


class OpenAIClient:
    """LLM client implementation for OpenAI Chat Completions (GPT-5.1)."""

    def __init__(self, model: str):
        api_key = os.getenv("OPENAI_API_KEY") or OPENAI_API_KEY
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY environment variable")

        openai.api_key = api_key
        self.model = model

    def generate(self, prompt: str) -> Dict:
        """Generate a structured response using OpenAI's ChatCompletion API."""
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"},
            timeout=LLM_TIMEOUT,
        )

        message = response.choices[0].message
        content = self._extract_content(message)

        if isinstance(content, dict):
            return content
        if isinstance(content, str):
            return json.loads(content)

        raise ValueError("OpenAI response content is neither string nor dict")

    @staticmethod
    def _extract_content(message: Any) -> Any:
        """Normalize different response message structures into JSON-ready data."""
        if isinstance(message, dict):
            content = message.get("content")
        else:
            content = getattr(message, "content", None)

        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    text_parts.append(part["text"])
            return "".join(text_parts)

        return content


class GeminiClient:
    """LLM client implementation for Google Gemini models."""

    def __init__(
        self,
        api_key: str,
        model: str,
        url_template: str,
        max_retries: int = MAX_RETRIES,
        retry_delay: int = RETRY_DELAY,
    ):
        if not api_key:
            raise ValueError("Gemini API key is required")

        self.api_key = api_key
        self.model = model
        self.url_template = url_template
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def generate(self, prompt: str) -> Dict:
        """Generate structured JSON output from Gemini."""
        url = f"{self.url_template.format(model=self.model)}?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 2000,
                "responseMimeType": "application/json",
            },
        }

        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(url, json=payload, timeout=LLM_TIMEOUT)
                response.raise_for_status()

                data = response.json()
                text_response = self._extract_text_from_response(data)
                if isinstance(text_response, dict):
                    return text_response
                return json.loads(text_response)

            except (requests.RequestException, ValueError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise

        if last_error:
            raise last_error
        raise RuntimeError("Gemini client failed without raising an exception")

    @staticmethod
    def _extract_text_from_response(data: Dict[str, Any]) -> Any:
        """Extract the JSON text from diverse Gemini response formats."""
        if not isinstance(data, dict):
            return data

        candidates = data.get("candidates") or []
        if not isinstance(candidates, list) or not candidates:
            return data

        candidate = candidates[0] or {}
        if not isinstance(candidate, dict):
            return data

        content = candidate.get("content")
        parts: List[Any] = []
        if isinstance(content, dict):
            parts = content.get("parts", [])
        elif isinstance(content, list):
            parts = content

        if parts:
            first = parts[0]
            if isinstance(first, dict):
                if isinstance(first.get("text"), str):
                    return first["text"]
                if "json" in first:
                    return first["json"]
                if "functionCall" in first:
                    fn = first["functionCall"]
                    if isinstance(fn, dict) and "args" in fn:
                        return fn["args"]

        if isinstance(candidate.get("text"), str):
            return candidate["text"]

        return data
