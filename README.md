# Taboola Social Listening Platform

LLM-powered ingestion, analysis, and visualization pipeline for tracking Taboola conversations across Reddit, Hacker News, and synthetic datasets.

This repository contains everything needed to collect social chatter about Taboola, run LLM-backed sentiment analysis, and surface the insights in a React dashboard.

## Repository Layout

- `reddit_ingestion_agent.py`, `hacker_news_ingestion_agent.py`, `base_ingestion_agent.py` - Reddit and HackerNews agents plus the shared filtering/serialization helpers.
- `AI_GENERATED_REALIZE_POSTS.json` - synthetic Taboola Realize discussions that can be processed like any other data source.
- `sentiment_analysis/` - Sentiment Analysis:  configuration, processor, analyzer, LLM clients, tests, helper scripts.
- `sentiment-dashboard/` - Frontend: Vite + React + Tailwind dashboard that reads the processed data.

## Visual Insights & Dashboard 
<img width="742" height="774" alt="image" src="https://github.com/user-attachments/assets/cb0fb57a-851b-43e8-a089-0c25ce93ba3f" />

## Sentiment Trends Over Time
<img width="834" height="425" alt="image" src="https://github.com/user-attachments/assets/465dbe34-b48d-448d-9dcd-68f57c6545c6" />

## Representative Quotes for different fields.
<img width="1243" height="623" alt="image" src="https://github.com/user-attachments/assets/216265f3-c4e4-4a16-ba05-74021aa8c221" />

## Posts & Comments section
<img width="1241" height="825" alt="image" src="https://github.com/user-attachments/assets/64fda341-1a9e-4b60-ab89-669c272ad7db" />

