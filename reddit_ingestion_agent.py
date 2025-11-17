import argparse
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qs, urlsplit
import requests
from bs4 import BeautifulSoup
from base_ingestion_agent import (
    BaseIngestionAgent,
    parse_llm_json,
    passes_quick_filter as base_passes_quick_filter,
)
from sentiment_analysis.config import FILTER_SCHEMA


SEARCH_QUERIES = [
    "Taboola",
    "Taboola Realize",
]
USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "social-listening-bot/0.1 by taboola_assignment")
REQUEST_SLEEP_SECONDS = 1.0
DEFAULT_TIMEOUT = 20
MAX_COMMENT_SAMPLE = 5
LLM_MIN_RELEVANCE_SCORE = 7.0
GOOGLE_RESULT_LIMIT = 50
GOOGLE_RESULT_THRESHOLD = 65
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_ENDPOINT_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"



@dataclass
class RedditPost:
    id: str
    subreddit: str
    title: str
    selftext: str
    author: Optional[str]
    url: str
    permalink: str
    created_utc: int
    score: int
    num_comments: int
    over_18: bool
    is_self: bool


@dataclass
class RedditComment:
    id: str
    post_id: str
    parent_id: Optional[str]
    author: Optional[str]
    body: str
    created_utc: int
    score: int
    depth: int


BASE_AGENT: BaseIngestionAgent[RedditPost, RedditComment] = BaseIngestionAgent(
    search_queries=SEARCH_QUERIES,
    max_comment_sample=MAX_COMMENT_SAMPLE,
    llm_min_relevance_score=LLM_MIN_RELEVANCE_SCORE,
    quick_filter=base_passes_quick_filter,
    item_label="post",
)


def _safe_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def build_reddit_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def fetch_global_search_posts(query: str, max_posts: int, session: requests.Session) -> List[RedditPost]:
    """
    IMPROVED: Fetch posts using multiple strategies to maximize results.
    
    Changes from original:
    - Removed 'type: link' filter to include self-posts
    - Changed time filter from 'month' to 'all'
    - Added multiple search strategies
    - Better verification that query appears in title/body
    """
    posts: List[RedditPost] = []
    seen_ids: Set[str] = set()
    
    # Strategy 1: Basic global search (NO type filter)
    posts_basic = _fetch_reddit_basic_search(query, max_posts, session, seen_ids)
    posts.extend(posts_basic)
    logging.info(f"Basic search found {len(posts_basic)} posts for '{query}'")
    
    # Strategy 2: Title-specific search
    if len(posts) < max_posts:
        remaining = max_posts - len(posts)
        posts_title = _fetch_reddit_title_search(query, remaining, session, seen_ids)
        posts.extend(posts_title)
        logging.info(f"Title search found {len(posts_title)} additional posts for '{query}'")
    
    # Strategy 3: Search specific relevant subreddits
    if len(posts) < max_posts:
        remaining = max_posts - len(posts)
        relevant_subs = [
            'advertising', 'adops', 'marketing', 'PPC', 'webdev',
            'startups', 'business', 'SEO', 'digital_marketing', 'entrepreneur'
        ]
        posts_subs = _fetch_from_subreddits(query, relevant_subs, remaining, session, seen_ids)
        posts.extend(posts_subs)
        logging.info(f"Subreddit search found {len(posts_subs)} additional posts for '{query}'")
    
    return posts


