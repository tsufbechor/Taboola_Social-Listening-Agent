import argparse
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import requests
from base_ingestion_agent import (
    BaseIngestionAgent,
    parse_llm_json,
    passes_quick_filter as base_passes_quick_filter,
)
from sentiment_analysis.config import FILTER_SCHEMA


def _load_env_fallback(env_path: Path) -> None:
    """
    Minimal .env loader so we can read API keys without python-dotenv.
    Only fills keys that are not already present in os.environ.
    """
    try:
        with env_path.open("r", encoding="utf-8") as env_file:
            for raw_line in env_file:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except OSError as exc:
        logging.warning("Failed to read %s: %s", env_path, exc)


def _ensure_env_loaded() -> None:
    """
    Load environment variables from a local .env file before configuring constants.
    """
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        _load_env_fallback(env_path)
        return
    load_dotenv(dotenv_path=env_path)


_ensure_env_loaded()

# -----------------------------
# Configuration / Constants
# -----------------------------

SEARCH_QUERIES = [
    "Taboola",
    "Taboola Realize",
]

HN_USER_AGENT = os.environ.get(
    "HN_USER_AGENT",
    "social-listening-hn-bot/0.1 by taboola_assignment"
)

REQUEST_SLEEP_SECONDS = 1.0
DEFAULT_TIMEOUT = 20
MAX_COMMENT_SAMPLE = 5
LLM_MIN_RELEVANCE_SCORE = 7.0
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_CHAT_COMPLETIONS_URL = os.environ.get(
    "OPENAI_CHAT_COMPLETIONS_URL",
    "https://api.openai.com/v1/chat/completions",
)
MAX_COMMENTS_PER_STORY = int(os.environ.get("HN_MAX_COMMENTS_PER_STORY", "10"))
MAX_COMMENT_DEPTH = int(os.environ.get("HN_MAX_COMMENT_DEPTH", "0"))

# Hacker News APIs
HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
HN_ITEM_API = "https://hacker-news.firebaseio.com/v0/item/{id}.json"
HN_PERMALINK_TEMPLATE = "https://news.ycombinator.com/item?id={id}"


# -----------------------------
# Dataclasses
# -----------------------------

@dataclass
class HackerNewsPost:
    """
    Intentionally uses the SAME field names as RedditPost so that
    the JSON schema matches reddit_filtered.json exactly.
    """
    id: str
    subreddit: str  # will be set to "hackernews"
    title: str
    selftext: str   # story text (if any)
    author: Optional[str]
    url: str
    permalink: str
    created_utc: int
    score: int
    num_comments: int
    over_18: bool
    is_self: bool


@dataclass
class HackerNewsComment:
    """
    Same shape as RedditComment so downstream processing is identical.
    """
    id: str
    post_id: str
    parent_id: Optional[str]
    author: Optional[str]
    body: str
    created_utc: int
    score: int
    depth: int


BASE_AGENT: BaseIngestionAgent[HackerNewsPost, HackerNewsComment] = BaseIngestionAgent(
    search_queries=SEARCH_QUERIES,
    max_comment_sample=MAX_COMMENT_SAMPLE,
    llm_min_relevance_score=LLM_MIN_RELEVANCE_SCORE,
    quick_filter=base_passes_quick_filter,
    item_label="HN story",
    output_label="HN",
)


# -----------------------------
# Utility helpers
# -----------------------------

def _safe_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def build_hn_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": HN_USER_AGENT})
    return session


# -----------------------------
# Fetching Hacker News posts
# -----------------------------

