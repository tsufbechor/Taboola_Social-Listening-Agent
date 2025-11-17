"""
Test Suite for Reddit Sentiment Analysis System
Includes unit tests and integration tests
"""
import unittest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from sentiment_analyzer import SentimentAnalyzer
from data_processor import RedditDataProcessor
from config import ANALYSIS_FIELDS, SENTIMENT_CATEGORIES


class TestSentimentAnalyzer(unittest.TestCase):
    """exercises the core parser/validator in SentimentAnalyzer:
      it feeds complete, empty, and partially-filled JSON blobs
    into _validate_and_fix_response, checks that missing fields get filled with defaults, verifies _get_empty_response, and ensures _create_prompt includes every field listed in ANALYSIS_FIELDS.
      That gives you confidence the JSON-schema guardrails behave before any API call happens."""
    
    def setUp(self):
        self.analyzer = SentimentAnalyzer(api_key="test_key")
    
    def test_validate_and_fix_response_complete(self):
        """Test validation with complete response"""
        response = {
            "overall_sentiment": "positive",
            "field_sentiments": {
                "product_quality": {
                    "sentiment": "positive",
                    "confidence": 0.8,
                    "key_phrases": ["great product"]
                }
            },
            "edge_cases": {
                "is_sarcastic": False,
                "has_mixed_sentiment": False,
                "is_non_english": False,
                "language": "en",
                "is_spam": False
            },
            "themes": [{"theme": "quality", "relevance": 0.9}],
            "reasoning": "Positive feedback"
        }
        
        validated = self.analyzer._validate_and_fix_response(response)
        
        self.assertEqual(validated["overall_sentiment"], "positive")
        self.assertIn("product_quality", validated["field_sentiments"])
        self.assertEqual(len(validated["field_sentiments"]), len(ANALYSIS_FIELDS))
    
    def test_validate_and_fix_response_missing_fields(self):
        """Test validation fills in missing fields"""
        response = {}
        
        validated = self.analyzer._validate_and_fix_response(response)
        
        self.assertIn("overall_sentiment", validated)
        self.assertIn("field_sentiments", validated)
        self.assertIn("edge_cases", validated)
        self.assertIn("themes", validated)
        self.assertEqual(len(validated["field_sentiments"]), len(ANALYSIS_FIELDS))
    
    def test_validate_and_fix_response_partial_fields(self):
        """Test validation with partial field data"""
        response = {
            "overall_sentiment": "negative",
            "field_sentiments": {
                "user_experience": {
                    "sentiment": "negative"
                    # Missing confidence and key_phrases
                }
            }
        }
        
        validated = self.analyzer._validate_and_fix_response(response)
        
        ux_field = validated["field_sentiments"]["user_experience"]
        self.assertEqual(ux_field["sentiment"], "negative")
        self.assertEqual(ux_field["confidence"], 0.0)
        self.assertEqual(ux_field["key_phrases"], [])
    
    def test_empty_response(self):
        """Test empty text handling"""
        empty_result = self.analyzer._get_empty_response()
        
        self.assertEqual(empty_result["overall_sentiment"], "neutral")
        self.assertIn("field_sentiments", empty_result)
        self.assertEqual(empty_result["reasoning"], "Empty or invalid text")
    
    def test_create_prompt_structure(self):
        """Test prompt creation has required elements"""
        text = "Taboola ads are intrusive and low quality"
        prompt = self.analyzer._create_prompt(text, "comment")
        
        self.assertIn("comment", prompt)
        self.assertIn(text, prompt)
        self.assertIn("field_sentiments", prompt)
        for field in ANALYSIS_FIELDS:
            self.assertIn(field, prompt)