def _fetch_reddit_basic_search(query: str, max_posts: int, session: requests.Session, seen_ids: Set[str]) -> List[RedditPost]:
    """Basic Reddit search - NO type filter to get all posts"""
    posts: List[RedditPost] = []
    after: Optional[str] = None
    url = "https://www.reddit.com/search.json"
    
    attempts = 0
    max_attempts = 10
    
    while len(posts) < max_posts and attempts < max_attempts:
        attempts += 1
        
        params = {
            "q": query,
            "sort": "relevance",
            "t": "all",  # CHANGED from "month" to "all"
            "limit": min(100, max_posts - len(posts)),
            # REMOVED: "type": "link" - this was excluding self-posts!
        }
        if after:
            params["after"] = after

        try:
            response = session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        except requests.RequestException as exc:
            logging.warning("Request failed for query '%s': %s", query, exc)
            break
        finally:
            time.sleep(REQUEST_SLEEP_SECONDS)

        if response.status_code != 200:
            logging.warning("Received status %s for query '%s'", response.status_code, query)
            break

        try:
            payload = response.json()
        except ValueError:
            logging.warning("Invalid JSON for query '%s'", query)
            break

        children = payload.get("data", {}).get("children", [])
        if not children:
            logging.info(f"No more results after {len(posts)} posts")
            break

        for child in children:
            if child.get("kind") != "t3":
                continue
            data = child.get("data", {})
            post_id = data.get("id")
            if not post_id or post_id in seen_ids:
                continue
            
            # IMPROVED: Verify query actually appears in title or body
            title = (data.get("title", "") or "").lower()
            selftext = (data.get("selftext", "") or "").lower()
            query_lower = query.lower()
            
            if query_lower not in title and query_lower not in selftext:
                continue
            
            post = RedditPost(
                id=post_id,
                subreddit=data.get("subreddit", "") or "",
                title=data.get("title", "") or "",
                selftext=data.get("selftext", "") or "",
                author=data.get("author"),
                url=data.get("url", "") or "",
                permalink=data.get("permalink", "") or "",
                created_utc=_safe_int(data.get("created_utc")),
                score=_safe_int(data.get("score")),
                num_comments=_safe_int(data.get("num_comments")),
                over_18=bool(data.get("over_18", False)),
                is_self=bool(data.get("is_self", False)),
            )
            posts.append(post)
            seen_ids.add(post_id)
            if len(posts) >= max_posts:
                break

        after = payload.get("data", {}).get("after")
        if not after:
            logging.info(f"No more pages available after {attempts} requests")
            break

    return posts


def _fetch_reddit_title_search(query: str, max_posts: int, session: requests.Session, seen_ids: Set[str]) -> List[RedditPost]:
    """Search specifically in titles using title: prefix"""
    posts: List[RedditPost] = []
    after: Optional[str] = None
    url = "https://www.reddit.com/search.json"
    
    search_query = f"title:{query}"
    
    while len(posts) < max_posts:
        params = {
            "q": search_query,
            "sort": "relevance",
            "t": "all",
            "limit": 100,
        }
        if after:
            params["after"] = after

        try:
            response = session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            time.sleep(REQUEST_SLEEP_SECONDS)
            
            if response.status_code != 200:
                break
            
            payload = response.json()
            children = payload.get("data", {}).get("children", [])
            
            if not children:
                break

            for child in children:
                if child.get("kind") != "t3":
                    continue
                data = child.get("data", {})
                post_id = data.get("id")
                if not post_id or post_id in seen_ids:
                    continue
                
                post = RedditPost(
                    id=post_id,
                    subreddit=data.get("subreddit", "") or "",
                    title=data.get("title", "") or "",
                    selftext=data.get("selftext", "") or "",
                    author=data.get("author"),
                    url=data.get("url", "") or "",
                    permalink=data.get("permalink", "") or "",
                    created_utc=_safe_int(data.get("created_utc")),
                    score=_safe_int(data.get("score")),
                    num_comments=_safe_int(data.get("num_comments")),
                    over_18=bool(data.get("over_18", False)),
                    is_self=bool(data.get("is_self", False)),
                )
                posts.append(post)
                seen_ids.add(post_id)
                if len(posts) >= max_posts:
                    break

            after = payload.get("data", {}).get("after")
            if not after:
                break
                
        except Exception as e:
            logging.error(f"Error in title search: {e}")
            break

    return posts