def fetch_hn_posts_for_query(
    query: str,
    max_posts: int,
    session: requests.Session,
) -> List[HackerNewsPost]:
    """
    Fetch Hacker News posts (stories) matching a query using the Algolia HN search API.

    We return a list of HackerNewsPost objects (same field names as RedditPost).
    """
    posts: List[HackerNewsPost] = []
    seen_ids: Set[str] = set()

    page = 0
    hits_per_page = min(100, max_posts)

    while len(posts) < max_posts:
        params = {
            "query": query,
            "tags": "story",
            "hitsPerPage": hits_per_page,
            "page": page,
        }

        try:
            response = session.get(HN_SEARCH_URL, params=params, timeout=DEFAULT_TIMEOUT)
        except requests.RequestException as exc:
            logging.warning("HN search request failed for '%s': %s", query, exc)
            break
        finally:
            time.sleep(REQUEST_SLEEP_SECONDS)

        if response.status_code != 200:
            logging.warning(
                "HN search returned status %s for query '%s'",
                response.status_code,
                query,
            )
            break

        try:
            payload = response.json()
        except ValueError:
            logging.warning("Invalid JSON from HN search for query '%s'", query)
            break

        hits = payload.get("hits", [])
        if not hits:
            logging.info("No more HN hits for query '%s' after %d posts", query, len(posts))
            break

        for hit in hits:
            object_id = hit.get("objectID")
            if not object_id or object_id in seen_ids:
                continue

            title = hit.get("title") or ""
            story_text = hit.get("story_text") or ""
            url = hit.get("url") or ""

            # Optional: ensure query appears somewhere in title/body/url
            lower_query = query.lower()
            combined = f"{title} {story_text} {url}".lower()
            if lower_query not in combined:
                # Keep this conservative / consistent with Reddit logic
                continue

            created_at_i = _safe_int(hit.get("created_at_i"))
            points = _safe_int(hit.get("points"))
            num_comments = _safe_int(hit.get("num_comments"))

            permalink = HN_PERMALINK_TEMPLATE.format(id=object_id)

            post = HackerNewsPost(
                id=str(object_id),
                subreddit="hackernews",  # fake subreddit field for schema compatibility
                title=title,
                selftext=story_text,
                author=hit.get("author"),
                url=url,
                permalink=permalink,
                created_utc=created_at_i,
                score=points,
                num_comments=num_comments,
                over_18=False,  # HN has no over_18, so always False
                is_self=not bool(url),  # treat stories without external URL as "self"
            )

            posts.append(post)
            seen_ids.add(object_id)

            if len(posts) >= max_posts:
                break

        page += 1
        if page >= (payload.get("nbPages") or 0):
            break

    logging.info("HN query '%s' returned %d posts", query, len(posts))
    return posts


# -----------------------------
# Fetching Hacker News comments
# -----------------------------

