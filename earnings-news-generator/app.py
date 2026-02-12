"""
Earnings Transcript to News Generator
Converts earnings call transcripts into professional news articles with infographics
Similar to AlphaStreet style
"""

import streamlit as st
import json
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import re
import base64
import io

# Try to import anthropic, but make it optional for demo mode
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


# Demo data for testing without API key
DEMO_FINANCIAL_DATA = {
    "company_name": "Apple Inc.",
    "ticker": "AAPL",
    "quarter": "Q4",
    "fiscal_year": "FY2024",
    "report_date": datetime.now().strftime("%Y-%m-%d"),
    "current_quarter": {
        "revenue": {"value": 89500, "currency": "USD"},
        "net_income": {"value": 22956, "currency": "USD"},
        "eps": {"value": 1.46, "diluted": True},
        "gross_margin": {"value": 45.2},
        "operating_income": {"value": 26885, "currency": "USD"}
    },
    "year_over_year": {
        "revenue_change": 6.0,
        "eps_change": 13.2,
        "net_income_change": 10.5
    },
    "quarter_over_quarter": {
        "revenue_change": 2.3,
        "eps_change": 4.1
    },
    "estimates": {
        "revenue_estimate": 87200,
        "eps_estimate": 1.39,
        "revenue_beat": True,
        "eps_beat": True
    },
    "guidance": {
        "next_quarter_revenue": {"low": 92000, "high": 96000},
        "full_year_revenue": {"low": 380000, "high": 395000},
        "next_quarter_eps": {"low": 1.50, "high": 1.58}
    },
    "historical_quarters": [
        {"quarter": "Q1 FY24", "revenue": 81800, "eps": 1.29},
        {"quarter": "Q2 FY24", "revenue": 84300, "eps": 1.33},
        {"quarter": "Q3 FY24", "revenue": 87500, "eps": 1.40},
        {"quarter": "Q4 FY24", "revenue": 89500, "eps": 1.46}
    ],
    "key_highlights": [
        "iPhone revenue reached $43.8 billion, up 5% YoY",
        "Services segment hit all-time high of $22.2 billion, growing 14% YoY",
        "Returned $25 billion to shareholders through dividends and buybacks",
        "Strong cash position of $162 billion"
    ],
    "segment_performance": [
        {"segment": "iPhone", "revenue": 43800, "growth": 5.0},
        {"segment": "Services", "revenue": 22200, "growth": 14.0},
        {"segment": "Wearables", "revenue": 9000, "growth": -2.0},
        {"segment": "Mac", "revenue": 7600, "growth": 3.0},
        {"segment": "iPad", "revenue": 7000, "growth": 8.0}
    ],
    "ceo_quote": "We're thrilled to report another record-breaking quarter with strong performance across our product lineup and services.",
    "outlook": "We expect continued growth driven by our services segment and upcoming product launches."
}

DEMO_ARTICLE_DATA = {
    "headline": "Apple Q4 FY2024 Earnings Beat: Revenue Up 6% to $89.5B, EPS Surges 13%",
    "subheadline": "Services segment hits all-time high as iPhone sales remain strong",
    "lead": "Apple Inc. (NASDAQ: AAPL) reported stellar fourth-quarter results that exceeded Wall Street expectations, with revenue climbing 6% year-over-year to $89.5 billion and earnings per share jumping 13% to $1.46. The tech giant's performance was driven by robust iPhone sales and a record-breaking quarter for its high-margin Services business.",
    "key_numbers": "Revenue of $89.5 billion topped analyst estimates of $87.2 billion, representing a $2.3 billion beat. Diluted EPS of $1.46 crushed the consensus estimate of $1.39 by 5%. Gross margin expanded to 45.2% from 44.5% in the year-ago quarter, reflecting improved operational efficiency and favorable product mix. The company generated operating income of $26.9 billion, up 8% year-over-year.",
    "segment_details": "iPhone remained the largest revenue contributor at $43.8 billion, up 5% YoY despite a challenging smartphone market. The Services segment was the star performer, hitting an all-time high of $22.2 billion with 14% growth, driven by App Store, Apple Music, and iCloud subscriptions. Mac revenue came in at $7.6 billion (+3%), while iPad saw an 8% increase to $7.0 billion. Wearables, Home and Accessories declined 2% to $9.0 billion amid market saturation.",
    "management_commentary": "CEO Tim Cook expressed optimism about the company's trajectory: 'We're thrilled to report another record-breaking quarter with strong performance across our product lineup and services. Our ecosystem continues to expand, and customer satisfaction remains at all-time highs.' CFO Luca Maestri highlighted the company's capital return program, noting that Apple returned $25 billion to shareholders this quarter through dividends and share repurchases.",
    "outlook": "For Q1 FY2025, Apple guided revenue between $92 billion and $96 billion, representing 5-8% year-over-year growth. EPS is expected in the range of $1.50 to $1.58. Management expressed confidence in the upcoming holiday season, citing strong demand for the new iPhone lineup and continued momentum in Services. The company maintains a robust cash position of $162 billion, providing flexibility for future investments and shareholder returns.",
    "conclusion": "Apple's Q4 results demonstrate the company's ability to deliver consistent growth despite macroeconomic headwinds. With a diversified revenue base, expanding services ecosystem, and loyal customer base, Apple remains well-positioned for continued success. The stock gained 2% in after-hours trading following the earnings release.",
    "read_time": 4
}