def _fetch_from_subreddits(query: str, subreddits: List[str], max_posts: int, session: requests.Session, seen_ids: Set[str]) -> List[RedditPost]:
    """Search specific subreddits for the query"""
    posts: List[RedditPost] = []
    posts_per_sub = max(5, max_posts // len(subreddits))
    
    for subreddit in subreddits:
        if len(posts) >= max_posts:
            break
        
        url = f"https://www.reddit.com/r/{subreddit}/search.json"
        params = {
            "q": query,
            "restrict_sr": "true",
            "sort": "relevance",
            "t": "all",
            "limit": 100,
        }
        
        try:
            response = session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
            time.sleep(REQUEST_SLEEP_SECONDS)
            
            if response.status_code != 200:
                continue
            
            payload = response.json()
            children = payload.get("data", {}).get("children", [])
            
            sub_count = 0
            for child in children:
                if child.get("kind") != "t3":
                    continue
                data = child.get("data", {})
                post_id = data.get("id")
                if not post_id or post_id in seen_ids:
                    continue
                
                # Verify query is in title or body
                title = (data.get("title", "") or "").lower()
                selftext = (data.get("selftext", "") or "").lower()
                if query.lower() not in title and query.lower() not in selftext:
                    continue
                
                post = RedditPost(
                    id=post_id,
                    subreddit=data.get("subreddit", "") or "",
                    title=data.get("title", "") or "",
                    selftext=data.get("selftext", "") or "",
                    author=data.get("author"),
                    url=data.get("url", "") or "",
                    permalink=data.get("permalink", "") or "",
                    created_utc=_safe_int(data.get("created_utc")),
                    score=_safe_int(data.get("score")),
                    num_comments=_safe_int(data.get("num_comments")),
                    over_18=bool(data.get("over_18", False)),
                    is_self=bool(data.get("is_self", False)),
                )
                posts.append(post)
                seen_ids.add(post_id)
                sub_count += 1
                
                if sub_count >= posts_per_sub or len(posts) >= max_posts:
                    break
                    
        except Exception as e:
            logging.warning(f"Error searching r/{subreddit}: {e}")
            continue
    
    return posts


def _extract_google_result_url(raw_href: Optional[str]) -> Optional[str]:
    if not raw_href:
        return None
    if raw_href.startswith("/url?") or raw_href.startswith("https://www.google.com/url?"):
        parsed = urlsplit(raw_href)
        params = parse_qs(parsed.query)
        targets = params.get("q")
        if targets:
            return targets[0]
        return None
    if raw_href.startswith("http"):
        return raw_href
    return None


def _extract_post_id_from_url(url: str) -> Optional[str]:
    if not url:
        return None
    parsed = urlsplit(url)
    path_parts = [segment for segment in parsed.path.split("/") if segment]
    for idx, segment in enumerate(path_parts):
        if segment == "comments" and idx + 1 < len(path_parts):
            post_id = path_parts[idx + 1]
            if post_id:
                return post_id
    return None


def fetch_post_by_id(post_id: str, session: requests.Session) -> Optional[RedditPost]:
    url = "https://www.reddit.com/api/info.json"
    params = {"id": f"t3_{post_id}"}
    try:
        response = session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as exc:
        logging.warning("Failed to fetch post %s via API: %s", post_id, exc)
        return None
    finally:
        time.sleep(REQUEST_SLEEP_SECONDS)

    if response.status_code != 200:
        logging.warning("Non-200 from Reddit info API for %s: %s", post_id, response.status_code)
        return None

    try:
        payload = response.json()
    except ValueError:
        logging.warning("Invalid JSON from info API for %s", post_id)
        return None

    children = payload.get("data", {}).get("children", [])
    for child in children:
        if child.get("kind") != "t3":
            continue
        data = child.get("data", {})
        return RedditPost(
            id=data.get("id", "") or "",
            subreddit=data.get("subreddit", "") or "",
            title=data.get("title", "") or "",
            selftext=data.get("selftext", "") or "",
            author=data.get("author"),
            url=data.get("url", "") or "",
            permalink=data.get("permalink", "") or "",
            created_utc=_safe_int(data.get("created_utc")),
            score=_safe_int(data.get("score")),
            num_comments=_safe_int(data.get("num_comments")),
            over_18=bool(data.get("over_18", False)),
            is_self=bool(data.get("is_self", False)),
        )
    return None


def fetch_additional_posts_duck_duck_go(
    query: str,
    session: requests.Session,
    existing_ids: Set[str],
    max_needed: int,
) -> List[RedditPost]:
    """
    Use DuckDuckGo instead of Google to avoid anti-bot measures.
    DuckDuckGo has simpler HTML and no JavaScript requirements.
    """
    if max_needed <= 0:
        return []
    
    # Use a separate session with better headers
    search_session = requests.Session()
    search_session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    # Try multiple search query variations
    search_queries = [
        f"{query} reddit",
        f"site:reddit.com {query}",
        f"reddit.com {query}",
    ]
    
    candidate_urls: Set[str] = set()
    
    for search_query in search_queries:
        if len(candidate_urls) >= max_needed * 2:  # Get more candidates than needed
            break
        
        try:
            # Use DuckDuckGo HTML search (no JavaScript needed)
            response = search_session.get(
                "https://html.duckduckgo.com/html/",
                params={
                    "q": search_query,
                    "t": "m",  # past month
                },
                timeout=DEFAULT_TIMEOUT
            )
            time.sleep(2)  # Be polite
            
            if response.status_code != 200:
                logging.warning(f"DuckDuckGo search status {response.status_code} for query: {search_query}")
                continue
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # DuckDuckGo uses simpler selectors
            for result in soup.select("a.result__a"):
                href = result.get("href")
                if href and "reddit.com" in href and "/comments/" in href:
                    candidate_urls.add(href)
            
            # Also try alternative selectors
            for link in soup.select("a[href*='reddit.com']"):
                href = link.get("href")
                if href and "/comments/" in href:
                    candidate_urls.add(href)
            
            logging.info(f"Found {len(candidate_urls)} URLs so far from query: {search_query}")
            
        except Exception as e:
            logging.error(f"Search failed for '{search_query}': {e}")
            continue
    
    if not candidate_urls:
        logging.warning(f"Search yielded no candidate URLs for query '{query}'")
        return []
    
    logging.info(f"Total candidate URLs found: {len(candidate_urls)}")
    
    # Extract posts from URLs
    posts = []
    for url in list(candidate_urls)[:max_needed * 3]:  # Try more URLs than needed
        if len(posts) >= max_needed:
            break
        
        post_id = _extract_post_id_from_url(url)
        if not post_id or post_id in existing_ids:
            continue
        
        post = fetch_post_by_id(post_id, session)
        if post:
            posts.append(post)
            existing_ids.add(post_id)
    
    logging.info(f"Successfully fetched {len(posts)} posts from search for query '{query}'")
    return posts


def passes_quick_filter(post: RedditPost) -> Tuple[bool, float, str]:
    return base_passes_quick_filter(post)


def fetch_post_comments(post_id: str, session: requests.Session) -> List[RedditComment]:
    url = f"https://www.reddit.com/comments/{post_id}.json"
    params = {"limit": 100, "depth": 4}
    try:
        response = session.get(url, params=params, timeout=DEFAULT_TIMEOUT)
    except requests.RequestException as exc:
        logging.warning("Failed to fetch comments for %s: %s", post_id, exc)
        return []
    finally:
        time.sleep(REQUEST_SLEEP_SECONDS)

    if response.status_code != 200:
        logging.warning("Non-200 from comments API for %s: %s", post_id, response.status_code)
        return []

    try:
        payload = response.json()
    except ValueError:
        logging.warning("Invalid JSON for comments of %s", post_id)
        return []

    if not isinstance(payload, list) or len(payload) < 2:
        return []

    comments_listing = payload[1]
    if not isinstance(comments_listing, dict):
        return []

    data = comments_listing.get("data", {})
    children = data.get("children", [])
    collected: List[RedditComment] = []
    for child in children:
        collected.extend(_extract_comments_recursive(child, post_id, 0))

    return collected


def _extract_comments_recursive(item: Dict[str, Any], post_id: str, depth: int) -> List[RedditComment]:
    collected: List[RedditComment] = []
    if not isinstance(item, dict):
        return collected

    kind = item.get("kind", "")
    data = item.get("data", {})

    if kind == "t1":
        comment_id = data.get("id")
        if comment_id:
            comment = RedditComment(
                id=comment_id,
                post_id=post_id,
                parent_id=data.get("parent_id"),
                author=data.get("author"),
                body=data.get("body", "") or "",
                created_utc=_safe_int(data.get("created_utc")),
                score=_safe_int(data.get("score")),
                depth=depth,
            )
            collected.append(comment)

            replies = data.get("replies")
            if isinstance(replies, dict) and depth < 4:
                reply_children = replies.get("data", {}).get("children", [])
                for reply in reply_children:
                    collected.extend(_extract_comments_recursive(reply, post_id, depth + 1))

    elif kind == "more":
        pass

    else:
        replies = data.get("replies")
        if isinstance(replies, dict) and depth < 4:
            reply_children = replies.get("data", {}).get("children", [])
            for reply in reply_children:
                collected.extend(_extract_comments_recursive(reply, post_id, depth + 1))

    return collected


def build_llm_prompt(post: RedditPost, comments_sample: List[RedditComment]) -> str:
       
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


def call_gemini_filter(post: RedditPost, comments_sample: List[RedditComment]) -> Dict[str, Any]:
    """
    IMPROVED: Call Gemini API with exponential backoff retry logic.
    Handles 503 (overloaded), 429 (rate limit), and network errors.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set")

    prompt = build_llm_prompt(post, comments_sample)
    endpoint = GEMINI_ENDPOINT_TEMPLATE.format(model=GEMINI_MODEL)
    
    max_retries = 5
    retry_delay = 2.0  # Start with 2 seconds
    max_delay = 60.0
    
    for attempt in range(max_retries):
        try:
            # Add small delay between requests to avoid rate limiting
            if attempt > 0:
                time.sleep(1)
            
            payload = {
                "contents": [
                    {
                        "parts": [{"text": prompt}],
                    }
                ],
                "generationConfig": {
                    "temperature": 0.0,
                    "responseMimeType": "application/json",
                },
            }
            
            response = requests.post(
                endpoint,
                params={"key": api_key},
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=DEFAULT_TIMEOUT,
            )
            
            # Success!
            if response.status_code == 200:
                if attempt > 0:
                    logging.info(f"✓ Gemini request succeeded on attempt {attempt + 1}")
                
                response_payload = response.json()
                raw_text = _extract_text_from_gemini_response(response_payload).strip()
                parsed = parse_llm_json(raw_text)
                
                return {
                    "is_relevant": bool(parsed.get("is_relevant", False)),
                    "mentions_taboola": bool(parsed.get("mentions_taboola", False)),
                    "mentions_realize_product": bool(parsed.get("mentions_realize_product", False)),
                    "relevance_score": float(parsed.get("relevance_score", 0.0) or 0.0),
                    "raw_model_response": raw_text,
                }
            
            # Retryable errors (503 overloaded, 429 rate limit, 500 server error)
            elif response.status_code in [429, 500, 502, 503, 504]:
                error_msg = f"Gemini returned status {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f": {error_data.get('error', {}).get('message', '')}"
                except:
                    pass
                
                if attempt < max_retries - 1:
                    # Exponential backoff with jitter
                    actual_delay = min(retry_delay, max_delay)
                    logging.warning(
                        f"⚠ {error_msg} for post {post.id}. "
                        f"Retrying in {actual_delay:.1f}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(actual_delay)
                    retry_delay *= 2  # Double the delay
                else:
                    logging.error(f"✗ Max retries reached for post {post.id}. {error_msg}")
                    raise RuntimeError(f"Max retries reached: {error_msg}")
            
            # Non-retryable error
            else:
                error_msg = f"Gemini returned status {response.status_code}: {response.text[:200]}"
                logging.error(f"✗ Non-retryable error for post {post.id}: {error_msg}")
                raise RuntimeError(error_msg)
        
        except requests.Timeout:
            if attempt < max_retries - 1:
                logging.warning(f"⚠ Timeout for post {post.id}. Retrying in {retry_delay:.1f}s")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logging.error(f"✗ Max retries reached for post {post.id} due to timeouts")
                raise RuntimeError("Request timeout after max retries")
        
        except requests.RequestException as exc:
            if attempt < max_retries - 1:
                logging.warning(f"⚠ Network error for post {post.id}: {exc}. Retrying in {retry_delay:.1f}s")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                logging.error(f"✗ Max retries reached for post {post.id}: {exc}")
                raise RuntimeError(f"Network error after max retries: {exc}")
    
    # Should not reach here
    raise RuntimeError(f"Failed to process post {post.id} after {max_retries} attempts")


def _extract_text_from_gemini_response(response_payload: Dict[str, Any]) -> str:
    candidates = response_payload.get("candidates") or []
    if not candidates:
        return ""
    content = candidates[0].get("content", {})
    parts = content.get("parts") or []
    texts = [part.get("text", "") for part in parts if isinstance(part, dict)]
    return "\n".join(texts)

def passes_llm_filter(post: RedditPost, comments: List[RedditComment]) -> Tuple[bool, Dict[str, Any]]:
    return BASE_AGENT.run_llm_filter(post, comments, call_gemini_filter)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reddit ingestion agent for Taboola social listening.")
    parser.add_argument("--output-path", default="reddit_filtered.json", help="Destination JSON filepath.")
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

    with build_reddit_session() as session:
        post_cache: Dict[str, RedditPost] = {}
        for query in SEARCH_QUERIES:
            logging.info("Fetching posts for query '%s'", query)
            query_posts = fetch_global_search_posts(query, args.max_posts_per_query, session)
            logging.info("Query '%s' returned %d posts from Reddit search", query, len(query_posts))
            
            existing_ids: Set[str] = set(post_cache.keys())
            existing_ids.update(post.id for post in query_posts)
            
            if len(query_posts) <= GOOGLE_RESULT_THRESHOLD and len(query_posts) < args.max_posts_per_query:
                logging.info(
                    "Query '%s' returned %d posts from Reddit search; attempting search engine augmentation",
                    query,
                    len(query_posts),
                )
                remaining_capacity = max(0, args.max_posts_per_query - len(query_posts))
                additional_posts = fetch_additional_posts_duck_duck_go(query, session, existing_ids, remaining_capacity)
                query_posts.extend(additional_posts)
                logging.info("After augmentation, query '%s' has %d total posts", query, len(query_posts))
            
            for post in query_posts:
                post_cache[post.id] = post

        logging.info("Total unique posts collected: %d", len(post_cache))

        # IMPROVED: Efficient filtering - separate by confidence level
        logging.info("=" * 60)
        logging.info("Stage 1: Quick filtering all posts...")
        
        high_confidence_posts, needs_llm_posts, rejected_count = BASE_AGENT.run_quick_filter(
            post_cache.values(),
            on_reject=lambda post, reason: logging.debug(f"✗ Rejected {post.id}: {reason}"),
            on_auto_accept=lambda post, confidence, reason: logging.info(
                f"✓ Auto-accept {post.id} (conf={confidence:.2f}): {reason}"
            ),
            on_needs_llm=lambda post, confidence, reason: logging.info(
                f"? Needs LLM {post.id} (conf={confidence:.2f}): {reason}"
            ),
        )
        
        logging.info("=" * 60)
        logging.info("Filtering Results:")
        logging.info(f"  Total posts: {len(post_cache)}")
        logging.info(f"  ✗ Rejected: {rejected_count}")
        logging.info(f"  ✓ Auto-accepted (high confidence): {len(high_confidence_posts)}")
        logging.info(f"  ? Needs LLM verification: {len(needs_llm_posts)}")
        logging.info(f"  📊 LLM calls reduced by: {(1 - len(needs_llm_posts)/max(1, len(post_cache))) * 100:.1f}%")
        logging.info("=" * 60)
        
        # Process high-confidence posts (NO LLM calls!)
        logging.info(
            "Stage 2: Processing %d high-confidence posts (no LLM)...",
            len(high_confidence_posts),
        )
        high_conf_payloads = BASE_AGENT.process_high_confidence_posts(
            high_confidence_posts,
            lambda post_id: fetch_post_comments(post_id, session),
        )
        posts_payload.extend(high_conf_payloads)
        
        logging.info("✓ Processed %d high-confidence posts", len(high_confidence_posts))
        
        logging.info("Stage 3: Processing %d posts with LLM...", len(needs_llm_posts))
        
        llm_payloads = BASE_AGENT.process_posts_with_llm(
            needs_llm_posts,
            fetch_comments=lambda post_id: fetch_post_comments(post_id, session),
            llm_filter_fn=passes_llm_filter,
            on_post_start=lambda idx, total, post: logging.info(
                f"Processing {idx}/{total}: {post.id}"
            ),
            on_llm_result=lambda post, llm_metadata: logging.info(
                "LLM filter: post %s -> is_relevant=%s, score=%s",
                post.id,
                llm_metadata.get("is_relevant"),
                llm_metadata.get("relevance_score"),
            ),
            on_rate_limit_pause=lambda idx, total: logging.info(
                "⏸ Pausing 3 seconds to avoid rate limits..."
            ),
        )
        posts_payload.extend(llm_payloads)
        
        logging.info("=" * 60)
        logging.info(f"✓ Finished! Total relevant posts: {len(posts_payload)}")
        logging.info("=" * 60)

    BASE_AGENT.write_output(args.output_path, posts_payload, args.max_posts_per_query)


if __name__ == "__main__":
    main()
