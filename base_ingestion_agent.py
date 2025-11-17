import json
import logging
import time
from dataclasses import asdict
from datetime import datetime, timezone
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
)

from sentiment_analysis.config import DEFAULT_LLM_RESULT

PostT = TypeVar("PostT")
CommentT = TypeVar("CommentT")


def passes_quick_filter(post: Any) -> Tuple[bool, float, str]:
    """
    Shared heuristic filter with confidence scoring.
    Returns: (should_process, confidence, reason)
    """
    title_lower = post.title.lower()
    body_lower = post.selftext.lower()
    content = f"{title_lower} {body_lower}"

    if "taboola" not in content:
        return False, 0.0, "No Taboola mention"

    generic_phrases = [
        "i realize",
        "i realized",
        "just realized",
        "didn't realize",
        "don't realize",
        "never realized",
        "finally realized",
        "suddenly realized",
        "now realize",
        "people realize",
        "you realize",
        "we realize",
        "they realize",
    ]
    for phrase in generic_phrases:
        if phrase in content:
            return False, 0.1, f"Generic phrase: {phrase}"

    strong_indicators = [
        "taboola realize",
        "realize by taboola",
        "taboola's realize",
        "taboola platform",
        "taboola widget",
        "taboola advertising",
        "taboola ad",
        "taboola sponsored",
        "work at taboola",
        "working for taboola",
        "taboola sucks",
        "taboola spam",
        "block taboola",
        "remove taboola",
        "taboola monetization",
        "taboola revenue",
    ]
    for indicator in strong_indicators:
        if indicator in content:
            return True, 0.95, f"Strong indicator: {indicator}"

    relevant_terms = [
        "advertising",
        "ad network",
        "sponsored",
        "native ad",
        "monetize",
        "monetization",
        "revenue",
        "publisher",
        "cpc",
        "cpm",
        "impressions",
        "clicks",
        "outbrain",
        "revcontent",
        "mgid",
        "widget",
        "recommendation",
        "content discovery",
        "banner",
        "display",
        "campaign",
    ]
    context_count = sum(1 for term in relevant_terms if term in content)

    if context_count >= 3:
        return True, 0.85, f"Strong context ({context_count} relevant terms)"
    if context_count >= 2:
        return True, 0.65, f"Medium context ({context_count} relevant terms)"
    if context_count >= 1:
        return True, 0.45, f"Weak context ({context_count} relevant term)"

    relevant_subs = {
        "advertising",
        "adops",
        "marketing",
        "digital_marketing",
        "webdev",
        "web_design",
        "blogging",
        "contentcreation",
        "entrepreneur",
        "smallbusiness",
        "ppc",
        "seo",
    }
    if getattr(post, "subreddit", "").lower() in relevant_subs:
        return True, 0.6, f"Relevant subreddit: r/{post.subreddit}"

    if len(content) > 150:
        return True, 0.4, "Taboola mentioned with substantial content"

    return False, 0.2, "Insufficient relevance signals"


def select_comment_sample(
    comments: List[CommentT],
    max_samples: int,
) -> List[CommentT]:
    top_level = [comment for comment in comments if getattr(comment, "depth", 0) == 0]
    top_level.sort(key=lambda comment: getattr(comment, "score", 0), reverse=True)
    return top_level[:max_samples]


def parse_llm_json(raw_text: str) -> Dict[str, Any]:
    if not raw_text:
        return {}
    text = raw_text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            snippet = text[start : end + 1]
            try:
                return json.loads(snippet)
            except json.JSONDecodeError:
                return {}
    return {}


def serialize_post(
    post: PostT,
    comments: List[CommentT],
    llm_data: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "post": asdict(post),
        "llm_filter": llm_data,
        "comments": [asdict(comment) for comment in comments],
    }