# Page configuration
st.set_page_config(
    page_title="Earnings News Generator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for AlphaStreet-style news
st.markdown("""
<style>
    .news-container {
        background: #ffffff;
        border-radius: 12px;
        padding: 30px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }
    .news-headline {
        font-size: 32px;
        font-weight: 700;
        color: #1a1a2e;
        line-height: 1.3;
        margin-bottom: 15px;
    }
    .news-meta {
        display: flex;
        gap: 20px;
        color: #666;
        font-size: 14px;
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 1px solid #eee;
    }
    .company-ticker {
        background: #0066cc;
        color: white;
        padding: 4px 12px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 14px;
    }
    .news-body {
        font-size: 17px;
        line-height: 1.8;
        color: #333;
    }
    .news-body p {
        margin-bottom: 16px;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 20px;
        color: white;
        text-align: center;
        height: 100%;
    }
    .metric-card.green {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    }
    .metric-card.blue {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    .metric-card.orange {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    }
    .metric-card.red {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 14px;
        opacity: 0.9;
    }
    .metric-change {
        font-size: 14px;
        margin-top: 8px;
    }
    .change-positive {
        color: #00ff88;
    }
    .change-negative {
        color: #ff6b6b;
    }
    .highlight-box {
        background: #f8f9fa;
        border-left: 4px solid #0066cc;
        padding: 15px 20px;
        margin: 20px 0;
        border-radius: 0 8px 8px 0;
    }
    .section-title {
        font-size: 20px;
        font-weight: 600;
        color: #1a1a2e;
        margin: 25px 0 15px 0;
    }
    .comparison-table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
    }
    .comparison-table th {
        background: #f8f9fa;
        padding: 12px;
        text-align: left;
        font-weight: 600;
        border-bottom: 2px solid #dee2e6;
    }
    .comparison-table td {
        padding: 12px;
        border-bottom: 1px solid #eee;
    }
    .beat {
        color: #28a745;
        font-weight: 600;
    }
    .miss {
        color: #dc3545;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


def extract_financial_data(client, transcript):
    """Use Claude to extract structured financial data from transcript"""

    extraction_prompt = """Analyze this earnings call transcript and extract the following information in JSON format:

{
    "company_name": "Full company name",
    "ticker": "Stock ticker symbol (e.g., AAPL)",
    "quarter": "Q1/Q2/Q3/Q4",
    "fiscal_year": "FY2024/FY2025 etc",
    "report_date": "Date mentioned or today",

    "current_quarter": {
        "revenue": {"value": number in millions, "currency": "USD"},
        "net_income": {"value": number in millions, "currency": "USD"},
        "eps": {"value": number, "diluted": true/false},
        "gross_margin": {"value": percentage number},
        "operating_income": {"value": number in millions, "currency": "USD"}
    },

    "year_over_year": {
        "revenue_change": percentage number (positive or negative),
        "eps_change": percentage number,
        "net_income_change": percentage number
    },

    "quarter_over_quarter": {
        "revenue_change": percentage number,
        "eps_change": percentage number
    },

    "estimates": {
        "revenue_estimate": number in millions or null,
        "eps_estimate": number or null,
        "revenue_beat": true/false/null,
        "eps_beat": true/false/null
    },

    "guidance": {
        "next_quarter_revenue": {"low": number, "high": number} or null,
        "full_year_revenue": {"low": number, "high": number} or null,
        "next_quarter_eps": {"low": number, "high": number} or null
    },

    "historical_quarters": [
        {"quarter": "Q4 2024", "revenue": number, "eps": number},
        {"quarter": "Q3 2024", "revenue": number, "eps": number},
        {"quarter": "Q2 2024", "revenue": number, "eps": number},
        {"quarter": "Q1 2024", "revenue": number, "eps": number}
    ],

    "key_highlights": [
        "Important bullet point 1",
        "Important bullet point 2",
        "Important bullet point 3"
    ],

    "segment_performance": [
        {"segment": "Segment Name", "revenue": number, "growth": percentage}
    ],

    "ceo_quote": "Notable quote from CEO if available",
    "outlook": "Brief outlook/guidance summary"
}

If any data is not available in the transcript, use null. Extract numbers without currency symbols.
For historical quarters, estimate or use any mentioned comparative figures.

TRANSCRIPT:
""" + transcript

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": extraction_prompt}]
    )

    # Extract JSON from response
    response_text = response.content[0].text

    # Try to find JSON in the response
    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            st.error("Failed to parse financial data. Please try again.")
            return None
    return None


def generate_news_article(client, financial_data, transcript):
    """Generate professional news article from extracted data"""

    article_prompt = f"""Based on this earnings data and transcript, write a professional financial news article in AlphaStreet style.

FINANCIAL DATA:
{json.dumps(financial_data, indent=2)}

ORIGINAL TRANSCRIPT (for context):
{transcript[:3000]}...

Write the article with these sections:
1. HEADLINE: Catchy, informative headline mentioning company, quarter, and key result (beat/miss)
2. LEAD: 2-3 sentence summary of the key results
3. KEY NUMBERS: Paragraph detailing revenue, EPS, and comparisons
4. SEGMENT DETAILS: Performance by business segment if available
5. MANAGEMENT COMMENTARY: Include CEO/CFO quotes or paraphrased insights
6. OUTLOOK: Forward-looking guidance and expectations
7. CONCLUSION: Brief wrap-up with stock context

Format the response as JSON:
{{
    "headline": "The headline text",
    "subheadline": "Optional subheadline",
    "lead": "Opening paragraph",
    "key_numbers": "Detailed numbers paragraph",
    "segment_details": "Segment performance paragraph",
    "management_commentary": "Quotes and insights paragraph",
    "outlook": "Guidance and outlook paragraph",
    "conclusion": "Closing paragraph",
    "read_time": estimated minutes to read (number)
}}

Write in professional financial journalism style - factual, clear, and engaging."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=3000,
        messages=[{"role": "user", "content": article_prompt}]
    )

    response_text = response.content[0].text
    json_match = re.search(r'\{[\s\S]*\}', response_text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            return None
    return None


def create_revenue_chart(financial_data):
    """Create revenue trend chart"""
    historical = financial_data.get('historical_quarters', [])

    if not historical:
        # Create sample data if not available
        current_rev = financial_data.get('current_quarter', {}).get('revenue', {}).get('value', 100)
        yoy_change = financial_data.get('year_over_year', {}).get('revenue_change', 5) or 5

        historical = [
            {"quarter": "Q1", "revenue": current_rev * 0.9},
            {"quarter": "Q2", "revenue": current_rev * 0.95},
            {"quarter": "Q3", "revenue": current_rev * 0.98},
            {"quarter": "Q4", "revenue": current_rev},
        ]

    quarters = [h['quarter'] for h in historical]
    revenues = [h.get('revenue', 0) for h in historical]

    fig = go.Figure()

    # Bar chart for revenue
    fig.add_trace(go.Bar(
        x=quarters,
        y=revenues,
        marker_color=['#4facfe', '#4facfe', '#4facfe', '#00f2fe'],
        text=[f"${r:,.0f}M" if r else "" for r in revenues],
        textposition='outside',
        name='Revenue'
    ))

    # Add trend line
    fig.add_trace(go.Scatter(
        x=quarters,
        y=revenues,
        mode='lines+markers',
        line=dict(color='#ff6b6b', width=3),
        marker=dict(size=10),
        name='Trend'
    ))

    fig.update_layout(
        title=dict(text='Quarterly Revenue Trend', font=dict(size=20)),
        xaxis_title='Quarter',
        yaxis_title='Revenue ($ Millions)',
        template='plotly_white',
        height=400,
        showlegend=False,
        margin=dict(t=50, b=50, l=50, r=50)
    )

    return fig


def create_eps_chart(financial_data):
    """Create EPS trend chart"""
    historical = financial_data.get('historical_quarters', [])

    if not historical:
        current_eps = financial_data.get('current_quarter', {}).get('eps', {}).get('value', 1.0)
        historical = [
            {"quarter": "Q1", "eps": current_eps * 0.85},
            {"quarter": "Q2", "eps": current_eps * 0.90},
            {"quarter": "Q3", "eps": current_eps * 0.95},
            {"quarter": "Q4", "eps": current_eps},
        ]

    quarters = [h['quarter'] for h in historical]
    eps_values = [h.get('eps', 0) for h in historical]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=quarters,
        y=eps_values,
        mode='lines+markers+text',
        fill='tozeroy',
        fillcolor='rgba(102, 126, 234, 0.2)',
        line=dict(color='#667eea', width=3),
        marker=dict(size=12, color='#667eea'),
        text=[f"${e:.2f}" if e else "" for e in eps_values],
        textposition='top center',
        name='EPS'
    ))

    fig.update_layout(
        title=dict(text='Earnings Per Share Trend', font=dict(size=20)),
        xaxis_title='Quarter',
        yaxis_title='EPS ($)',
        template='plotly_white',
        height=400,
        showlegend=False,
        margin=dict(t=50, b=50, l=50, r=50)
    )

    return fig


