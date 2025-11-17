#!/bin/bash
# Quick Start Guide for Reddit Sentiment Analysis System

cat << 'EOF'
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   Reddit Sentiment Analysis System - Quick Start Guide           ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

This script helps you get started with the sentiment analysis system.

PREREQUISITES:
--------------
1. Python 3.8+ installed
2. Gemini API key from https://makersuite.google.com/app/apikey
3. Reddit data in /mnt/project/reddit_filtered.json

STEP 1: Install Dependencies
-----------------------------
EOF

echo "Installing required packages..."
pip install -q requests pandas

cat << 'EOF'

✓ Dependencies installed

STEP 2: Set API Key
-------------------
You need to set your Gemini API key. Choose one method:

Method A - Environment Variable (Recommended):
  export GEMINI_API_KEY="your-api-key-here"

Method B - Pass as argument:
  python main.py --api-key "your-api-key-here"

STEP 3: Run the System
----------------------

Option 1: Quick Test (50 items)
  python main.py --limit 50

Option 2: Medium Test (200 items) 
  python main.py --limit 200

Option 3: Full Analysis (all items)
  python main.py

Option 4: Run Tests First
  python main.py --test

STEP 4: Review Outputs
----------------------
Results will be saved to: /mnt/user-data/outputs/

Files created:
  • sentiment_results.json    - Full detailed analysis
  • summary_report.json       - Executive summary
  • field_distributions.csv   - Sentiment by field
  • sentiment_trends.csv      - Time-based trends
  • top_themes.json          - Key themes with quotes

DEMO MODE:
----------
To see sample outputs without using API:
  python demo.py

This creates demo files showing the expected output format.

EXAMPLE WORKFLOW:
-----------------

# 1. View demo outputs
python demo.py

# 2. Run tests to verify system
python main.py --test

# 3. Test with small sample
export GEMINI_API_KEY="your-key"
python main.py --limit 50

# 4. Review outputs
ls -lh /mnt/user-data/outputs/

# 5. Run full analysis (if sample looks good)
python main.py

TROUBLESHOOTING:
----------------

Problem: "ERROR: Gemini API key not provided"
Solution: Set GEMINI_API_KEY environment variable

Problem: "API call failed"
Solution: Check your API key, internet connection, and API quota

Problem: "Rate limit exceeded"
Solution: Increase RETRY_DELAY in config.py or run smaller batches

Problem: Tests failing
Solution: Ensure all dependencies installed correctly

COST ESTIMATION:
----------------
• Gemini Flash: ~$0.001 per analysis
• 1000 items: ~$1-2 total
• Your data has ~400 items: ~$0.40-0.80

SUPPORT:
--------
• Read: README.md for full documentation
• Read: BUSINESS_INSIGHTS_GUIDE.md for interpreting results
• Check: test_sentiment_system.py for code examples

╔═══════════════════════════════════════════════════════════════════╗
║                     READY TO START?                               ║
╚═══════════════════════════════════════════════════════════════════╝

Run this command to start:

  python main.py --limit 50

EOF
