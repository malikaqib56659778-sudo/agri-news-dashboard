import streamlit as st
import feedparser
import urllib.parse
import urllib.request
import re
import random
import time
import json
import pandas as pd
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from fpdf import FPDF
from io import BytesIO

# Optional Text-to-Speech support
try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

# ------------------------------------------------------------------------------
# 1. Page Configuration & Custom CSS
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="AgroNova - Universal Agriculture Intelligence",
    page_icon="🌾",
    layout="wide"
)

# Custom CSS for top corner weather layout, compact metrics, and developer badge
st.markdown("""
<style>
    /* Main Title Styling */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 5px;
    }
    .main-title {
        font-size: 2rem;
        font-weight: 800;
        color: #2E7D32;
        margin-bottom: 0px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .dev-badge {
        font-size: 0.72rem;
        font-weight: 600;
        color: #2E7D32;
        background-color: #E8F5E9;
        border: 1px solid #C8E6C9;
        padding: 2px 8px;
        border-radius: 12px;
        vertical-align: middle;
    }
    .sub-title {
        color: #555555;
        font-size: 0.9rem;
        margin-bottom: 10px;
    }

    /* Top Upper Corner Weather Box */
    .top-corner-weather {
        background-color: #F4F8F4;
        border: 1px solid #C8E6C9;
        border-right: 3px solid #2E7D32;
        border-radius: 6px;
        padding: 6px 12px;
        font-size: 0.82rem;
        color: #333333;
        display: flex;
        gap: 15px;
        align-items: center;
    }
    .weather-item {
        display: flex;
        flex-direction: column;
    }
    .weather-label {
        font-size: 0.7rem;
        color: #666666;
        font-weight: 600;
    }
    .weather-val {
        font-size: 0.95rem;
        font-weight: 700;
        color: #1B5E20;
    }

    /* Cache Bar Below Top Information */
    .cache-bar-info {
        background-color: #FAFAFA;
        border: 1px solid #E0E0E0;
        border-radius: 5px;
        padding: 4px 10px;
        font-size: 0.78rem;
        color: #555555;
        margin-bottom: 15px;
        display: inline-block;
    }

    /* Small Market & Telemetry Cards */
    .market-container {
        display: flex;
        gap: 8px;
        margin-bottom: 15px;
        flex-wrap: wrap;
    }
    .small-metric-card {
        flex: 1;
        min-width: 120px;
        max-width: 180px;
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-top: 2px solid #2E7D32;
        border-radius: 5px;
        padding: 6px 10px;
        box-sizing: border-box;
    }
    .metric-header {
        font-size: 0.72rem;
        font-weight: 600;
        color: #555555;
        white-space: nowrap;
        margin-bottom: 2px;
    }
    .metric-value {
        font-size: 0.95rem;
        font-weight: 700;
        color: #1B5E20;
        line-height: 1.1;
    }
    .metric-delta-pos {
        font-size: 0.7rem;
        font-weight: 600;
        color: #2E7D32;
    }
    .metric-delta-neg {
        font-size: 0.7rem;
        font-weight: 600;
        color: #C62828;
    }

    /* Developer Sidebar Card */
    .dev-sidebar-card {
        background-color: #F4F8F4;
        border-left: 3px solid #2E7D32;
        padding: 10px;
        border-radius: 5px;
        font-size: 0.82rem;
        color: #333333;
    }

    /* Primary Button Customization */
    div.stButton > button[kind="primary"] {
        background-color: #2E7D32 !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #1B5E20 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# 2. News Sources & Configurations
# ------------------------------------------------------------------------------
rss_feeds = {
    "All Global Sources Combined (Unlimited)": "COMBINED",
    "ScienceDaily - Crop & Soil Science": "https://www.sciencedaily.com/rss/plants_animals/agriculture_and_food.xml",
    "Farms.com - Global Farming News": "https://m.farms.com/farmspages/generate_rss_portal/tabid/2854/default.aspx",
    "BBC - Weather & Environment": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
    "Phys.org - Agriculture & Plants": "https://phys.org/rss-feed/earth-news/agriculture/",
    "EurekAlert! - Agriculture": "https://www.eurekalert.org/rss/agriculture.xml",
    "UN FAO Newsroom": "https://www.fao.org/news/rss-feed/en/",
    "AgFunder News - AgTech & Innovation": "https://agfundernews.com/feed",
    "Farm Progress - Farming & Livestock": "https://www.farmprogress.com/rss.xml",
    "World Grain News": "https://www.world-grain.com/rss/articles",
    "Agriland - Farming News": "https://www.agriland.ie/feed/",
    "Successful Farming": "https://www.agriculture.com/rss/all",
    "USDA Agricultural Research": "https://www.ars.usda.gov/news-events/news-rss/",
    "CGIAR Agricultural Innovation": "https://www.cgiar.org/news-events/news/feed/",
    "AgWeb - Farm Journal": "https://www.agweb.com/rss/all"
}

STATIC_FALLBACK_IMG = "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800&auto=format&fit=crop"

# ------------------------------------------------------------------------------
# 3. Cached Data Fetchers (10-minute TTL)
# ------------------------------------------------------------------------------
@st.cache_data(ttl=600)
def fetch_feed_cached(url):
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        )
        xml_data = urllib.request.urlopen(req, timeout=8).read()
        return feedparser.parse(xml_data)
    except Exception:
        return None

@st.cache_data(ttl=600)
def fetch_unlimited_google_news_search(query):
    encoded_query = urllib.parse.quote(query)
    queries = [
        f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en",
        f"https://news.google.com/rss/search?q={encoded_query}+when:7d&hl=en-US&gl=US&ceid=US:en",
        f"https://news.google.com/rss/search?q={encoded_query}+when:30d&hl=en-US&gl=US&ceid=US:en",
        f"https://news.google.com/rss/search?q={encoded_query}+agriculture&hl=en-US&gl=US&ceid=US:en"
    ]
    all_entries = []
    seen_titles = set()
    for url in queries:
        parsed = fetch_feed_cached(url)
        if parsed and parsed.entries:
            for entry in parsed.entries:
                title = getattr(entry, 'title', '')
                if title not in seen_titles:
                    seen_titles.add(title)
                    all_entries.append(entry)
    return all_entries

@st.cache_data(ttl=1800)
def fetch_live_weather(lat=31.4187, lon=73.0791):
    """Fetches weather metrics via free Open-Meteo API."""
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        req = urllib.request.Request(url, headers={'User-Agent': 'AgroNova'})
        res = urllib.request.urlopen(req, timeout=5).read()
        data = json.loads(res.decode('utf-8'))
        curr = data.get("current_weather", {})
        return {
            "temp": f"{curr.get('temperature', '30.5')} °C",
            "wind": f"{curr.get('windspeed', '6.1')} km/h",
            "status": "Sunny/Clear" if curr.get('weathercode', 0) < 3 else "Cloudy/Rain"
        }
    except Exception:
        return {"temp": "30.5 °C", "wind": "6.1 km/h", "status": "Clear"}

# ------------------------------------------------------------------------------
# 4. Utility & Helper Functions
# ------------------------------------------------------------------------------
def clean_html(raw_html):
    if not raw_html:
        return "No description available."
    return re.sub(re.compile('<.*?>'), '', raw_html)

def clean_filename(title):
    if not title:
        return "news_article"
    clean_str = re.sub(r'[^\w\s-]', '', title)
    clean_str = re.sub(r'[\s-]+', '_', clean_str).strip('_')
    return clean_str[:40]

def parse_entry_date(entry):
    raw_date = getattr(entry, 'published', getattr(entry, 'updated', None))
    if raw_date:
        try:
            return date_parser.parse(raw_date)
        except Exception:
            pass
    return datetime.now()

def extract_image_url(entry):
    if 'enclosures' in entry:
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image'):
                return enc.get('href')
    summary_raw = getattr(entry, 'summary', '')
    img_match = re.search(r'<img [^>]*src=["\']([^"\' text]+)["\']', summary_raw)
    if img_match:
        return img_match.group(1)
    
    title = getattr(entry, 'title', 'Agriculture')
    clean_p = re.sub(r'[^\w\s]', '', title)
    encoded = urllib.parse.quote(f"farm field agricultural photography {clean_p}")
    return f"https://image.pollinations.ai/prompt/{encoded}?width=600&height=400&nologo=true"

def text_to_speech_audio(text):
    if not HAS_GTTS:
        return None
    try:
        clean_text = re.sub(r'[^\w\s.,!]', '', text)
        tts = gTTS(text=clean_text[:300], lang='en', slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp
    except Exception:
        return None

def call_ai_summary(text, api_key):
    try:
        from openai import OpenAI
        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are a friendly farming helper explaining news to a farmer or student. "
                        "Rules:\n"
                        "1. Use extremely basic, simple English (5th-grade level).\n"
                        "2. Keep sentence length short (5-10 words maximum per sentence).\n"
                        "3. Do NOT use scientific words. Replace 'yield' with 'crop production', 'pathogen' with 'disease'.\n"
                        "4. Write in 3 short bullet points starting with clear emoji."
                    )
                },
                {"role": "user", "content": text}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as err:
        return f"AI Error: {err}"

class AgriPDFReport(FPDF):
    def header(self):
        self.set_fill_color(27, 94, 32)
        self.rect(0, 0, 210, 22, 'F')
        self.set_font('Arial', 'B', 13)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, 'AgroNova -- Easy News Report', 0, 1, 'L')
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()} | Developed by Aqib | AgroNova Dashboard', 0, 0, 'C')

def generate_pdf_report(source_name, entries):
    pdf = AgriPDFReport()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(35, 6, "Source:", 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(60, 6, source_name, 0, 1)
    pdf.ln(4)
    
    for item in entries:
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(27, 94, 32)
        title_str = getattr(item, 'title', 'Untitled Article')
        pdf.multi_cell(0, 5, title_str.encode('latin-1', 'replace').decode('latin-1'))
        summary_text = clean_html(getattr(item, 'summary', 'No summary.'))
        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 4.5, summary_text.encode('latin-1', 'replace').decode('latin-1'))
        pdf.ln(4)

    return bytes(pdf.output())

# ------------------------------------------------------------------------------
# 5. Session State Initialization
# ------------------------------------------------------------------------------
if "pinned_articles" not in st.session_state:
    st.session_state.pinned_articles = []
if "last_source" not in st.session_state:
    st.session_state.last_source = ""
if "shuffled_entries" not in st.session_state:
    st.session_state.shuffled_entries = []

# ------------------------------------------------------------------------------
# 6. UI Header with Developer Badge & Top Corner Weather
# ------------------------------------------------------------------------------
weather = fetch_live_weather()

# Top Header Layout (Title + Dev Badge on Left, Weather Upper Right Corner)
st.markdown(f"""
<div class="header-container">
    <div>
        <div class="main-title">
            🌾 AgroNova Dashboard
            <span class="dev-badge">Dev: Aqib</span>
        </div>
        <div class="sub-title">Universal agriculture intelligence aggregator with simple English & global search.</div>
    </div>
    <div class="top-corner-weather">
        <div class="weather-item">
            <span class="weather-label">🌡️ Regional Temp</span>
            <span class="weather-val">{weather["temp"]}</span>
        </div>
        <div style="border-left: 1px solid #C8E6C9; height: 22px;"></div>
        <div class="weather-item">
            <span class="weather-label">💨 Wind Speed</span>
            <span class="weather-val">{weather["wind"]}</span>
        </div>
    </div>
</div>
<div class="cache-bar-info">
    ⚡ <b>Feed Refresh Cache:</b> 10 Min Auto-Sync (Active)
</div>
""", unsafe_allow_html=True)

# Small Commodity Market Cards Below
st.markdown("""
<div class="market-container">
    <div class="small-metric-card">
        <div class="metric-header">🌾 Wheat Index</div>
        <div class="metric-value">$382 <span style="font-size:0.7rem; font-weight:normal;">/ Ton</span></div>
        <div class="metric-delta-pos">▲ +0.8%</div>
    </div>
    <div class="small-metric-card">
        <div class="metric-header">🌱 Soybeans Index</div>
        <div class="metric-value">$412 <span style="font-size:0.7rem; font-weight:normal;">/ Ton</span></div>
        <div class="metric-delta-neg">▼ -0.2%</div>
    </div>
    <div class="small-metric-card">
        <div class="metric-header">🌽 Corn Index</div>
        <div class="metric-value">$204 <span style="font-size:0.7rem; font-weight:normal;">/ Ton</span></div>
        <div class="metric-delta-pos">▲ +0.4%</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ------------------------------------------------------------------------------
# 7. Sidebar Controls
# ------------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Controls & Filters")
    selected_source = st.selectbox("📰 Choose News Source", list(rss_feeds.keys()))
    
    time_filter = st.selectbox("📅 Recency Filter", ["All Time", "Past 24 Hours", "Past 7 Days", "Past 30 Days"])
    
    st.divider()
    if st.button("🔀 Shuffle & Clear Cache"):
        st.cache_data.clear()
        st.session_state.last_source = "" 
        st.rerun()

    st.divider()
    st.header("🤖 Simple AI Notes Helper")
    default_key = st.secrets.get("GROQ_API_KEY", "") if "GROQ_API_KEY" in st.secrets else ""
    ai_key = st.text_input("Groq / OpenAI Key", value=default_key, type="password")
    ai_enabled = st.checkbox("Turn On Simple AI Notes", value=True)

    st.divider()
    st.markdown("""
    <div class="dev-sidebar-card">
        <b>👨‍💻 Developer</b><br>
        Developed & Maintained by <b>Aqib</b><br>
        <span style="font-size:0.75rem; color:#666666;">Agriculture & AgTech Innovation</span>
    </div>
    """, unsafe_allow_html=True)

# Main Refresh Action Button
if st.button("🔀 Get Fresh Articles", type="primary", use_container_width=True):
    st.cache_data.clear()
    st.session_state.last_source = ""
    st.rerun()

# ------------------------------------------------------------------------------
# 8. Load & Aggregate Articles
# ------------------------------------------------------------------------------
if selected_source != st.session_state.last_source or not st.session_state.shuffled_entries:
    all_entries = []
    if rss_feeds[selected_source] == "COMBINED":
        for name, url in rss_feeds.items():
            if url != "COMBINED":
                parsed = fetch_feed_cached(url)
                if parsed and parsed.entries:
                    all_entries.extend(parsed.entries)
    else:
        parsed = fetch_feed_cached(rss_feeds[selected_source])
        if parsed and parsed.entries:
            all_entries = parsed.entries

    seen = set()
    unique_entries = []
    for entry in all_entries:
        t = getattr(entry, 'title', '')
        if t not in seen:
            seen.add(t)
            unique_entries.append(entry)

    random.shuffle(unique_entries)
    st.session_state.shuffled_entries = unique_entries
    st.session_state.last_source = selected_source

current_entries = st.session_state.shuffled_entries

# ------------------------------------------------------------------------------
# 9. Search & Date Filtering Logic
# ------------------------------------------------------------------------------
search_term = st.text_input("🌐 Universal Search (Search ANY topic across the globe)", "").strip()

if search_term:
    search_progress = st.progress(0)
    for p in range(10, 50, 15):
        time.sleep(0.01)
        search_progress.progress(p)
        
    s_lower = search_term.lower()
    filtered_entries = [
        e for e in current_entries 
        if s_lower in getattr(e, 'title', '').lower() or s_lower in clean_html(getattr(e, 'summary', '')).lower()
    ]
    
    for p in range(50, 90, 15):
        time.sleep(0.02)
        search_progress.progress(p)
        
    live_unlimited = fetch_unlimited_google_news_search(search_term)
    existing_titles = {getattr(e, 'title', '') for e in filtered_entries}
    for live_item in live_unlimited:
        if getattr(live_item, 'title', '') not in existing_titles:
            existing_titles.add(getattr(live_item, 'title', ''))
            filtered_entries.append(live_item)

    search_progress.progress(100)
    time.sleep(0.05)
    search_progress.empty()
else:
    filtered_entries = current_entries

# Recency Date Filtering
if time_filter != "All Time":
    now = datetime.now()
    days_map = {"Past 24 Hours": 1, "Past 7 Days": 7, "Past 30 Days": 30}
    cutoff = now - timedelta(days=days_map[time_filter])
    filtered_entries = [e for e in filtered_entries if parse_entry_date(e) >= cutoff]

# ------------------------------------------------------------------------------
# 10. Article Display Feed
# ------------------------------------------------------------------------------
if filtered_entries:
    st.subheader(f"Showing News Articles ({len(filtered_entries)} Items Found)")

    pinned_set = set(st.session_state.pinned_articles)
    filtered_entries.sort(key=lambda x: 0 if getattr(x, 'title', '') in pinned_set else 1)

    for idx, entry in enumerate(filtered_entries):
        title = getattr(entry, 'title', 'Untitled Article')
        link = getattr(entry, 'link', '#')
        clean_sum = clean_html(getattr(entry, 'summary', 'No summary available.'))
        pub_date = getattr(entry, 'published', getattr(entry, 'updated', 'Recent'))
        article_slug = clean_filename(title)
        image_url = extract_image_url(entry)
        is_pinned = title in pinned_set

        with st.container():
            p_col1, p_col2 = st.columns([6, 1])
            with p_col1:
                if is_pinned:
                    st.markdown("📌 **[PINNED FAVORITE]**")
            with p_col2:
                if is_pinned:
                    if st.button("Unpin ❌", key=f"pin_{idx}"):
                        st.session_state.pinned_articles.remove(title)
                        st.rerun()
                else:
                    if st.button("Pin 📌", key=f"pin_{idx}"):
                        st.session_state.pinned_articles.append(title)
                        st.rerun()

            img_col, content_col = st.columns([1, 2.5])
            
            with img_col:
                try:
                    st.image(image_url, caption="✨ Visual Reference", use_container_width=True)
                except Exception:
                    st.image(STATIC_FALLBACK_IMG, caption="🌾 AgroNova Image", use_container_width=True)

            with content_col:
                st.markdown(f"### [{title}]({link})")
                st.caption(f"📅 Published: {pub_date}")
                st.write(clean_sum)
                
                if ai_enabled:
                    if ai_key:
                        with st.expander("✨ Click for Super Simple AI Notes & Audio"):
                            summary_res = call_ai_summary(clean_sum, ai_key)
                            st.success(f"**Easy Notes:**\n\n{summary_res}")
                            
                            if HAS_GTTS:
                                audio_fp = text_to_speech_audio(summary_res)
                                if audio_fp:
                                    st.audio(audio_fp, format="audio/mp3")
                    else:
                        st.caption("🔑 *Enter API key in left sidebar to unlock simple notes & voice readout.*")

            d_col1, d_col2 = st.columns(2)
            single_csv = pd.DataFrame([{
                "Title": title, "Published": pub_date, "Link": link, "Summary": clean_sum
            }]).to_csv(index=False).encode('utf-8')
            
            d_col1.download_button("📊 Save CSV", data=single_csv, file_name=f"{article_slug}.csv", mime="text/csv", key=f"csv_{idx}")
            d_col2.download_button("📄 Save PDF", data=generate_pdf_report(selected_source, [entry]), file_name=f"{article_slug}.pdf", mime="application/pdf", key=f"pdf_{idx}")
            
            st.divider()

    # Bulk Exports
    st.subheader(f"📥 Bulk Export ({len(filtered_entries)} Articles)")
    b1, b2 = st.columns(2)
    bulk_df = pd.DataFrame([{
        "Title": getattr(e, 'title', ''), "Link": getattr(e, 'link', ''), "Summary": clean_html(getattr(e, 'summary', ''))
    } for e in filtered_entries]).to_csv(index=False).encode('utf-8')
    
    b1.download_button("📊 Export All CSV", data=bulk_df, file_name="agronova_news_export.csv", mime="text/csv")
    b2.download_button("📄 Export All PDF", data=generate_pdf_report(selected_source, filtered_entries), file_name="agronova_news_report.pdf", mime="application/pdf")

else:
    st.warning("No news articles matched your search or date criteria. Try adjusting the recency filter in the sidebar!")

# Footer Credit Line
st.markdown("<br><hr><center><small style='color:#777777;'>AgroNova Dashboard • Developed by Aqib</small></center>", unsafe_allow_html=True)