def create_segment_chart(financial_data):
    """Create segment performance pie/bar chart"""
    segments = financial_data.get('segment_performance', [])

    if not segments:
        return None

    segment_names = [s['segment'] for s in segments]
    segment_revenues = [s.get('revenue', 0) for s in segments]

    fig = go.Figure(data=[go.Pie(
        labels=segment_names,
        values=segment_revenues,
        hole=0.4,
        marker_colors=px.colors.qualitative.Set2
    )])

    fig.update_layout(
        title=dict(text='Revenue by Segment', font=dict(size=20)),
        template='plotly_white',
        height=400,
        margin=dict(t=50, b=50, l=50, r=50)
    )

    return fig


def create_comparison_chart(financial_data):
    """Create YoY comparison chart"""
    yoy = financial_data.get('year_over_year', {})

    metrics = ['Revenue', 'EPS', 'Net Income']
    changes = [
        yoy.get('revenue_change', 0) or 0,
        yoy.get('eps_change', 0) or 0,
        yoy.get('net_income_change', 0) or 0
    ]

    colors = ['#38ef7d' if c >= 0 else '#ff4b2b' for c in changes]

    fig = go.Figure(data=[go.Bar(
        x=metrics,
        y=changes,
        marker_color=colors,
        text=[f"{c:+.1f}%" for c in changes],
        textposition='outside'
    )])

    fig.update_layout(
        title=dict(text='Year-over-Year Change', font=dict(size=20)),
        xaxis_title='Metric',
        yaxis_title='Change (%)',
        template='plotly_white',
        height=400,
        showlegend=False,
        margin=dict(t=50, b=50, l=50, r=50)
    )

    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray")

    return fig