## Filters
![20251117-1327-18 0383466](https://github.com/user-attachments/assets/e46f9c8e-121f-43e7-8e0f-b1d30bfba55d)

## Changing Data Source

![20251117-1329-03 8317740](https://github.com/user-attachments/assets/ef3e71fa-21d8-4575-8092-649cb19c5418)


## Prerequisites

- Python 3.10 or newer with `pip`.
- Node.js 18 or newer with `npm`.
- API access for the LLMs you plan to use:
  - Google Gemini Flash for the Reddit agent (Stage 3 relevance filter) and optionally the sentiment analyzer.
  - OpenAI for the HackerNews agent and  the sentiment analyzer.

## 1. Python Environment Setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install -r sentiment_analysis/requirements.txt
```


### Environment variables (`.env`)

Both the ingestion agents and the sentiment package automatically load `./.env`. Create it once in the repo root:

```
LLM_PROVIDER=openai                # or gemini
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-5.1
OPENAI_CHAT_COMPLETIONS_URL=https://api.openai.com/v1/chat/completions
GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-2.5-flash
LLM_MAX_WORKERS=3
LLM_REQUEST_DELAY=0.1
LLM_TIMEOUT=45

```


## 2. Run the Ingestion Agents

Common workflow:

1. Activate the virtualenv so all required packages and `.env` are loaded.
2. Run the agent from the repo root.
3. Inspect the generated JSON to make sure the payload looks correct.

### Reddit agent

```powershell
python reddit_ingestion_agent.py --max-posts-per-query 350 --output-path data/reddit_filtered.json
```

- Pulls Reddit search plus DuckDuckGo fallbacks, so no Reddit Auth keys are needed.
- Requires `GEMINI_API_KEY` and a descriptive `REDDIT_USER_AGENT`.
- Output schema per post: `{"post": {...}, "comments": [...], "llm_filter": {...}}` wrapped in a `{"metadata": ..., "posts": [...]}` envelope.

### HackerNews agent

```powershell
python hacker_news_ingestion_agent.py --max-posts-per-query 250 --output-path data/hacker_news_filtered.json
```

- Queries Algolia search for `Taboola` and `Taboola Realize`, fetches the stories and comment trees from the Firebase API, and applies the same quick filter plus LLM filter pipeline.
- Requires `OPENAI_API_KEY`, `OPENAI_MODEL`, and (optionally) `HN_USER_AGENT`.
- Produces the exact same JSON schema as the Reddit agent.

### Synthetic data

`AI_GENERATED_REALIZE_POSTS.json` already matches the ingestion schema. Run the sentiment analyzer directly on it whenever you want to refresh the synthetic data set.

## 3. Sentiment Analysis (`sentiment_analysis/`)

Use the analyzer to convert any ingestion output into dashboard-ready aggregates.

```powershell
cd sentiment_analysis
python main.py --input ../reddit_filtered.json --limit 250          # adjust limit as needed
python main.py --input ../hacker_news_filtered.json                 # run once per source
```

Flags:

- `--limit N` - process only the first `N` items (great for dry runs or quota control).
- `--api-key ...` - override the key from `.env` for the current execution.
- `--model ...` - override the configured OpenAI or Gemini model.
- `--test` - run `test_sentiment_system.py` and exit.

Each successful run writes the following files to `sentiment_analysis/output/`:

- `sentiment_results.json`
- `summary_report.json`
- `field_distributions.csv`
- `sentiment_trends.csv` (only when there is enough timestamp coverage)
- `top_themes.json`

Because new runs overwrite those files, copy them into the source-specific folders immediately so you can keep multiple data sets side by side:

```powershell
# Example: stash fresh Reddit results
mkdir -Force output/REDDIT_DATA
Copy-Item output/sentiment_results.json output/REDDIT_DATA/
Copy-Item output/summary_report.json output/REDDIT_DATA/
Copy-Item output/field_distributions.csv output/REDDIT_DATA/
Copy-Item output/sentiment_trends.csv output/REDDIT_DATA/ -ErrorAction SilentlyContinue
Copy-Item output/top_themes.json output/REDDIT_DATA/
```

Repeat those copy commands for `output/HACKER_NEWS_DATA` and `output/AI_GENERATED_DATA`.

Optional: build a lighter-weight rollup after copying the files:

```powershell
python build_aggregates_from_outputs.py
```

That script expects the three directories above and emits an `aggregates.json` file inside each one.

## 4. Feed the Dashboard

`sentiment-dashboard` reads static files from `public/data/<dataSource>/`. Three folders already exist (`reddit`, `hackernews`, `ai-generated`) and they map directly to the analyzer output directories you just populated.

Update the dashboard data whenever you refresh the analysis:

```powershell
# from the repository root
Copy-Item sentiment_analysis/output/REDDIT_DATA/* sentiment-dashboard/public/data/reddit/ -Recurse -Force
Copy-Item sentiment_analysis/output/HACKER_NEWS_DATA/* sentiment-dashboard/public/data/hackernews/ -Recurse -Force
Copy-Item sentiment_analysis/output/AI_GENERATED_DATA/* sentiment-dashboard/public/data/ai-generated/ -Recurse -Force
```

To add a brand-new data source, create a matching folder under `public/data/<name>/` with the five files listed above, then extend the `DataSource` union type in `sentiment-dashboard/src/types/index.ts`.

## 5. Launch the Dashboard

```powershell
cd sentiment-dashboard
npm install
npm run dev
```

Open http://localhost:5173 in your browser and use the header toggle to switch between Reddit, HackerNews, and AI generated data. For a production bundle:

```powershell
npm run build
npm run preview        # serves the dist/ directory locally
```

## Verification and Troubleshooting

- Rate limits: both agents implement exponential backoff and log when they pause. If you see many `429` or `503` responses, drop `--max-posts-per-query` or increase `LLM_REQUEST_DELAY`.
- Schema drift: the dashboard expects the CSV/JSON columns listed above. When you change fields in the analyzer, adjust `sentiment-dashboard/src/types` and `src/utils/csvParser.ts` to match.
- Frequent refreshes: wrap the agent + analyzer steps in a scheduled task, then copy the files into `sentiment-dashboard/public/data` before redeploying the front end.
- Testing: `python sentiment_analysis/main.py --test` runs the sentiment unit tests.

Following the five sections above lets any teammate reproduce your ingestion, analysis, and dashboard results from scratch.