def fetch_hn_comments(
    story_id: str,
    session: requests.Session,
    max_depth: int = MAX_COMMENT_DEPTH,
    max_comments: int = MAX_COMMENTS_PER_STORY,
) -> List[HackerNewsComment]:
    """
    Fetch top-level comments (and some nested replies) for a HN story via Firebase API.
    """
    root_url = HN_ITEM_API.format(id=story_id)
    try:
        response = session.get(root_url, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as exc:
        logging.warning("Failed to fetch HN story %s: %s", story_id, exc)
        return []
    finally:
        time.sleep(REQUEST_SLEEP_SECONDS)

    if response.status_code != 200:
        logging.warning(
            "Non-200 from HN item API for story %s: %s",
            story_id,
            response.status_code,
        )
        return []

    try:
        story_payload = response.json()
    except ValueError:
        logging.warning("Invalid JSON from HN item API for story %s", story_id)
        return []

    kids = story_payload.get("kids") or []
    collected: List[HackerNewsComment] = []

    for kid_id in kids:
        if len(collected) >= max_comments:
            break
        collected.extend(
            _fetch_hn_comment_recursive(
                comment_id=kid_id,
                post_id=story_id,
                depth=0,
                session=session,
                max_depth=max_depth,
            )
        )
        if len(collected) >= max_comments:
            break

    return collected


def _fetch_hn_comment_recursive(
    comment_id: int,
    post_id: str,
    depth: int,
    session: requests.Session,
    max_depth: int,
) -> List[HackerNewsComment]:
    if depth > max_depth:
        return []

    url = HN_ITEM_API.format(id=comment_id)
    try:
        response = session.get(url, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as exc:
        logging.warning("Failed to fetch HN comment %s: %s", comment_id, exc)
        return []
    finally:
        time.sleep(REQUEST_SLEEP_SECONDS)

    if response.status_code != 200:
        logging.warning(
            "Non-200 from HN item API for comment %s: %s",
            comment_id,
            response.status_code,
        )
        return []

    try:
        payload = response.json()
    except ValueError:
        logging.warning("Invalid JSON for HN comment %s", comment_id)
        return []

    if not payload or payload.get("deleted") or payload.get("dead"):
        return []

    text = payload.get("text") or ""
    author = payload.get("by")
    created_utc = _safe_int(payload.get("time"))
    score = _safe_int(payload.get("score"))
    parent_id = payload.get("parent")

    comment = HackerNewsComment(
        id=str(payload.get("id")),
        post_id=str(post_id),
        parent_id=str(parent_id) if parent_id is not None else None,
        author=author,
        body=text,
        created_utc=created_utc,
        score=score,
        depth=depth,
    )

    collected: List[HackerNewsComment] = [comment]

    kids = payload.get("kids") or []
    for kid in kids:
        collected.extend(
            _fetch_hn_comment_recursive(
                comment_id=kid,
                post_id=post_id,
                depth=depth + 1,
                session=session,
                max_depth=max_depth,
            )
        )

    return collected


# -----------------------------
# Filtering logic (reused)
# -----------------------------

def passes_quick_filter(post: HackerNewsPost) -> Tuple[bool, float, str]:
    return base_passes_quick_filter(post)


# -----------------------------
# LLM filter (OpenAI)
# -----------------------------

def build_llm_prompt(post: HackerNewsPost, comments_sample: List[HackerNewsComment]) -> str:
    
    
    lines = [
        "You are a semantic filter that determines if content is about Taboola, the advertising company/platform.",
        "Rules:",
        "1. Confirm the post chiefly revolves around Taboola; brief or passing mentions must be rejected.",
        "2. Only treat 'Realize' as Taboola's product when it is explicitly described as such.",
        "3. Ignore generic uses of the verb 'realize'.",
        "4. Be conservative; if unsure, mark the content as not relevant.",
        "",
        f"Subreddit: {post.subreddit}",
        f"Post Title: {post.title}",
        f"Post Body: {post.selftext or '(empty)'}",
    ]
    if comments_sample:
        lines.append("")
        lines.append("Sampled top comments:")
        for idx, comment in enumerate(comments_sample, start=1):
            sanitized = comment.body.replace("\n", " ").strip()
            lines.append(f"{idx}. {sanitized}")
    
    lines.append("")
    lines.append("Return JSON matching this exact schema:")
    lines.append(json.dumps(FILTER_SCHEMA, indent=2))
    
    return "\n".join(lines)

def call_openai_filter(
    post: HackerNewsPost,
    comments_sample: List[HackerNewsComment],
) -> Dict[str, Any]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")

    prompt = build_llm_prompt(post, comments_sample)
    system_message = (
        "You are a semantic filter that determines if Hacker News content is about "
        "Taboola and its Realize product. Respond ONLY with JSON containing the keys "
        "is_relevant, mentions_taboola, mentions_realize_product, relevance_score."
    )
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_completion_tokens": 300,
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    max_retries = 3
    retry_delay = 2.0
    max_delay = 30.0
    retryable_status = {429, 500, 502, 503, 504}

    for attempt in range(max_retries):
        try:
            logging.debug(
                "[HN] Calling OpenAI for story %s (attempt %d/%d, timeout=%s)",
                post.id,
                attempt + 1,
                max_retries,
                DEFAULT_TIMEOUT,
            )
            start_time = time.time()
            response = requests.post(
                OPENAI_CHAT_COMPLETIONS_URL,
                headers=headers,
                json=payload,
                timeout=DEFAULT_TIMEOUT,
            )
            elapsed = time.time() - start_time
            logging.debug(
                "[HN] OpenAI response for story %s (attempt %d/%d) status=%s took %.2fs",
                post.id,
                attempt + 1,
                max_retries,
                response.status_code,
                elapsed,
            )

            if response.status_code == 200:
                if attempt > 0:
                    logging.info(
                        "[HN] OpenAI request succeeded on attempt %d",
                        attempt + 1,
                    )
                try:
                    response_payload = response.json()
                except ValueError as exc:
                    raise RuntimeError(f"Invalid JSON from OpenAI: {exc}") from exc
                choices = response_payload.get("choices") or []
                raw_text = ""
                if choices:
                    message = choices[0].get("message") or {}
                    raw_text = (message.get("content") or "").strip()

                parsed = parse_llm_json(raw_text)
                return {
                    "is_relevant": bool(parsed.get("is_relevant", False)),
                    "mentions_taboola": bool(parsed.get("mentions_taboola", False)),
                    "mentions_realize_product": bool(
                        parsed.get("mentions_realize_product", False)
                    ),
                    "relevance_score": float(parsed.get("relevance_score", 0.0) or 0.0),
                    "raw_model_response": raw_text,
                }

            error_msg = (
                f"OpenAI returned status {response.status_code}: "
                f"{response.text[:200]}"
            )
            if response.status_code in retryable_status and attempt < max_retries - 1:
                actual_delay = min(retry_delay, max_delay)
                logging.warning(
                    "[HN] %s. Retrying in %.1fs (attempt %d/%d)",
                    error_msg,
                    actual_delay,
                    attempt + 1,
                    max_retries,
                )
                time.sleep(actual_delay)
                retry_delay = min(retry_delay * 2, max_delay)
                continue

            logging.error(
                "[HN] Non-retryable OpenAI error for story %s: %s",
                post.id,
                error_msg,
            )
            raise RuntimeError(error_msg)

        except requests.Timeout:
            if attempt < max_retries - 1:
                logging.warning(
                    "[HN] Timeout for story %s. Retrying in %.1fs",
                    post.id,
                    retry_delay,
                )
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)
            else:
                logging.error(
                    "[HN] Max retries reached for story %s due to timeouts",
                    post.id,
                )
                raise RuntimeError("Request timeout after max retries")

        except requests.RequestException as exc:
            if attempt < max_retries - 1:
                logging.warning(
                    "[HN] Network error for story %s: %s. Retrying in %.1fs",
                    post.id,
                    exc,
                    retry_delay,
                )
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, max_delay)
            else:
                logging.error(
                    "[HN] Max retries reached for story %s: %s",
                    post.id,
                    exc,
                )
                raise RuntimeError(f"Network error after max retries: {exc}")
        except RuntimeError:
            raise
        except Exception as exc:
            logging.error(
                "[HN] Unexpected error while calling OpenAI for story %s: %s",
                post.id,
                exc,
            )
            raise RuntimeError(f"Unexpected error calling OpenAI: {exc}") from exc

    raise RuntimeError(f"Failed to process HN story {post.id} after {max_retries} attempts")


