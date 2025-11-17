"""
Sentiment Analyzer using pluggable LLM clients with structured JSON outputs.
"""
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional
from config import (
    SENTIMENT_SCHEMA,
    ANALYSIS_FIELDS,
    SENTIMENT_CATEGORIES,
    LLM_PROVIDER,
    OPENAI_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_API_URL,
    LLM_MAX_WORKERS,
    LLM_REQUEST_DELAY,
)
from llm_client import LLMClient, OpenAIClient, GeminiClient


class SentimentAnalyzer:
    """Handles sentiment analysis with schema-constrained outputs."""

    def __init__(self, llm_client: Optional[LLMClient] = None, **_: Any):
        """
        Accept an optional LLM client (for dependency injection).
        Extra keyword arguments are ignored for backwards compatibility.
        """
        self.llm_client = llm_client or self._build_default_client()

    def _build_default_client(self) -> LLMClient:
        """Instantiate the default LLM client based on config settings."""
        if LLM_PROVIDER == "gemini":
            if not GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY environment variable is not set")
            return GeminiClient(
                api_key=GEMINI_API_KEY,
                model=GEMINI_MODEL,
                url_template=GEMINI_API_URL,
            )

        return OpenAIClient(model=OPENAI_MODEL)

    def _build_prompt(self, text: str, context: str = "post") -> str:
        """Create a concise, structured prompt for sentiment analysis."""

        
        prompt = f"""Analyze sentiment for this Reddit {context} about Taboola (ad tech company).

    Analyze these specific fields:
    {', '.join(ANALYSIS_FIELDS)}

    Return JSON matching this exact schema:
    {json.dumps(SENTIMENT_SCHEMA, indent=2)}

    EXAMPLES:

    Example 1 (Sarcasm):
    TEXT: "Oh great, more Taboola clickbait. Just wonderful how they clutter every website."
    OUTPUT: {{
    "overall_sentiment": "negative",
    "field_sentiments": {{
        "product_quality": {{"sentiment": "negative", "confidence": 0.9, "key_phrases": ["clickbait"]}},
        "user_experience": {{"sentiment": "negative", "confidence": 0.95, "key_phrases": ["clutter every website"]}}
    }},
    "edge_cases": {{"is_sarcastic": true, "has_mixed_sentiment": false, "is_non_english": false, "language": "en", "is_spam": false}},
    "themes": [{{"theme": "ad_intrusiveness", "relevance": 0.9}}],
    "reasoning": "Sarcastic negative sentiment about ad quality and intrusiveness"
    }}

    Example 2 (Positive):
    TEXT: "Implemented Taboola Realize last quarter. Revenue up 40% and publishers love the dashboard."
    OUTPUT: {{
    "overall_sentiment": "positive",
    "field_sentiments": {{
        "financial_performance": {{"sentiment": "positive", "confidence": 0.95, "key_phrases": ["revenue up 40%"]}},
        "publisher_relations": {{"sentiment": "positive", "confidence": 0.85, "key_phrases": ["publishers love"]}},
        "user_experience": {{"sentiment": "positive", "confidence": 0.8, "key_phrases": ["love the dashboard"]}}
    }},
    "edge_cases": {{"is_sarcastic": false, "has_mixed_sentiment": false, "is_non_english": false, "language": "en", "is_spam": false}},
    "themes": [{{"theme": "realize_success", "relevance": 0.9}}],
    "reasoning": "Strong positive sentiment about financial results and publisher satisfaction"
    }}


    Now analyze this text:
    TEXT: {text[:2000]}

    IMPORTANT:
    - Only analyze fields relevant to the text (set confidence=0 if not mentioned)
    - Detect sarcasm carefully like in Example 1
    - Flag mixed sentiment if positive AND negative present like in Example 3
    - Be concise but accurate"""
        return prompt

    def analyze_text(
        self,
        text: str,
        context: str = "post",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze sentiment for a given text and ensure schema compliance.
        """
        if not text or not text.strip():
            empty_response = self._get_empty_response()
            if metadata:
                empty_response["metadata"] = metadata
            return empty_response

        prompt = self._build_prompt(text, context)
        raw_output = self.llm_client.generate(prompt)
        parsed = self._parse_llm_output(raw_output)
        validated = self._validate_and_fix_response(parsed)

        if metadata:
            validated["metadata"] = metadata

        return validated

    def analyze_batch(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze multiple items in batch using a worker pool to avoid long waits.
        """
        total = len(items)
        if total == 0:
            return []

        results: List[Optional[Dict[str, Any]]] = [None] * total
        max_workers = max(1, LLM_MAX_WORKERS)

        def process_item(index: int, item: Dict[str, Any]):
            try:
                result = self.analyze_text(
                    text=item.get("text", ""),
                    context=item.get("context", "post"),
                    metadata=item.get("metadata", {}),
                )
            except Exception as exc:
                print(f"Error analyzing item {index + 1}/{total}: {exc}")
                result = self._get_empty_response()
            return index, result

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for idx, item in enumerate(items):
                futures.append(executor.submit(process_item, idx, item))
                if LLM_REQUEST_DELAY > 0 and idx < total - 1:
                    time.sleep(LLM_REQUEST_DELAY)

            completed = 0
            progress_interval = max(1, total // 5)
            for future in as_completed(futures):
                idx, result = future.result()
                results[idx] = result
                completed += 1
                if completed % progress_interval == 0 or completed == total:
                    print(f"    LLM progress: {completed}/{total} items processed")

        return [res if isinstance(res, dict) else self._get_empty_response() for res in results]

    def _parse_llm_output(self, raw_output: Any) -> Dict[str, Any]:
        """Convert raw provider response into a Python dictionary."""
        if isinstance(raw_output, dict):
            return raw_output
        if isinstance(raw_output, str):
            try:
                return json.loads(raw_output)
            except json.JSONDecodeError as exc:
                raise ValueError("LLM output is not valid JSON") from exc

        raise ValueError("Unsupported LLM output type")

    def _validate_and_fix_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and fix the API response to match expected schema."""
        if isinstance(response, list):
            response = next((item for item in response if isinstance(item, dict)), {})

        if not isinstance(response, dict):
            return self._get_empty_response()

        if "overall_sentiment" not in response or response["overall_sentiment"] not in SENTIMENT_CATEGORIES:
            response["overall_sentiment"] = "neutral"

        field_sentiments = response.get("field_sentiments", {})
        normalized_fs: Dict[str, Dict[str, Any]] = {}

        if isinstance(field_sentiments, dict):
            normalized_fs = field_sentiments
        elif isinstance(field_sentiments, list):
            for item in field_sentiments:
                if isinstance(item, dict):
                    field_name = item.get("field")
                    if field_name and field_name in ANALYSIS_FIELDS:
                        normalized_fs[field_name] = item
            if not normalized_fs:
                for idx, field in enumerate(ANALYSIS_FIELDS):
                    if idx < len(field_sentiments) and isinstance(field_sentiments[idx], dict):
                        normalized_fs[field] = field_sentiments[idx]
        response["field_sentiments"] = normalized_fs

        for field in ANALYSIS_FIELDS:
            if field not in response["field_sentiments"] or not isinstance(response["field_sentiments"][field], dict):
                response["field_sentiments"][field] = {
                    "sentiment": "neutral",
                    "confidence": 0.0,
                    "key_phrases": [],
                }
            else:
                fs = response["field_sentiments"][field]
                if fs.get("sentiment") not in SENTIMENT_CATEGORIES:
                    fs["sentiment"] = "neutral"
                if "confidence" not in fs:
                    fs["confidence"] = 0.0
                if "key_phrases" not in fs:
                    fs["key_phrases"] = []

        if "edge_cases" not in response:
            response["edge_cases"] = {
                "is_sarcastic": False,
                "has_mixed_sentiment": False,
                "is_non_english": False,
                "language": "en",
                "is_spam": False,
            }

        if "themes" not in response or not isinstance(response["themes"], list):
            response["themes"] = []

        if "reasoning" not in response:
            response["reasoning"] = "Analysis completed"

        return response

    def _get_empty_response(self) -> Dict[str, Any]:
        """Return empty response for invalid input."""
        return {
            "overall_sentiment": "neutral",
            "field_sentiments": {
                field: {"sentiment": "neutral", "confidence": 0.0, "key_phrases": []}
                for field in ANALYSIS_FIELDS
            },
            "edge_cases": {
                "is_sarcastic": False,
                "has_mixed_sentiment": False,
                "is_non_english": False,
                "language": "unknown",
                "is_spam": False,
            },
            "themes": [],
            "reasoning": "Empty or invalid text",
        }
