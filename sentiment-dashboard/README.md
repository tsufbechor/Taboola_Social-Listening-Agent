# Taboola Sentiment Analysis Dashboard

A modern, minimalistic React dashboard for visualizing sentiment analysis results from social listening data about Taboola and their "Realize" product.

## Features

### Data Source Selection

**Multi-Source Toggle** - Switch between different data sources in real-time:
- **Reddit Data** - Actual sentiment data from Reddit discussions about Taboola
- **AI Generated Data** - Synthetic sentiment data for testing and demonstration
- Seamless switching with automatic data reload
- Toggle located in the header for easy access

### Core Visualizations

1. **Dashboard Overview**
   - Key metrics cards showing total items, posts, comments, and subreddits
   - Overall sentiment distribution with interactive pie chart
   - Date range display

2. **Field-Level Sentiment Analysis**
   - Horizontal stacked bar chart showing sentiment distribution across 6 fields:
     - Product Quality
     - User Experience
     - Business Practices
     - Financial Performance
     - Publisher Relations
     - Advertiser Value
   - Color-coded: Green (positive), Yellow/Orange (mixed), Red (negative), Gray (neutral)
   - Displays mention counts for each field

3. **Trend Over Time**
   - Interactive line chart showing sentiment trends
   - Toggle between overall sentiment and individual field trends
   - Show/hide specific sentiment types
   - Smooth curves with hover tooltips

4. **Top Themes Explorer**
   - Browse top themes by field
   - View representative quotes with sentiment indicators
   - Click to read full quotes in a modal
   - Direct links to original Reddit posts

5. **Data Table / Feed**
   - Searchable, sortable, filterable table of all posts/comments
   - Expandable rows showing:
     - Full text with search highlighting
     - Field-level sentiment analysis with confidence scores
     - Key phrases for each field
     - Edge case indicators (sarcasm, mixed sentiment, etc.)
     - Links to original posts
   - Pagination support (10/25/50/100 per page)

### Filtering & Interactivity

6. **Comprehensive Filter Panel**
   - Full-text search across posts, comments, authors, and keywords
   - Multi-select sentiment filter
   - Field focus filter (show posts mentioning specific fields)
   - Platform filter (Reddit)
   - Subreddit multi-select
   - Post type filter (posts vs comments)
   - Edge case filters (sarcastic, mixed sentiment, non-English, spam)
   - Active filter count indicator
   - Clear all filters button

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS v4
- **Charts**: Recharts (React-native charting library)
- **Icons**: Lucide React
- **Data Handling**: Papa Parse (CSV parsing), native fetch (JSON)
- **Date Handling**: date-fns

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

1. Navigate to the project directory:
   ```bash
   cd sentiment-dashboard
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Ensure data files are in the `public/data/` directory:
   - `sentiment_results.json`
   - `sentiment_trends.csv`
   - `field_distributions.csv`
   - `summary_report.json`
   - `top_themes.json`

### Development

Start the development server:

```bash
npm run dev
```

The dashboard will be available at [http://localhost:5173](http://localhost:5173)

### Build for Production

Build the optimized production bundle:

```bash
npm run build
```

Preview the production build locally:

```bash
npm run preview
```

## Design Guidelines

### Visual Aesthetic
- **Minimalistic**: Clean, uncluttered interface
- **Data-First**: Visualizations speak for themselves
- **Professional**: Suitable for stakeholder presentations
- **Modern**: Dark theme with smooth transitions
- **Responsive**: Adapts to desktop and tablet screens

### Color Palette

- **Sentiment Colors**:
  - Positive: `#10b981` (green)
  - Neutral: `#6b7280` (gray)
  - Negative: `#ef4444` (red)
  - Mixed: `#f59e0b` (amber)

- **Background & Surface**:
  - Primary: `#0f172a` (slate-900)
  - Secondary: `#1e293b` (slate-800)
  - Surface: `#334155` (slate-700)

## Usage

### Viewing Overall Metrics

The top of the dashboard displays key metrics cards showing:
- Total items analyzed (posts + comments)
- Breakdown by posts vs comments
- Number of unique subreddits
- Data collection date range

### Analyzing Sentiment by Field

The "Sentiment by Field" chart shows how sentiment is distributed across all 6 analyzed fields. Each bar is stacked to show the percentage breakdown of positive, mixed, negative, and neutral sentiment.

### Tracking Trends

The "Sentiment Trends Over Time" chart lets you:
1. Select which metric to view (overall or specific field)
2. Toggle visibility of individual sentiment lines
3. Hover over data points to see exact values

### Exploring Themes

The "Top Themes by Field" section allows you to:
1. Select a field to view its top themes
2. Read representative quotes for each theme
3. Click "Read full quote" to see the complete text
4. Click "View source" to open the original Reddit post

### Filtering Data

Use the filter panel on the right to:
1. Search for specific text, authors, or keywords
2. Filter by sentiment (positive, negative, neutral, mixed)
3. Focus on specific fields
4. Filter by subreddit or post type
5. Show only edge cases (sarcasm, mixed sentiment, etc.)

Active filters are indicated by a blue badge. Click "Clear all" to reset.

### Browsing the Data Table

The posts & comments table at the bottom shows all data items. You can:
1. Sort by date, score, sentiment, or subreddit
2. Expand rows to see full analysis
3. View field-level sentiment with confidence scores
4. See key phrases and edge case flags
5. Navigate directly to original posts
6. Adjust items per page (10/25/50/100)

## Performance

- **Data Loading**: All data files are loaded in parallel on mount for fast initial load
- **Filtering**: Uses React's `useMemo` for efficient filter computation
- **Pagination**: Table pagination prevents rendering thousands of rows at once
- **Build Size**: ~636 KB JavaScript (minified), ~190 KB gzipped

## Browser Support

Tested and working on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Future Enhancements

Potential features for future versions:
- Export functionality (download filtered data as CSV)
- Dark/Light mode toggle
- Shareable dashboard state (URL parameters)
- Animated transitions
- Comparative analysis (compare time periods)
- Additional data sources (HackerNews, Twitter, etc.)
- Real-time data updates

## License

© 2025 Taboola Sentiment Analysis Dashboard
