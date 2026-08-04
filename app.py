import streamlit as st
import feedparser
import urllib.request
import re

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
    .badge {
        background-color: #E8F5E9;
        color: #1B5E20;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# App Top Banner
st.markdown('<div class="main-title">🌾 Agri Pulse AI Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Real-time global agricultural market intelligence and automated AI summaries.</div>', unsafe_allow_html=True)

# Free & Reliable Feeds
rss_feeds = {
    "ScienceDaily - Ag & Food Research": "https://www.sciencedaily.com/rss/plants_animals/agriculture_and_food.xml",
    "Farms.com - Global Industry News": "https://m.farms.com/farmspages/generate_rss_portal/tabid/2854/default.aspx",
    "BBC - Climate & Environment": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"
}

# Sidebar Navigation & AI Configuration
with st.sidebar:
    st.header("⚙️ Dashboard Controls")
    selected_source = st.selectbox("📰 Select News Source", list(rss_feeds.keys()))
    
    st.divider()
    st.header("🤖 AI Integration Settings")
    st.caption("Summarize news using free cloud AI (Groq / OpenAI API).")
    ai_key = st.text_input("Enter Groq / OpenAI API Key", type="password", help="Optional: Get a free key from console.groq.com")
    ai_enabled = st.checkbox("Enable AI Article Summaries", value=False)
    
    st.divider()
    st.info("💡 **Tip:** Use the search bar on the main page to filter articles by specific crops like *Sugarcane, Wheat, Cotton, or Soil*.")

# Article Fetching Logic with User-Agent setup
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
    clean_text = re.sub(re.compile('<.*?>'), '', raw_html)
    return clean_text

def call_ai_summary(text, api_key):
    # Optional Groq/OpenAI integration logic
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
        return f"AI Service Error: Ensure your API key is correct. ({err})"

# Fetch Data
feed_url = rss_feeds[selected_source]
feed_data = fetch_feed(feed_url)

if feed_data and feed_data.entries:
    # Main Dashboard Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Active Source", selected_source.split(" - ")[0])
    col2.metric("Total Articles Loaded", len(feed_data.entries))
    col3.metric("System Status", "Live Connection 🟢")

    st.divider()

    # Search & Filter Bar
    search_term = st.text_input("🔍 Search Articles by Keyword / Crop Name", "").lower()

    # Filter articles
    filtered_entries = [
        entry for entry in feed_data.entries 
        if search_term in entry.title.lower() or search_term in getattr(entry, 'summary', '').lower()
    ]

    st.subheader(f"Showing Top Articles ({len(filtered_entries)})")

    for entry in filtered_entries[:10]:
        clean_summary = clean_html(getattr(entry, 'summary', 'No summary available.'))
        pub_date = getattr(entry, 'published', getattr(entry, 'updated', 'Recent'))
        
        with st.container():
            st.markdown(f"### [{entry.title}]({entry.link})")
            st.caption(f"📅 Published: {pub_date}")
            st.write(clean_summary[:300] + ("..." if len(clean_summary) > 300 else ""))
            
            # Integrated AI Summary Trigger
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
