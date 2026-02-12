# Earnings News Generator

Transform earnings call transcripts into professional news articles with infographics - similar to AlphaStreet style.

## Features

- **AI-Powered Analysis**: Uses Claude API to extract financial data from transcripts
- **Professional News Articles**: Generates AlphaStreet-style earnings news
- **Interactive Infographics**:
  - Revenue trend charts
  - EPS trend charts
  - YoY comparison charts
  - Segment performance pie charts
- **Key Metrics Cards**: Visual cards showing Revenue, EPS, Gross Margin, Net Income
- **Comparison Tables**: Actual vs Estimates with Beat/Miss indicators
- **Export Options**: Download as JSON or text

## Quick Start

### 1. Install Dependencies

```bash
cd earnings-news-generator
pip install -r requirements.txt
```

### 2. Get Claude API Key

1. Go to https://console.anthropic.com/
2. Create an account or sign in
3. Navigate to API Keys
4. Create a new API key

### 3. Run the Application

```bash
streamlit run app.py
```

### 4. Use the App

1. Enter your Claude API key in the sidebar
2. Paste an earnings call transcript
3. Click "Generate News"
4. View the generated article and infographics
5. Export as needed

## Sample Input

You can use earnings transcripts from:
- Company investor relations pages
- SEC EDGAR filings
- Financial news sites
- Earnings call transcript services (Seeking Alpha, The Motley Fool, etc.)

## Output Examples

The app generates:

1. **News Article** with:
   - Headline
   - Lead paragraph
   - Key numbers section
   - Segment performance
   - Management commentary
   - Outlook/guidance
   - Conclusion

2. **Infographics**:
   - Quarterly revenue bar chart with trend line
   - EPS area chart
   - YoY change comparison chart
   - Revenue by segment pie chart

3. **Metric Cards**:
   - Revenue with YoY change
   - EPS with YoY change
   - Gross Margin
   - Net Income with YoY change

4. **Comparison Table**:
   - Actual vs Estimate
   - Beat/Miss indicators

## Tech Stack

- **Frontend**: Streamlit
- **AI**: Claude API (Anthropic)
- **Charts**: Plotly
- **Data**: Pandas

## Customization

You can modify `app.py` to:
- Change chart colors and styles
- Add more metrics
- Customize the news article format
- Add new export formats (HTML, PDF)

## License

MIT License