class TestDataProcessor(unittest.TestCase):
    """focuses on the ETL layer: load_data, extract_posts_and_comments (deduping IDs, dropping bot/short comments), and calculate_field_distributions."""
    
    def setUp(self):
        # Create mock Reddit data
        self.test_data = {
            "metadata": {
                "generated_at_utc": "2025-01-01T00:00:00Z"
            },
            "posts": [
                {
                    "post": {
                        "id": "test1",
                        "subreddit": "test",
                        "title": "Taboola is great",
                        "selftext": "I love this product",
                        "author": "user1",
                        "created_utc": 1704067200,
                        "score": 10,
                        "num_comments": 2
                    },
                    "comments": [
                        {
                            "id": "comment1",
                            "post_id": "test1",
                            "author": "user2",
                            "body": "I agree, the user experience is excellent",
                            "created_utc": 1704067300,
                            "score": 5,
                            "depth": 0
                        },
                        {
                            "id": "comment2",
                            "post_id": "test1",
                            "author": "AutoModerator",
                            "body": "I am a bot, and this action was performed automatically.",
                            "created_utc": 1704067400,
                            "score": 1,
                            "depth": 0
                        }
                    ]
                },
                {
                    "post": {
                        "id": "test1",  # Duplicate ID
                        "subreddit": "test",
                        "title": "Another post",
                        "selftext": "This is a duplicate",
                        "author": "user3",
                        "created_utc": 1704067500,
                        "score": 3,
                        "num_comments": 0
                    },
                    "comments": []
                }
            ]
        }
        
        # Save test data to temp file
        self.test_file = "/tmp/test_reddit_data.json"
        with open(self.test_file, 'w') as f:
            json.dump(self.test_data, f)
        
        self.processor = RedditDataProcessor(self.test_file, api_key="test_key")
    
    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
    
    def test_load_data(self):
        """Test data loading"""
        data = self.processor.load_data()
        
        self.assertIn("metadata", data)
        self.assertIn("posts", data)
        self.assertEqual(len(data["posts"]), 2)
    
    def test_extract_posts_and_comments(self):
        """Test extraction with deduplication"""
        items = self.processor.extract_posts_and_comments()
        
        # Should have 1 unique post (duplicate removed) + 1 comment (bot filtered)
        self.assertEqual(len(items), 2)
        
        # Check bot comment was filtered
        comment_texts = [item["text"] for item in items if item["context"] == "comment"]
        self.assertTrue(all("I am a bot" not in text for text in comment_texts))
        
        # Check deduplication worked
        post_ids = [item["metadata"]["id"] for item in items if item["context"] == "post"]
        self.assertEqual(len(post_ids), 1)
    
    def test_extract_filters_short_comments(self):
        """Test that very short comments are filtered"""
        short_comment_data = {
            "posts": [{
                "post": {
                    "id": "test2",
                    "title": "Test",
                    "selftext": "",
                    "created_utc": 1704067200
                },
                "comments": [
                    {
                        "id": "short1",
                        "body": "ok",  # Too short
                        "created_utc": 1704067200
                    },
                    {
                        "id": "good1",
                        "body": "This is a good comment with enough content",
                        "created_utc": 1704067200
                    }
                ]
            }]
        }
        
        test_file = "/tmp/test_short.json"
        with open(test_file, 'w') as f:
            json.dump(short_comment_data, f)
        
        processor = RedditDataProcessor(test_file)
        items = processor.extract_posts_and_comments()
        
        # Should only get the longer comment
        comments = [item for item in items if item["context"] == "comment"]
        self.assertEqual(len(comments), 1)
        self.assertIn("enough content", comments[0]["text"])
        
        os.remove(test_file)
    
    def test_calculate_field_distributions(self):
        """Test field distribution calculation"""
        # Mock processed data
        self.processor.processed_data = [
            {
                "analysis": {
                    "field_sentiments": {
                        "product_quality": {
                            "sentiment": "positive",
                            "confidence": 0.8
                        },
                        "user_experience": {
                            "sentiment": "negative",
                            "confidence": 0.9
                        }
                    }
                }
            },
            {
                "analysis": {
                    "field_sentiments": {
                        "product_quality": {
                            "sentiment": "positive",
                            "confidence": 0.7
                        },
                        "user_experience": {
                            "sentiment": "negative",
                            "confidence": 0.6
                        }
                    }
                }
            }
        ]
        
        distributions = self.processor.calculate_field_distributions()
        
        self.assertIn("product_quality", distributions)
        self.assertEqual(distributions["product_quality"]["total_mentions"], 2)
        self.assertEqual(distributions["product_quality"]["positive"], 100.0)
        
        self.assertIn("user_experience", distributions)
        self.assertEqual(distributions["user_experience"]["negative"], 100.0)


