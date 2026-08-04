import streamlit as st
import feedparser
import urllib.request
import re
import pandas as pd
from datetime import datetime
from weasyprint import HTML

# Page configuration
st.set_page_config(
    page_title="Agri Pulse AI - Global Agricultural Dashboard",
    page_icon="🌾",
    layout="wide"
)

# Custom Styling (CSS)
st.markdown("""
<style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 700;
        color: #2E7D32;
        margin-bottom: 0px;
    }
    .sub-title {
        color: #555555;
        font-size: 1rem;
        margin-bottom: 25px;
    }
    .news-card {
        background-color: #f9fbf9;
        padding: 18px;
        border-radius: 10px;
        border-left: 5px solid #2E7D32;
        margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# App Title Header
st.markdown('<div class="main-title">🌾 Agri Pulse AI Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Real-time global agricultural market intelligence and automated AI summaries.</div>', unsafe_allow_html=True)

# Free & Reliable Feeds
rss_feeds = {
    "ScienceDaily - Ag & Food Research": "https://www.sciencedaily.com/rss/plants_animals/agriculture_and_food.xml",
    "Farms.com - Global Industry News": "https://m.farms.com/farmspages/generate_rss_portal/tabid/2854/default.aspx",
    "BBC - Climate & Environment": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"
}

# Article Fetching Helper Functions
def fetch_feed(url):
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        )
        xml_data = urllib.request.urlopen(req, timeout=10).read()
        return feedparser.parse(xml_data)
    except Exception as e:
        st.error(f"Error connecting to server: {e}")
        return None

def clean_html(raw_html):
    return re.sub(re.compile('<.*?>'), '', raw_html)

def call_ai_summary(text, api_key):
    try:
        from openai import OpenAI
        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert agronomy consultant. Provide a 2-bullet point summary highlighting key agricultural implications."},
                {"role": "user", "content": text}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as err:
        return f"AI Service Error: {err}"

# Function to generate downloadable PDF report via WeasyPrint
def generate_pdf_report(source_name, entries):
    today_str = datetime.now().strftime("%B %d, %Y")
    
    articles_html = ""
    for idx, item in enumerate(entries[:10], 1):
        summary_text = clean_html(getattr(item, 'summary', 'No summary provided.'))
        pub_date = getattr(item, 'published', getattr(item, 'updated', 'Recent'))
        articles_html += f"""
        <div style="background:#ffffff; border:1px solid #e0e0e0; border-left:5px solid #2e7d32; padding:12px 16px; margin-bottom:12px; page-break-inside:avoid;">
            <div style="font-size:11pt; font-weight:bold; color:#1b5e20; margin-bottom:4px;">{idx}. {item.title}</div>
            <div style="font-size:8.5pt; color:#7f8c8d; margin-bottom:6px;">📅 Published: {pub_date}</div>
            <div style="font-size:9.5pt; line-height:1.4; color:#34495e;">{summary_text[:350]}...</div>
        </div>
        """

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        @page {{ size: A4; margin: 15mm 12mm; background-color: #fafbfa; }}
        body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #2c3e50; margin: 0; }}
        .header {{ background: linear-gradient(135deg, #1b5e20, #2e7d32); color: white; padding: 18px 22px; margin: -15mm -12mm 15px -12mm; }}
        .header h1 {{ margin: 0; font-size: 18pt; }}
        .header p {{ margin: 4px 0 0 0; font-size: 9.5pt; opacity: 0.9; }}
        .meta-table {{ width: 100%; border-collapse: collapse; background: #fff; margin-bottom: 15px; border: 1px solid #e0e0e0; }}
        .meta-table td {{ padding: 8px 12px; font-size: 9pt; border-bottom: 1px solid #f0f0f0; }}
        .meta-label {{ font-weight: bold; color: #2e7d32; width: 25%; }}
        .section-title {{ font-size: 12pt; color: #1b5e20; border-bottom: 2px solid #2e7d32; padding-bottom: 4px; margin: 15px 0 10px 0; text-transform: uppercase; }}
        .footer {{ margin-top: 25px; text-align: center; font-size: 8pt; color: #95a5a6; border-top: 1px solid #e0e0e0; padding-top: 8px; }}
    </style>
    </head>
    <body>
        <div class="header">
            <h1>🌾 Agri Pulse AI — News Intelligence Report</h1>
            <p>Automated Agricultural News Analysis & Market Briefing</p>
        </div>
        <table class="meta-table">
            <tr>
                <td class="meta-label">News Source:</td>
                <td>{source_name}</td>
                <td class="meta-label">Generated On:</td>
                <td>{today_str}</td>
            </tr>
            <tr>
                <td class="meta-label">Total Articles:</td>
                <td>{len(entries[:10])} Articles</td>
                <td class="meta-label">Status:</td>
                <td>Live Data Sync 🟢</td>
            </tr>
        </table>
        <div class="section-title">Summary of Top News & Findings</div>
        {articles_html}
        <div class="footer">
            Report generated by Agri Pulse AI Dashboard • Powered by Streamlit & Groq AI
        </div>
    </body>
    </html>
    """
    return HTML(string=html_template).write_pdf()

# Sidebar Navigation
with st.sidebar:
    st.header("⚙️ Dashboard Controls")
    selected_source = st.selectbox("📰 Select News Source", list(rss_feeds.keys()))
    
    st.divider()
    st.header("🤖 AI Integration Settings")
    ai_key = st.text_input("Enter Groq / OpenAI API Key", type="password", help="Get a free key from console.groq.com")
    ai_enabled = st.checkbox("Enable AI Article Summaries", value=False)

# Fetch Data
feed_url = rss_feeds[selected_source]
feed_data = fetch_feed(feed_url)

if feed_data and feed_data.entries:
    # Top Level Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Source", selected_source.split(" - ")[0])
    col2.metric("Total Articles Loaded", len(feed_data.entries))
    col3.metric("System Status", "Live Connection 🟢")

    st.divider()

    # Search Bar
    search_term = st.text_input("🔍 Search Articles by Keyword / Crop Name", "").lower()

    # Filter articles
    filtered_entries = [
        entry for entry in feed_data.entries 
        if search_term in entry.title.lower() or search_term in getattr(entry, 'summary', '').lower()
    ]

    # Sidebar Export Section
    with st.sidebar:
        st.divider()
        st.header("📥 Export Intelligence Report")
        
        # 1. Export CSV
        export_data = []
        for e in filtered_entries[:15]:
            export_data.append({
                "Title": e.title,
                "Published Date": getattr(e, 'published', getattr(e, 'updated', 'N/A')),
                "Link": e.link,
                "Summary": clean_html(getattr(e, 'summary', ''))
            })
        df_export = pd.DataFrame(export_data)
        csv_bytes = df_export.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📊 Download CSV Data",
            data=csv_bytes,
            file_name=f"Agri_News_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

        # 2. Export PDF
        try:
            pdf_bytes = generate_pdf_report(selected_source, filtered_entries)
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_bytes,
                file_name=f"Agri_Intelligence_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.caption(f"PDF Export setup notice: {e}")

    st.subheader(f"Showing Top Articles ({len(filtered_entries)})")

    # Display Article Cards
    for entry in filtered_entries[:10]:
        clean_summary = clean_html(getattr(entry, 'summary', 'No summary available.'))
        pub_date = getattr(entry, 'published', getattr(entry, 'updated', 'Recent'))
        
        with st.container():
            st.markdown(f"### [{entry.title}]({entry.link})")
            st.caption(f"📅 Published: {pub_date}")
            st.write(clean_summary[:300] + ("..." if len(clean_summary) > 300 else ""))
            
            if ai_enabled:
                if ai_key:
                    with st.expander("✨ View AI Insights & Agronomy Summary"):
                        with st.spinner("Analyzing article..."):
                            summary_result = call_ai_summary(clean_summary, ai_key)
                            st.write(summary_result)
                else:
                    st.warning("Please enter your API key in the sidebar menu to unlock AI Summaries.")
            
            st.divider()
else:
    st.warning("Currently unable to retrieve live articles for this feed. Try selecting another source from the sidebar.")