def render_metric_card(label, value, change=None, color="blue", prefix="", suffix=""):
    """Render a styled metric card"""
    change_html = ""
    if change is not None:
        change_class = "change-positive" if change >= 0 else "change-negative"
        change_symbol = "▲" if change >= 0 else "▼"
        change_html = f'<div class="metric-change {change_class}">{change_symbol} {abs(change):.1f}% YoY</div>'

    return f"""
    <div class="metric-card {color}">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{prefix}{value}{suffix}</div>
        {change_html}
    </div>
    """


def render_news_article(article_data, financial_data):
    """Render the complete news article"""

    ticker = financial_data.get('ticker', 'N/A')
    company = financial_data.get('company_name', 'Company')
    quarter = financial_data.get('quarter', 'Q4')
    fy = financial_data.get('fiscal_year', 'FY2024')
    read_time = article_data.get('read_time', 3)

    st.markdown(f"""
    <div class="news-container">
        <div class="news-headline">{article_data.get('headline', 'Earnings Report')}</div>
        <div class="news-meta">
            <span class="company-ticker">{ticker}</span>
            <span>{company}</span>
            <span>{quarter} {fy}</span>
            <span>📅 {datetime.now().strftime('%B %d, %Y')}</span>
            <span>⏱️ {read_time} min read</span>
        </div>
        <div class="news-body">
            <p><strong>{article_data.get('lead', '')}</strong></p>
            <p>{article_data.get('key_numbers', '')}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_comparison_table(financial_data):
    """Render YoY and QoQ comparison table"""
    current = financial_data.get('current_quarter', {})
    yoy = financial_data.get('year_over_year', {})
    estimates = financial_data.get('estimates', {})

    revenue = current.get('revenue', {}).get('value', 'N/A')
    eps = current.get('eps', {}).get('value', 'N/A')

    revenue_est = estimates.get('revenue_estimate', 'N/A')
    eps_est = estimates.get('eps_estimate', 'N/A')

    revenue_beat = estimates.get('revenue_beat')
    eps_beat = estimates.get('eps_beat')

    def beat_miss_class(beat):
        if beat is True:
            return 'beat', 'BEAT ✓'
        elif beat is False:
            return 'miss', 'MISS ✗'
        return '', 'N/A'

    rev_class, rev_status = beat_miss_class(revenue_beat)
    eps_class, eps_status = beat_miss_class(eps_beat)

    st.markdown(f"""
    <table class="comparison-table">
        <tr>
            <th>Metric</th>
            <th>Actual</th>
            <th>Estimate</th>
            <th>YoY Change</th>
            <th>Status</th>
        </tr>
        <tr>
            <td><strong>Revenue</strong></td>
            <td>${revenue:,.0f}M</td>
            <td>${revenue_est:,.0f}M</td>
            <td>{yoy.get('revenue_change', 'N/A')}%</td>
            <td class="{rev_class}">{rev_status}</td>
        </tr>
        <tr>
            <td><strong>EPS</strong></td>
            <td>${eps:.2f}</td>
            <td>${eps_est:.2f}</td>
            <td>{yoy.get('eps_change', 'N/A')}%</td>
            <td class="{eps_class}">{eps_status}</td>
        </tr>
    </table>
    """, unsafe_allow_html=True)


# Function to generate complete HTML report with all charts and data
def generate_full_html_report(financial_data, article_data):
    """Generate a complete HTML report with embedded charts"""

    ticker = financial_data.get('ticker', 'N/A')
    company = financial_data.get('company_name', 'Company')
    quarter = financial_data.get('quarter', 'Q4')
    fy = financial_data.get('fiscal_year', 'FY2024')
    read_time = article_data.get('read_time', 3)

    current = financial_data.get('current_quarter', {})
    yoy = financial_data.get('year_over_year', {})
    estimates = financial_data.get('estimates', {})

    # Get metric values
    revenue = current.get('revenue', {}).get('value', 0)
    eps = current.get('eps', {}).get('value', 0)
    margin = current.get('gross_margin', {}).get('value', 0)
    net_income = current.get('net_income', {}).get('value', 0)

    rev_change = yoy.get('revenue_change', 0) or 0
    eps_change = yoy.get('eps_change', 0) or 0
    ni_change = yoy.get('net_income_change', 0) or 0

    revenue_est = estimates.get('revenue_estimate', 0) or 0
    eps_est = estimates.get('eps_estimate', 0) or 0
    revenue_beat = estimates.get('revenue_beat')
    eps_beat = estimates.get('eps_beat')

    # Generate charts as HTML
    revenue_chart = create_revenue_chart(financial_data)
    eps_chart = create_eps_chart(financial_data)
    comparison_chart = create_comparison_chart(financial_data)
    segment_chart = create_segment_chart(financial_data)

    revenue_chart_html = revenue_chart.to_html(full_html=False, include_plotlyjs='cdn')
    eps_chart_html = eps_chart.to_html(full_html=False, include_plotlyjs=False)
    comparison_chart_html = comparison_chart.to_html(full_html=False, include_plotlyjs=False)
    segment_chart_html = segment_chart.to_html(full_html=False, include_plotlyjs=False) if segment_chart else "<p>Segment data not available</p>"

    # Beat/Miss status
    def get_status(beat):
        if beat is True:
            return '<span style="color: #28a745; font-weight: bold;">BEAT ✓</span>'
        elif beat is False:
            return '<span style="color: #dc3545; font-weight: bold;">MISS ✗</span>'
        return 'N/A'

    # Key highlights
    highlights_html = ""
    for h in financial_data.get('key_highlights', []):
        highlights_html += f"<li>{h}</li>"

    # Segment table
    segment_table = ""
    for seg in financial_data.get('segment_performance', []):
        growth_color = "#28a745" if seg.get('growth', 0) >= 0 else "#dc3545"
        segment_table += f"""
        <tr>
            <td>{seg.get('segment', 'N/A')}</td>
            <td>${seg.get('revenue', 0):,.0f}M</td>
            <td style="color: {growth_color}">{seg.get('growth', 0):+.1f}%</td>
        </tr>
        """

    html_report = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ticker} {quarter} {fy} Earnings Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 25px;
        }}
        .headline {{
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        .meta {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            font-size: 14px;
            opacity: 0.9;
        }}
        .ticker {{
            background: #0066cc;
            padding: 4px 12px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .section {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .section-title {{
            font-size: 20px;
            font-weight: 600;
            color: #1a1a2e;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #0066cc;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 25px;
        }}
        .metric-card {{
            border-radius: 12px;
            padding: 20px;
            color: white;
            text-align: center;
        }}
        .metric-card.blue {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }}
        .metric-card.green {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
        .metric-card.orange {{ background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }}
        .metric-card.purple {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
        .metric-label {{ font-size: 14px; opacity: 0.9; }}
        .metric-value {{ font-size: 28px; font-weight: 700; margin: 10px 0; }}
        .metric-change {{ font-size: 13px; }}
        .change-positive {{ color: #00ff88; }}
        .change-negative {{ color: #ff6b6b; }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }}
        .chart-container {{
            background: white;
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .highlight-box {{
            background: #f0f7fb;
            border-left: 4px solid #0066cc;
            padding: 15px 20px;
            margin: 15px 0;
            border-radius: 0 8px 8px 0;
        }}
        .article-body {{
            font-size: 16px;
            line-height: 1.8;
        }}
        .article-body p {{
            margin-bottom: 15px;
        }}
        ul {{
            margin-left: 20px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 12px;
        }}
        @media print {{
            body {{ background: white; }}
            .section {{ box-shadow: none; border: 1px solid #eee; }}
            .chart-container {{ page-break-inside: avoid; }}
        }}
        @media (max-width: 768px) {{
            .metrics-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .charts-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="headline">{article_data.get('headline', 'Earnings Report')}</div>
        <div class="meta">
            <span class="ticker">{ticker}</span>
            <span>{company}</span>
            <span>{quarter} {fy}</span>
            <span>📅 {datetime.now().strftime('%B %d, %Y')}</span>
            <span>⏱️ {read_time} min read</span>
        </div>
    </div>

    <!-- Key Metrics -->
    <div class="section">
        <div class="section-title">📊 Key Metrics</div>
        <div class="metrics-grid">
            <div class="metric-card blue">
                <div class="metric-label">Revenue</div>
                <div class="metric-value">${revenue:,.0f}M</div>
                <div class="metric-change {'change-positive' if rev_change >= 0 else 'change-negative'}">
                    {'▲' if rev_change >= 0 else '▼'} {abs(rev_change):.1f}% YoY
                </div>
            </div>
            <div class="metric-card green">
                <div class="metric-label">EPS</div>
                <div class="metric-value">${eps:.2f}</div>
                <div class="metric-change {'change-positive' if eps_change >= 0 else 'change-negative'}">
                    {'▲' if eps_change >= 0 else '▼'} {abs(eps_change):.1f}% YoY
                </div>
            </div>
            <div class="metric-card orange">
                <div class="metric-label">Gross Margin</div>
                <div class="metric-value">{margin:.1f}%</div>
            </div>
            <div class="metric-card purple">
                <div class="metric-label">Net Income</div>
                <div class="metric-value">${net_income:,.0f}M</div>
                <div class="metric-change {'change-positive' if ni_change >= 0 else 'change-negative'}">
                    {'▲' if ni_change >= 0 else '▼'} {abs(ni_change):.1f}% YoY
                </div>
            </div>
        </div>
    </div>

    <!-- Estimates vs Actual -->
    <div class="section">
        <div class="section-title">📋 Estimates vs Actual</div>
        <table>
            <tr>
                <th>Metric</th>
                <th>Actual</th>
                <th>Estimate</th>
                <th>YoY Change</th>
                <th>Status</th>
            </tr>
            <tr>
                <td><strong>Revenue</strong></td>
                <td>${revenue:,.0f}M</td>
                <td>${revenue_est:,.0f}M</td>
                <td>{rev_change:+.1f}%</td>
                <td>{get_status(revenue_beat)}</td>
            </tr>
            <tr>
                <td><strong>EPS</strong></td>
                <td>${eps:.2f}</td>
                <td>${eps_est:.2f}</td>
                <td>{eps_change:+.1f}%</td>
                <td>{get_status(eps_beat)}</td>
            </tr>
        </table>
    </div>

    <!-- Performance Charts -->
    <div class="section">
        <div class="section-title">📈 Performance Charts</div>
        <div class="charts-grid">
            <div class="chart-container">
                {revenue_chart_html}
            </div>
            <div class="chart-container">
                {eps_chart_html}
            </div>
            <div class="chart-container">
                {comparison_chart_html}
            </div>
            <div class="chart-container">
                {segment_chart_html}
            </div>
        </div>
    </div>

    <!-- Segment Performance Table -->
    <div class="section">
        <div class="section-title">📊 Segment Performance</div>
        <table>
            <tr>
                <th>Segment</th>
                <th>Revenue</th>
                <th>YoY Growth</th>
            </tr>
            {segment_table}
        </table>
    </div>

    <!-- Article Content -->
    <div class="section">
        <div class="section-title">📰 Full Article</div>
        <div class="article-body">
            <p><strong>{article_data.get('lead', '')}</strong></p>
            <p>{article_data.get('key_numbers', '')}</p>

            <h3 style="margin-top: 20px; color: #1a1a2e;">Segment Performance</h3>
            <p>{article_data.get('segment_details', '')}</p>

            <h3 style="margin-top: 20px; color: #1a1a2e;">Management Commentary</h3>
            <div class="highlight-box">
                {article_data.get('management_commentary', '')}
            </div>

            <h3 style="margin-top: 20px; color: #1a1a2e;">Outlook & Guidance</h3>
            <p>{article_data.get('outlook', '')}</p>

            <h3 style="margin-top: 20px; color: #1a1a2e;">Conclusion</h3>
            <p>{article_data.get('conclusion', '')}</p>
        </div>
    </div>

    <!-- Key Highlights -->
    <div class="section">
        <div class="section-title">🎯 Key Highlights</div>
        <ul>
            {highlights_html}
        </ul>
    </div>

    <div class="footer">
        Generated by Earnings News Generator | {datetime.now().strftime('%B %d, %Y at %H:%M')}
    </div>
</body>
</html>
    """
    return html_report


# Function to display all results
def display_results(financial_data, article_data):
    """Display the news article and all infographics"""

    # Display the news article
    render_news_article(article_data, financial_data)

    # Key Metrics Cards
    st.markdown("### 📊 Key Metrics")

    current = financial_data.get('current_quarter', {})
    yoy = financial_data.get('year_over_year', {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        revenue = current.get('revenue', {}).get('value', 0)
        rev_change = yoy.get('revenue_change', 0)
        st.markdown(render_metric_card(
            "Revenue",
            f"{revenue:,.0f}M" if revenue else "N/A",
            rev_change,
            "blue" if (rev_change or 0) >= 0 else "red",
            "$"
        ), unsafe_allow_html=True)

    with col2:
        eps = current.get('eps', {}).get('value', 0)
        eps_change = yoy.get('eps_change', 0)
        st.markdown(render_metric_card(
            "EPS",
            f"{eps:.2f}" if eps else "N/A",
            eps_change,
            "green" if (eps_change or 0) >= 0 else "red",
            "$"
        ), unsafe_allow_html=True)

    with col3:
        margin = current.get('gross_margin', {}).get('value', 0)
        st.markdown(render_metric_card(
            "Gross Margin",
            f"{margin:.1f}" if margin else "N/A",
            None,
            "orange",
            suffix="%"
        ), unsafe_allow_html=True)

    with col4:
        net_income = current.get('net_income', {}).get('value', 0)
        ni_change = yoy.get('net_income_change', 0)
        st.markdown(render_metric_card(
            "Net Income",
            f"{net_income:,.0f}M" if net_income else "N/A",
            ni_change,
            "green" if (ni_change or 0) >= 0 else "red",
            "$"
        ), unsafe_allow_html=True)

    # Comparison Table
    st.markdown("### 📋 Estimates vs Actual")
    render_comparison_table(financial_data)

    # Charts Section
    st.markdown("### 📈 Performance Charts")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        revenue_chart = create_revenue_chart(financial_data)
        st.plotly_chart(revenue_chart, use_container_width=True)

    with chart_col2:
        eps_chart = create_eps_chart(financial_data)
        st.plotly_chart(eps_chart, use_container_width=True)

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        comparison_chart = create_comparison_chart(financial_data)
        st.plotly_chart(comparison_chart, use_container_width=True)

    with chart_col4:
        segment_chart = create_segment_chart(financial_data)
        if segment_chart:
            st.plotly_chart(segment_chart, use_container_width=True)
        else:
            st.info("Segment data not available")

    # Full Article Content
    st.markdown("### 📰 Full Article")

    st.markdown(f"""
    <div class="news-container">
        <div class="section-title">Segment Performance</div>
        <p>{article_data.get('segment_details', 'Details not available.')}</p>

        <div class="section-title">Management Commentary</div>
        <div class="highlight-box">
            {article_data.get('management_commentary', 'Commentary not available.')}
        </div>

        <div class="section-title">Outlook & Guidance</div>
        <p>{article_data.get('outlook', 'Outlook not available.')}</p>

        <div class="section-title">Conclusion</div>
        <p>{article_data.get('conclusion', '')}</p>
    </div>
    """, unsafe_allow_html=True)

    # Key Highlights
    highlights = financial_data.get('key_highlights', [])
    if highlights:
        st.markdown("### 🎯 Key Highlights")
        for highlight in highlights:
            st.markdown(f"- {highlight}")

    # Export options
    st.markdown("---")
    st.markdown("### 📥 Export Options")

    ticker = financial_data.get('ticker', 'earnings')

    # Main export - Full HTML Report
    st.markdown("#### 🌟 Complete Report (Recommended)")
    st.markdown("*Download the full report with all charts, metrics, and article - ready to print or convert to PDF*")

    full_html_report = generate_full_html_report(financial_data, article_data)
    st.download_button(
        "📊 Download Complete HTML Report (All Charts + Article)",
        full_html_report,
        file_name=f"{ticker}_earnings_report.html",
        mime="text/html",
        use_container_width=True,
        type="primary"
    )

    st.info("💡 **Tip:** Open the HTML file in Chrome/Edge and press Ctrl+P to save as PDF with all charts!")

    st.markdown("---")
    st.markdown("#### 📈 Individual Charts")

    # Generate charts for download
    revenue_chart = create_revenue_chart(financial_data)
    eps_chart = create_eps_chart(financial_data)
    comparison_chart = create_comparison_chart(financial_data)
    segment_chart = create_segment_chart(financial_data)

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.download_button(
            "📊 Revenue Chart (HTML)",
            revenue_chart.to_html(full_html=True, include_plotlyjs='cdn'),
            file_name=f"{ticker}_revenue_chart.html",
            mime="text/html"
        )
        st.download_button(
            "📈 YoY Comparison Chart (HTML)",
            comparison_chart.to_html(full_html=True, include_plotlyjs='cdn'),
            file_name=f"{ticker}_yoy_comparison.html",
            mime="text/html"
        )

    with chart_col2:
        st.download_button(
            "💰 EPS Chart (HTML)",
            eps_chart.to_html(full_html=True, include_plotlyjs='cdn'),
            file_name=f"{ticker}_eps_chart.html",
            mime="text/html"
        )
        if segment_chart:
            st.download_button(
                "🥧 Segment Chart (HTML)",
                segment_chart.to_html(full_html=True, include_plotlyjs='cdn'),
                file_name=f"{ticker}_segment_chart.html",
                mime="text/html"
            )

    st.markdown("---")
    st.markdown("#### 📄 Data Exports")

    data_col1, data_col2, data_col3 = st.columns(3)

    with data_col1:
        # Export as JSON
        export_data = {
            "financial_data": financial_data,
            "article": article_data,
            "generated_at": datetime.now().isoformat()
        }
        st.download_button(
            "📄 Download JSON Data",
            json.dumps(export_data, indent=2, default=str),
            file_name=f"{ticker}_data.json",
            mime="application/json"
        )

    with data_col2:
        # Export article as text
        article_text = f"""
{article_data.get('headline', '')}
{'=' * 60}

{article_data.get('lead', '')}

KEY NUMBERS
{'-' * 40}
{article_data.get('key_numbers', '')}

SEGMENT PERFORMANCE
{'-' * 40}
{article_data.get('segment_details', '')}

MANAGEMENT COMMENTARY
{'-' * 40}
{article_data.get('management_commentary', '')}

OUTLOOK & GUIDANCE
{'-' * 40}
{article_data.get('outlook', '')}

CONCLUSION
{'-' * 40}
{article_data.get('conclusion', '')}

KEY HIGHLIGHTS
{'-' * 40}
""" + "\n".join([f"• {h}" for h in financial_data.get('key_highlights', [])])

        st.download_button(
            "📝 Download Article (TXT)",
            article_text,
            file_name=f"{ticker}_article.txt",
            mime="text/plain"
        )

    with data_col3:
        # Export metrics as CSV
        current = financial_data.get('current_quarter', {})
        yoy = financial_data.get('year_over_year', {})
        estimates = financial_data.get('estimates', {})

        csv_data = f"""Metric,Actual,Estimate,YoY Change,Status
Revenue (M),{current.get('revenue', {}).get('value', 'N/A')},{estimates.get('revenue_estimate', 'N/A')},{yoy.get('revenue_change', 'N/A')}%,{'BEAT' if estimates.get('revenue_beat') else 'MISS' if estimates.get('revenue_beat') is False else 'N/A'}
EPS,{current.get('eps', {}).get('value', 'N/A')},{estimates.get('eps_estimate', 'N/A')},{yoy.get('eps_change', 'N/A')}%,{'BEAT' if estimates.get('eps_beat') else 'MISS' if estimates.get('eps_beat') is False else 'N/A'}
Gross Margin %,{current.get('gross_margin', {}).get('value', 'N/A')},,
Net Income (M),{current.get('net_income', {}).get('value', 'N/A')},,{yoy.get('net_income_change', 'N/A')}%,

Segment,Revenue (M),Growth %
""" + "\n".join([f"{s.get('segment', 'N/A')},{s.get('revenue', 'N/A')},{s.get('growth', 'N/A')}%" for s in financial_data.get('segment_performance', [])])

        st.download_button(
            "📊 Download Metrics (CSV)",
            csv_data,
            file_name=f"{ticker}_metrics.csv",
            mime="text/csv"
        )


# Main Application
def main():
    st.title("📊 Earnings News Generator")
    st.markdown("*Transform earnings call transcripts into professional news articles with infographics*")

    # Sidebar for API key and settings
    with st.sidebar:
        st.header("⚙️ Settings")

        # Demo mode toggle
        demo_mode = st.toggle("🎮 Demo Mode (No API needed)", value=True, help="Use sample data to see how the app works")

        if not demo_mode:
            api_key = st.text_input("Claude API Key", type="password", help="Enter your Anthropic API key")
            st.caption("Get free API key at [console.anthropic.com](https://console.anthropic.com/)")
        else:
            api_key = None
            st.success("Demo mode active - using sample Apple earnings data")

        st.markdown("---")
        st.header("📋 Quick Guide")
        st.markdown("""
        1. Toggle Demo Mode ON to try the app
        2. Or enter Claude API key for real data
        3. Paste earnings transcript
        4. Click **Generate News**
        5. View article & infographics
        """)

        st.markdown("---")
        st.markdown("**Powered by Claude AI**")

    # Main content area
    tab1, tab2 = st.tabs(["📝 Input Transcript", "📰 Generated News"])

    with tab1:
        st.subheader("Paste Earnings Call Transcript")

        # Sample transcript for testing
        sample_transcript = """
        [Sample - Replace with actual transcript]

        Good afternoon and welcome to Apple Inc's Q4 FY2024 Earnings Conference Call.

        Tim Cook, CEO: We're thrilled to report another record-breaking quarter. Revenue came in at $89.5 billion,
        up 6% year-over-year, beating analyst estimates of $87.2 billion. Our iPhone revenue reached $43.8 billion,
        while Services hit an all-time high of $22.2 billion, growing 14% year-over-year.

        Earnings per share was $1.46, compared to $1.29 last year, beating the consensus estimate of $1.39.
        Gross margin improved to 45.2% from 44.5% in the prior year quarter.

        Luca Maestri, CFO: Looking at our segments, iPhone revenue was $43.8 billion, Mac revenue was $7.6 billion,
        iPad was $7.0 billion, Wearables and Accessories contributed $9.0 billion, and Services reached $22.2 billion.

        For Q1 FY2025, we expect revenue between $92 billion and $96 billion, representing growth of 5-8% year-over-year.
        We anticipate EPS in the range of $1.50 to $1.58.

        Our cash position remains strong at $162 billion, and we returned $25 billion to shareholders through
        dividends and buybacks this quarter.
        """

        transcript = st.text_area(
            "Transcript",
            value=sample_transcript,
            height=400,
            help="Paste the full earnings call transcript here"
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            generate_btn = st.button("🚀 Generate News", type="primary", use_container_width=True)

    # Process and display results
    if generate_btn:
        # Demo mode - use sample data
        if demo_mode:
            import time
            with st.spinner("🔍 Loading demo data..."):
                time.sleep(1)  # Simulate processing

            st.session_state['financial_data'] = DEMO_FINANCIAL_DATA
            st.session_state['article_data'] = DEMO_ARTICLE_DATA
            st.session_state['generated'] = True

        # Real API mode
        else:
            if not api_key:
                st.error("Please enter your Claude API key in the sidebar, or enable Demo Mode.")
                st.stop()

            if not transcript or len(transcript) < 100:
                st.error("Please enter a valid earnings transcript (minimum 100 characters).")
                st.stop()

            if not ANTHROPIC_AVAILABLE:
                st.error("Anthropic library not installed. Run: pip install anthropic")
                st.stop()

            try:
                client = anthropic.Anthropic(api_key=api_key)

                with st.spinner("🔍 Extracting financial data..."):
                    financial_data = extract_financial_data(client, transcript)

                if not financial_data:
                    st.error("Failed to extract financial data. Please check the transcript and try again.")
                    st.stop()

                with st.spinner("✍️ Generating news article..."):
                    article_data = generate_news_article(client, financial_data, transcript)

                if not article_data:
                    st.error("Failed to generate article. Please try again.")
                    st.stop()

                st.session_state['financial_data'] = financial_data
                st.session_state['article_data'] = article_data
                st.session_state['generated'] = True

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.stop()

    # Display results in tab2
    with tab2:
        if st.session_state.get('generated') and st.session_state.get('financial_data') and st.session_state.get('article_data'):
            financial_data = st.session_state['financial_data']
            article_data = st.session_state['article_data']

            if st.session_state.get('generated'):
                st.success("✅ News article generated successfully!")
                st.session_state['generated'] = False  # Reset flag

            display_results(financial_data, article_data)
        else:
            st.info("👈 Enter a transcript and click 'Generate News' to create your earnings article, or enable Demo Mode to see a sample.")


if __name__ == "__main__":
    main()
