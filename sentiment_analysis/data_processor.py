"""
Data Processor for Reddit sentiment analysis
Handles data ingestion, processing, and aggregation
"""
import json
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from collections import defaultdict, Counter
from sentiment_analyzer import SentimentAnalyzer
from config import ANALYSIS_FIELDS, OUTPUT_DIR,  GEMINI_MODEL,BATCH_SIZE
import os
LOW_CONFIDENCE_THRESHOLD = 0.3
MEDIUM_CONFIDENCE_THRESHOLD = 0.45
class RedditDataProcessor:
    """Process Reddit data and generate business insights"""
    
    def __init__(
        self,
        json_path: str,
        api_key: str = None,
        model: str = GEMINI_MODEL,
        analyzer: Optional[SentimentAnalyzer] = None
    ):
        self.json_path = json_path
        self.model = model or GEMINI_MODEL
        self.analyzer = analyzer
        self.api_key = api_key
        self.raw_data = None
        self.processed_data = []
        self.deduplicated_ids = set()
    def load_data(self) -> Dict[str, Any]:
        """Load Reddit data from JSON file"""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            self.raw_data = json.load(f)
        return self.raw_data
    
    def extract_posts_and_comments(self) -> List[Dict[str, Any]]:
        """
        Extract posts and comments with deduplication
        Returns list of items ready for analysis
        """
        items = []
        
        if not self.raw_data:
            self.load_data()
        
        for post_data in self.raw_data.get("posts", []):
            post = post_data.get("post", {})
            post_id = post.get("id")
            
            # Deduplicate by ID
            if post_id in self.deduplicated_ids:
                continue
            self.deduplicated_ids.add(post_id)
            
            # Extract post
            post_text = f"{post.get('title', '')} {post.get('selftext', '')}".strip()
            if post_text:
                items.append({
                    "text": post_text,
                    "context": "post",
                    "metadata": {
                        "id": post_id,
                        "type": "post",
                        "subreddit": post.get("subreddit", ""),
                        "author": post.get("author", ""),
                        "created_utc": post.get("created_utc", 0),
                        "score": post.get("score", 0),
                        "num_comments": post.get("num_comments", 0),
                        "url": post.get("url", "")
                    }
                })
            
            # Extract comments
            for comment in post_data.get("comments", []):
                comment_id = comment.get("id")
                if comment_id in self.deduplicated_ids:
                    continue
                self.deduplicated_ids.add(comment_id)
                
                comment_text = comment.get("body", "").strip()
                
                # Skip bot comments and very short comments
                if (comment_text and 
                    len(comment_text) > 20 and 
                    "I am a bot" not in comment_text):
                    items.append({
                        "text": comment_text,
                        "context": "comment",
                        "metadata": {
                            "id": comment_id,
                            "type": "comment",
                            "post_id": post_id,
                            "author": comment.get("author", ""),
                            "created_utc": comment.get("created_utc", 0),
                            "score": comment.get("score", 0),
                            "depth": comment.get("depth", 0)
                        }
                    })
        
        return items
    
    def process_all(self, items: List[Dict[str, Any]] = None, limit: int = None) -> List[Dict[str, Any]]:
        """
        Process all posts and comments through sentiment analyzer

        Args:
            items: Pre-extracted items to process (if None, will extract fresh)
            limit: Maximum number of items to process (for testing)

        Returns:
            List of processed items with sentiment analysis
        """
        # Use provided items or extract fresh ones
        if items is None:
            items = self.extract_posts_and_comments()
        
        if limit:
            items = items[:limit]
        
        print(f"Processing {len(items)} items...")
        
        # Ensure analyzer is available (backwards compatibility)
        if self.analyzer is None:
            self.analyzer = SentimentAnalyzer()

        # Process in batches
        batch_size = BATCH_SIZE
        for i in range(0, len(items), batch_size):
            batch = items[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(items)-1)//batch_size + 1}")
            
            results = self.analyzer.analyze_batch(batch)
            
            # Combine original data with analysis
            for item, result in zip(batch, results):
                item["analysis"] = result
                self.processed_data.append(item)
        
        print(f"Processed {len(self.processed_data)} items")
        return self.processed_data
    
    def calculate_field_distributions(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate sentiment distribution for each analysis field
        
        Returns:
            Dict mapping field -> sentiment -> percentage
        """
        distributions = {}
        
        for field in ANALYSIS_FIELDS:
            sentiment_counts = Counter()
            total = 0
            
            for item in self.processed_data:
                analysis = item.get("analysis", {})
                field_data = analysis.get("field_sentiments", {}).get(field, {})
                
                # Only count if confidence > 0.3
                confidence = field_data.get("confidence", 0)
                if confidence > LOW_CONFIDENCE_THRESHOLD:
                    sentiment = field_data.get("sentiment", "neutral")
                    sentiment_counts[sentiment] += 1
                    total += 1
            
            # Calculate percentages
            if total > 0:
                distributions[field] = {
                    sentiment: (count / total) * 100
                    for sentiment, count in sentiment_counts.items()
                }
                distributions[field]["total_mentions"] = total
            else:
                distributions[field] = {"total_mentions": 0}
        
        return distributions
    
    def extract_top_themes(self, top_n: int = 3) -> Dict[str, List[Dict]]:
        """
        Extract top themes per field with representative quotes
        
        Returns:
            Dict mapping field -> list of themes with quotes and links
        """
        themes_by_field = defaultdict(lambda: defaultdict(list))
        
        # Collect all themes by field
        for item in self.processed_data:
            analysis = item.get("analysis", {})
            metadata = item.get("metadata", {})
            
            for field in ANALYSIS_FIELDS:
                field_data = analysis.get("field_sentiments", {}).get(field, {})
                confidence = field_data.get("confidence", 0)
                
                if confidence > MEDIUM_CONFIDENCE_THRESHOLD:  # Only high confidence
                    key_phrases = field_data.get("key_phrases", [])
                    sentiment = field_data.get("sentiment", "neutral")
                    
                    for phrase in key_phrases[:2]:  # Top 2 phrases per item
                        themes_by_field[field][phrase].append({
                            "text": item.get("text", "")[:200],
                            "sentiment": sentiment,
                            "score": metadata.get("score", 0),
                            "url": metadata.get("url", ""),
                            "id": metadata.get("id", ""),
                            "type": metadata.get("type", "")
                        })
        
        # Get top themes for each field
        top_themes = {}
        for field, themes in themes_by_field.items():
            # Sort by frequency and score
            sorted_themes = sorted(
                themes.items(),
                key=lambda x: (len(x[1]), sum(item["score"] for item in x[1])),
                reverse=True
            )[:top_n]
            
            top_themes[field] = [
                {
                    "theme": theme,
                    "frequency": len(examples),
                    "representative_quotes": [
                        {
                            "text": ex["text"],
                            "sentiment": ex["sentiment"],
                            "score": ex["score"],
                            "link": ex["url"] if ex["url"] else f"https://www.reddit.com/comments/{ex['id']}"
                        }
                        for ex in sorted(examples, key=lambda x: x["score"], reverse=True)[:3]
                    ]
                }
                for theme, examples in sorted_themes
            ]
        
        return top_themes
    
    def calculate_trends_over_time(self, period: str = "week") -> pd.DataFrame:
        """
        Calculate sentiment trends over time
        
        Args:
            period: 'day' or 'week'
        
        Returns:
            DataFrame with time-based sentiment trends
        """
        # Convert to DataFrame
        records = []
        for item in self.processed_data:
            metadata = item.get("metadata", {})
            analysis = item.get("analysis", {})
            
            timestamp = metadata.get("created_utc", 0)
            if timestamp:
                date = datetime.fromtimestamp(timestamp)
                
                records.append({
                    "date": date,
                    "overall_sentiment": analysis.get("overall_sentiment", "neutral"),
                    "type": metadata.get("type", "unknown"),
                    "score": metadata.get("score", 0),
                    **{
                        f"{field}_sentiment": analysis.get("field_sentiments", {}).get(field, {}).get("sentiment", "neutral")
                        for field in ANALYSIS_FIELDS
                    },
                    **{
                        f"{field}_confidence": analysis.get("field_sentiments", {}).get(field, {}).get("confidence", 0)
                        for field in ANALYSIS_FIELDS
                    }
                })
        
        df = pd.DataFrame(records)
        
        if df.empty:
            return df
        
        # Group by period
        if period == "day":
            df["period"] = df["date"].dt.date
        else:  # week
            df["period"] = df["date"].dt.to_period("W").dt.start_time
        
        # Calculate sentiment percentages per period
        trends = []
        for period_val, group in df.groupby("period"):
            trend_record = {
                "period": period_val,
                "total_items": len(group),
                "avg_score": group["score"].mean()
            }
            
            # Overall sentiment distribution
            overall_dist = group["overall_sentiment"].value_counts(normalize=True) * 100
            for sentiment in ["positive", "neutral", "negative", "mixed"]:
                trend_record[f"overall_{sentiment}_pct"] = overall_dist.get(sentiment, 0)
            
            # Field-specific trends (for high confidence only)
            for field in ANALYSIS_FIELDS:
                high_conf = group[group[f"{field}_confidence"] > LOW_CONFIDENCE_THRESHOLD]
                if len(high_conf) > 0:
                    field_dist = high_conf[f"{field}_sentiment"].value_counts(normalize=True) * 100
                    trend_record[f"{field}_mentions"] = len(high_conf)
                    for sentiment in ["positive", "neutral", "negative"]:
                        trend_record[f"{field}_{sentiment}_pct"] = field_dist.get(sentiment, 0)
            
            trends.append(trend_record)
        
        return pd.DataFrame(trends).sort_values("period")
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive summary report"""
        
        # Overall statistics
        total_posts = sum(1 for item in self.processed_data if item["metadata"]["type"] == "post")
        total_comments = len(self.processed_data) - total_posts
        
        # Overall sentiment distribution
        overall_sentiments = Counter(
            item["analysis"]["overall_sentiment"] 
            for item in self.processed_data
        )
        total = len(self.processed_data)
        
        # Edge cases summary
        edge_cases = {
            "sarcastic_count": sum(1 for item in self.processed_data 
                                  if item["analysis"]["edge_cases"]["is_sarcastic"]),
            "mixed_sentiment_count": sum(1 for item in self.processed_data 
                                        if item["analysis"]["edge_cases"]["has_mixed_sentiment"]),
            "non_english_count": sum(1 for item in self.processed_data 
                                    if item["analysis"]["edge_cases"]["is_non_english"]),
            "spam_count": sum(1 for item in self.processed_data 
                             if item["analysis"]["edge_cases"]["is_spam"])
        }
        
        # Language distribution
        languages = Counter(
            item["analysis"]["edge_cases"]["language"]
            for item in self.processed_data
        )
        
        return {
            "summary": {
                "total_items": total,
                "total_posts": total_posts,
                "total_comments": total_comments,
                "unique_subreddits": len(set(item["metadata"].get("subreddit", "") 
                                            for item in self.processed_data)),
                "date_range": {
                    "earliest": min((item["metadata"]["created_utc"] 
                                   for item in self.processed_data), default=0),
                    "latest": max((item["metadata"]["created_utc"] 
                                 for item in self.processed_data), default=0)
                }
            },
            "overall_sentiment_distribution": {
                sentiment: f"{(count/total)*100:.1f}%"
                for sentiment, count in overall_sentiments.items()
            },
            "field_distributions": self.calculate_field_distributions(),
            "edge_cases": edge_cases,
            "language_distribution": dict(languages.most_common(5)),
            "top_themes_by_field": self.extract_top_themes()
        }
    
    def save_results(self):
        """Save all results to JSON and CSV files"""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Save full processed data
        output_json = f"{OUTPUT_DIR}/sentiment_results.json"
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(self.processed_data, f, indent=2, ensure_ascii=False)
        print(f"Saved detailed results to {output_json}")
        
        # Save summary report
        summary = self.generate_summary_report()
        summary_json = f"{OUTPUT_DIR}/summary_report.json"
        with open(summary_json, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"Saved summary report to {summary_json}")
        
        # Save field distributions as CSV
        dist_data = []
        for field, distribution in summary["field_distributions"].items():
            row = {"field": field}
            row.update(distribution)
            dist_data.append(row)
        
        dist_df = pd.DataFrame(dist_data)
        dist_csv = f"{OUTPUT_DIR}/field_distributions.csv"
        dist_df.to_csv(dist_csv, index=False)
        print(f"Saved field distributions to {dist_csv}")
        
        # Save trends
        trends_csv = None  # Default when no trends are available
        trends_df = self.calculate_trends_over_time(period="week")
        if not trends_df.empty:
            trends_csv = f"{OUTPUT_DIR}/sentiment_trends.csv"
            trends_df.to_csv(trends_csv, index=False)
            print(f"Saved trends to {trends_csv}")
        else:
            print("No time-based trends to save (insufficient dated items).")
        
        # Save top themes
        themes_json = f"{OUTPUT_DIR}/top_themes.json"
        with open(themes_json, 'w', encoding='utf-8') as f:
            json.dump(summary["top_themes_by_field"], f, indent=2, ensure_ascii=False)
        print(f"Saved top themes to {themes_json}")
        
        return {
            "detailed_results": output_json,
            "summary": summary_json,
            "distributions": dist_csv,
            "trends": trends_csv,
            "themes": themes_json
        }