class BaseIngestionAgent(Generic[PostT, CommentT]):
    def __init__(
        self,
        *,
        search_queries: Sequence[str],
        max_comment_sample: int,
        llm_min_relevance_score: float,
        quick_filter: Callable[[PostT], Tuple[bool, float, str]] = passes_quick_filter,
        item_label: str = "post",
        output_label: str = "",
    ) -> None:
        self.search_queries = list(search_queries)
        self.max_comment_sample = max_comment_sample
        self.llm_min_relevance_score = llm_min_relevance_score
        self.quick_filter = quick_filter
        self.item_label = item_label
        self.output_label = output_label

    def sample_comments(self, comments: List[CommentT]) -> List[CommentT]:
        return select_comment_sample(comments, self.max_comment_sample)

    def run_quick_filter(
        self,
        posts: Iterable[PostT],
        *,
        auto_accept_threshold: float = 0.8,
        on_reject: Optional[Callable[[PostT, str], None]] = None,
        on_auto_accept: Optional[Callable[[PostT, float, str], None]] = None,
        on_needs_llm: Optional[Callable[[PostT, float, str], None]] = None,
    ) -> Tuple[List[Tuple[PostT, str]], List[PostT], int]:
        high_confidence: List[Tuple[PostT, str]] = []
        needs_llm: List[PostT] = []
        rejected = 0

        for post in posts:
            should_process, confidence, reason = self.quick_filter(post)
            if not should_process:
                rejected += 1
                if on_reject:
                    on_reject(post, reason)
                continue

            if confidence >= auto_accept_threshold:
                high_confidence.append((post, reason))
                if on_auto_accept:
                    on_auto_accept(post, confidence, reason)
            else:
                needs_llm.append(post)
                if on_needs_llm:
                    on_needs_llm(post, confidence, reason)

        return high_confidence, needs_llm, rejected

    def build_auto_accept_metadata(
        self,
        post: PostT,
        filter_reason: str,
    ) -> Dict[str, Any]:
        content = f"{post.title}{post.selftext}".lower()
        return {
            "is_relevant": True,
            "mentions_taboola": True,
            "mentions_realize_product": "realize" in content,
            "relevance_score": 9.0,
            "raw_model_response": f"Auto-accepted by filter: {filter_reason}",
            "filter_auto_accepted": True,
        }

    def process_high_confidence_posts(
        self,
        high_confidence_posts: Sequence[Tuple[PostT, str]],
        fetch_comments: Callable[[str], List[CommentT]],
    ) -> List[Dict[str, Any]]:
        payloads: List[Dict[str, Any]] = []
        for post, filter_reason in high_confidence_posts:
            comments = fetch_comments(post.id)
            metadata = self.build_auto_accept_metadata(post, filter_reason)
            payloads.append(serialize_post(post, comments, metadata))
        return payloads

    def is_relevant_llm_result(self, llm_result: Dict[str, Any]) -> bool:
        return (
            bool(llm_result.get("is_relevant"))
            and bool(llm_result.get("mentions_taboola"))
            and float(llm_result.get("relevance_score", 0.0) or 0.0)
            >= self.llm_min_relevance_score
        )

    def run_llm_filter(
        self,
        post: PostT,
        comments: List[CommentT],
        llm_callable: Callable[[PostT, List[CommentT]], Dict[str, Any]],
    ) -> Tuple[bool, Dict[str, Any]]:
        comments_sample = self.sample_comments(comments)
        try:
            llm_result = llm_callable(post, comments_sample)
        except Exception as exc:
            logging.error(
                "LLM filter failed for %s %s: %s",
                self.item_label,
                getattr(post, "id", ""),
                exc,
            )
            llm_result = {
                **DEFAULT_LLM_RESULT,
                "raw_model_response": "",
                "error": str(exc),
            }

        is_relevant = self.is_relevant_llm_result(llm_result)
        return is_relevant, llm_result

    def process_posts_with_llm(
        self,
        posts: Sequence[PostT],
        fetch_comments: Callable[[str], List[CommentT]],
        llm_filter_fn: Callable[[PostT, List[CommentT]], Tuple[bool, Dict[str, Any]]],
        *,
        on_post_start: Optional[Callable[[int, int, PostT], None]] = None,
        on_llm_result: Optional[Callable[[PostT, Dict[str, Any]], None]] = None,
        on_rate_limit_pause: Optional[Callable[[int, int], None]] = None,
        rate_limit_every: int = 10,
        rate_limit_sleep: float = 3.0,
        suppress_exceptions: bool = False,
        on_exception: Optional[Callable[[PostT, Exception], None]] = None,
    ) -> List[Dict[str, Any]]:
        payloads: List[Dict[str, Any]] = []
        total = len(posts)

        for idx, post in enumerate(posts, 1):
            if on_post_start:
                on_post_start(idx, total, post)

            def _process() -> None:
                comments = fetch_comments(post.id)
                is_relevant, llm_metadata = llm_filter_fn(post, comments)
                if on_llm_result:
                    on_llm_result(post, llm_metadata)
                if is_relevant:
                    payloads.append(serialize_post(post, comments, llm_metadata))

            if suppress_exceptions:
                try:
                    _process()
                except Exception as exc:
                    if on_exception:
                        on_exception(post, exc)
                    continue
            else:
                _process()

            if (
                rate_limit_every
                and rate_limit_sleep > 0
                and idx % rate_limit_every == 0
                and idx < total
            ):
                if on_rate_limit_pause:
                    on_rate_limit_pause(idx, total)
                time.sleep(rate_limit_sleep)

        return payloads

    def write_output(
        self,
        output_path: str,
        posts_payload: List[Dict[str, Any]],
        max_posts_per_query: int,
    ) -> None:
        metadata = {
            "generated_at_utc": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
            "search_queries": self.search_queries,
            "max_posts_per_query": max_posts_per_query,
        }
        payload = {
            "metadata": metadata,
            "posts": posts_payload,
        }
        with open(output_path, "w", encoding="utf-8") as output_file:
            json.dump(payload, output_file, ensure_ascii=False, indent=2)

        if self.output_label:
            logging.info(
                "Wrote %d %s posts to %s",
                len(posts_payload),
                self.output_label,
                output_path,
            )
        else:
            logging.info("Wrote %d posts to %s", len(posts_payload), output_path)