class TestIntegration(unittest.TestCase):
    """patches the Gemini HTTP call (@patch('sentiment_analyzer.requests.post')) to return canned JSON,
      then runs RedditDataProcessor.process_all, generate_summary_report, and the schema validator. 
      That ensures the full pipeline—from raw post/comment payload through sentiment analysis to summary/CSV-ready
        structures—still produces valid shapes even if the live API is unavailable."""
    
    @patch('sentiment_analyzer.requests.post')
    def test_end_to_end_pipeline(self, mock_post):
        """Test complete pipeline from data load to output"""
        
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "overall_sentiment": "mixed",
                            "field_sentiments": {
                                field: {
                                    "sentiment": "neutral",
                                    "confidence": 0.5,
                                    "key_phrases": ["test phrase"]
                                }
                                for field in ANALYSIS_FIELDS
                            },
                            "edge_cases": {
                                "is_sarcastic": False,
                                "has_mixed_sentiment": True,
                                "is_non_english": False,
                                "language": "en",
                                "is_spam": False
                            },
                            "themes": [
                                {"theme": "advertising", "relevance": 0.8}
                            ],
                            "reasoning": "Test reasoning"
                        })
                    }]
                }
            }]
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Create test data
        test_data = {
            "posts": [{
                "post": {
                    "id": "integration_test",
                    "title": "Test Taboola post",
                    "selftext": "Testing the system",
                    "subreddit": "test",
                    "author": "tester",
                    "created_utc": 1704067200,
                    "score": 5,
                    "num_comments": 1
                },
                "comments": [{
                    "id": "integration_comment",
                    "body": "This is a test comment about user experience",
                    "created_utc": 1704067300,
                    "score": 2
                }]
            }]
        }
        
        test_file = "/tmp/integration_test.json"
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Run pipeline
        processor = RedditDataProcessor(test_file, api_key="test_key")
        results = processor.process_all(limit=2)
        
        # Verify results
        self.assertEqual(len(results), 2)  # 1 post + 1 comment
        self.assertIn("analysis", results[0])
        self.assertEqual(results[0]["analysis"]["overall_sentiment"], "mixed")
        
        # Verify summary generation
        summary = processor.generate_summary_report()
        self.assertIn("summary", summary)
        self.assertIn("field_distributions", summary)
        self.assertIn("top_themes_by_field", summary)
        
        # Cleanup
        os.remove(test_file)
    
    def test_json_schema_validation(self):
        """Test that output matches expected JSON schema"""
        analyzer = SentimentAnalyzer(api_key="test_key")
        
        # Create a mock response
        mock_result = {
            "overall_sentiment": "positive",
            "field_sentiments": {
                field: {
                    "sentiment": "positive",
                    "confidence": 0.8,
                    "key_phrases": ["test"]
                }
                for field in ANALYSIS_FIELDS
            },
            "edge_cases": {
                "is_sarcastic": False,
                "has_mixed_sentiment": False,
                "is_non_english": False,
                "language": "en",
                "is_spam": False
            },
            "themes": [{"theme": "test", "relevance": 0.5}],
            "reasoning": "Test"
        }
        
        validated = analyzer._validate_and_fix_response(mock_result)
        
        # Validate schema compliance
        self.assertIn(validated["overall_sentiment"], SENTIMENT_CATEGORIES)
        
        for field in ANALYSIS_FIELDS:
            self.assertIn(field, validated["field_sentiments"])
            field_data = validated["field_sentiments"][field]
            self.assertIn("sentiment", field_data)
            self.assertIn("confidence", field_data)
            self.assertIn("key_phrases", field_data)
            self.assertIn(field_data["sentiment"], SENTIMENT_CATEGORIES)
            self.assertTrue(0 <= field_data["confidence"] <= 1)
        
        self.assertIsInstance(validated["themes"], list)
        self.assertIsInstance(validated["reasoning"], str)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSentimentAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestDataProcessor))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    result = run_tests()
    
    # Print summary
    print("\n" + "="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    print("="*70)
