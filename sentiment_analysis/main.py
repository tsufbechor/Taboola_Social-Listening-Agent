#!/usr/bin/env python3
"""
Main execution script for Reddit Sentiment Analysis System
Run this to process Reddit data and generate insights
"""
import os
import sys
import argparse
from datetime import datetime

from config import (
    LLM_PROVIDER,
    OPENAI_MODEL,
    GEMINI_MODEL,
    GEMINI_API_KEY,
    GEMINI_API_URL,
)
from data_processor import RedditDataProcessor
from llm_client import OpenAIClient, GeminiClient
from sentiment_analyzer import SentimentAnalyzer


def main():
    parser = argparse.ArgumentParser(
        description="Analyze sentiment of Reddit posts and comments about Taboola"
    )
    parser.add_argument(
        "--input",
        default="/mnt/project/reddit_filtered.json",
        help="Path to input JSON file"
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Override LLM API key for the configured provider"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of items to process (for testing)"
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override LLM model identifier (defaults come from config)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run unit tests instead of processing"
    )
    
    args = parser.parse_args()
    
    # Run tests if requested
    if args.test:
        print("Running test suite...")
        from test_sentiment_system import run_tests
        result = run_tests()
        sys.exit(0 if result.wasSuccessful() else 1)
    
    # Validate input file
    if not os.path.exists(args.input):
        print(f"ERROR: Input file not found: {args.input}")
        sys.exit(1)

    provider = LLM_PROVIDER
    model_in_use = args.model or (OPENAI_MODEL if provider == "openai" else GEMINI_MODEL)

    try:
        if provider == "openai":
            if args.api_key:
                os.environ["OPENAI_API_KEY"] = args.api_key
            llm_client = OpenAIClient(model=model_in_use)
        elif provider == "gemini":
            gemini_key = args.api_key or GEMINI_API_KEY
            if not gemini_key:
                print("ERROR: Gemini API key not provided!")
                print("Set GEMINI_API_KEY environment variable or use --api-key argument")
                sys.exit(1)
            llm_client = GeminiClient(
                api_key=gemini_key,
                model=model_in_use,
                url_template=GEMINI_API_URL,
            )
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")
    except ValueError as exc:
        print(f"ERROR initializing LLM provider: {exc}")
        sys.exit(1)
    
    print("="*70)
    print("Reddit Sentiment Analysis System")
    print("="*70)
    print(f"Input file: {args.input}")
    print(f"Processing limit: {args.limit if args.limit else 'No limit'}")
    print(f"LLM provider: {provider}")
    print(f"LLM model: {model_in_use}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    try:
        # Initialize processor
        analyzer = SentimentAnalyzer(llm_client=llm_client)
        processor = RedditDataProcessor(
            args.input,
            api_key=args.api_key,
            model=model_in_use,
            analyzer=analyzer
        )
        
        # Load data
        print("\n[1/4] Loading Reddit data...")
        raw_data = processor.load_data()
        print(f"✓ Loaded {len(raw_data.get('posts', []))} posts")
        
        # Extract items
        print("\n[2/4] Extracting and deduplicating posts/comments...")
        items = processor.extract_posts_and_comments()
        print(f"✓ Extracted {len(items)} unique items")
        print(f"  - Filtered {len(processor.deduplicated_ids) - len(items)} duplicates/bots")
        
        # Process with sentiment analysis
        print(f"\n[3/4] Processing through sentiment analysis...")
        print("⚠ This may take a while depending on data size and API rate limits")
        results = processor.process_all(items=items, limit=args.limit)
        print(f"✓ Analyzed {len(results)} items")
        
        # Generate and save outputs
        print("\n[4/4] Generating insights and saving results...")
        output_files = processor.save_results()
        
        # Print summary
        summary = processor.generate_summary_report()
        
        print("\n" + "="*70)
        print("ANALYSIS COMPLETE!")
        print("="*70)
        
        print("\n📊 OVERVIEW:")
        print(f"  Total items analyzed: {summary['summary']['total_items']}")
        print(f"  Posts: {summary['summary']['total_posts']}")
        print(f"  Comments: {summary['summary']['total_comments']}")
        print(f"  Unique subreddits: {summary['summary']['unique_subreddits']}")
        
        print("\n💭 OVERALL SENTIMENT:")
        for sentiment, pct in summary['overall_sentiment_distribution'].items():
            print(f"  {sentiment.capitalize()}: {pct}")
        
        print("\n🚨 EDGE CASES DETECTED:")
        edge = summary['edge_cases']
        print(f"  Sarcastic comments: {edge['sarcastic_count']}")
        print(f"  Mixed sentiment: {edge['mixed_sentiment_count']}")
        print(f"  Non-English: {edge['non_english_count']}")
        print(f"  Spam/bots: {edge['spam_count']}")
        
        print("\n📈 TOP SENTIMENT BY FIELD:")
        for field, dist in summary['field_distributions'].items():
            mentions = dist.get('total_mentions', 0)
            if mentions > 0:
                # Get top sentiment
                sentiments = {k: v for k, v in dist.items() if k != 'total_mentions'}
                if sentiments:
                    top_sentiment = max(sentiments.items(), key=lambda x: x[1])
                    print(f"  {field}: {top_sentiment[0]} ({top_sentiment[1]:.1f}%) [{mentions} mentions]")
        
        print("\n📁 OUTPUT FILES:")
        for name, path in output_files.items():
            print(f"  {name}: {path}")
        
        print("\n✅ Analysis completed successfully!")
        print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