def passes_llm_filter(
    post: HackerNewsPost,
    comments: List[HackerNewsComment],
) -> Tuple[bool, Dict[str, Any]]:
    return BASE_AGENT.run_llm_filter(post, comments, call_openai_filter)


# -----------------------------
# Serialization / Output
# -----------------------------

# -----------------------------
# CLI / Main
# -----------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hacker News ingestion agent for Taboola social listening."
    )
    parser.add_argument(
        "--output-path",
        default="hacker_news_filtered.json",
        help="Destination JSON filepath.",
    )
    parser.add_argument(
        "--max-posts-per-query",
        type=int,
        default=200,
        help="Maximum number of posts to fetch per search query.",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    args = parse_args()
    posts_payload: List[Dict[str, Any]] = []

    try:
        with build_hn_session() as session:
            post_cache: Dict[str, HackerNewsPost] = {}
    
            # 1) Fetch posts for all queries
            for query in SEARCH_QUERIES:
                logging.info("Fetching HN posts for query '%s'", query)
                query_posts = fetch_hn_posts_for_query(
                    query,
                    args.max_posts_per_query,
                    session,
                )
                for post in query_posts:
                    post_cache[post.id] = post
    
            logging.info("Total unique HN posts collected: %d", len(post_cache))
    
            # 2) Quick filter
            logging.info("=" * 60)
            logging.info("Stage 1 (HN): Quick filtering all posts...")
    
            high_confidence_posts, needs_llm_posts, rejected_count = BASE_AGENT.run_quick_filter(
                post_cache.values(),
                on_reject=lambda post, reason: logging.debug(
                    "✗ Rejected HN story %s: %s", post.id, reason
                ),
                on_auto_accept=lambda post, confidence, reason: logging.info(
                    "✓ Auto-accept HN story %s (conf=%.2f): %s",
                    post.id,
                    confidence,
                    reason,
                ),
                on_needs_llm=lambda post, confidence, reason: logging.info(
                    "? Needs LLM HN story %s (conf=%.2f): %s",
                    post.id,
                    confidence,
                    reason,
                ),
            )
    
            logging.info("=" * 60)
            logging.info("HN Filtering Results:")
            logging.info("  Total posts: %d", len(post_cache))
            logging.info("  ✗ Rejected: %d", rejected_count)
            logging.info("  ✓ Auto-accepted (high confidence): %d", len(high_confidence_posts))
            logging.info("  ? Needs LLM verification: %d", len(needs_llm_posts))
            if post_cache:
                llm_reduction = (1 - len(needs_llm_posts) / max(1, len(post_cache))) * 100
                logging.info("  📊 LLM calls reduced by: %.1f%%", llm_reduction)
            logging.info("=" * 60)
    
            # 3) High-confidence posts (no LLM)
            logging.info(
                "Stage 2 (HN): Processing %d high-confidence posts (no LLM)...",
                len(high_confidence_posts),
            )
            high_conf_payloads = BASE_AGENT.process_high_confidence_posts(
                high_confidence_posts,
                lambda post_id: fetch_hn_comments(post_id, session),
            )
            posts_payload.extend(high_conf_payloads)

            logging.info("\u2713 Processed %d high-confidence HN posts", len(high_confidence_posts))

            logging.info(
                "Stage 3 (HN): Processing %d posts with LLM...",
                len(needs_llm_posts),
            )

            def _fetch_comments_with_logging(post_id: str) -> List[HackerNewsComment]:
                logging.info(
                    "HN: fetching comments for story %s (limit=%d, depth=%d)",
                    post_id,
                    MAX_COMMENTS_PER_STORY,
                    MAX_COMMENT_DEPTH,
                )
                comments = fetch_hn_comments(post_id, session)
                logging.info(
                    "HN: fetched %d comments for story %s", len(comments), post_id
                )
                return comments

            def _passes_llm_filter_with_logging(
                post: HackerNewsPost, comments: List[HackerNewsComment]
            ) -> Tuple[bool, Dict[str, Any]]:
                logging.info("HN: calling LLM filter for story %s", post.id)
                result = passes_llm_filter(post, comments)
                logging.info("HN: finished LLM filter for story %s", post.id)
                return result

            llm_payloads = BASE_AGENT.process_posts_with_llm(
                needs_llm_posts,
                fetch_comments=_fetch_comments_with_logging,
                llm_filter_fn=_passes_llm_filter_with_logging,
                on_post_start=lambda idx, total, post: logging.info(
                    "Processing HN %d/%d: story %s",
                    idx,
                    total,
                    post.id,
                ),
                on_llm_result=lambda post, llm_metadata: logging.info(
                    "LLM filter (HN): story %s -> is_relevant=%s, score=%s",
                    post.id,
                    llm_metadata.get("is_relevant"),
                    llm_metadata.get("relevance_score"),
                ),
                on_rate_limit_pause=lambda idx, total: logging.info(
                    "HN: Pausing 3 seconds to avoid rate limits..."
                ),
                suppress_exceptions=True,
                on_exception=lambda post, exc: logging.error(
                    "HN: fatal error processing story %s in Stage 3: %s",
                    post.id,
                    exc,
                ),
            )
            posts_payload.extend(llm_payloads)
    
            logging.info("=" * 60)
            logging.info("✓ HN Finished! Total relevant posts: %d", len(posts_payload))
            logging.info("=" * 60)
    
    except Exception as e:
        logging.error("HN ingestion failed with an unexpected error: %s", e)

    BASE_AGENT.write_output(args.output_path, posts_payload, args.max_posts_per_query)


if __name__ == "__main__":
    main()


