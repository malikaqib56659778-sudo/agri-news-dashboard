import streamlit as st
import feedparser
import urllib.parse
import urllib.request
import re
import random
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# Page configuration
st.set_page_config(
    page_title="Agri Pulse AI - Universal & Simple Farm News",
    page_icon="🌾",
    layout="wide"
)

# Custom Styling (CSS)
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #2E7D32;
        margin-bottom: 0px;
    }
    .sub-title {
        color: #555555;
        font-size: 1rem;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# App Header
st.markdown('<div class="main-title">🌾 Agri Pulse AI Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Universal news aggregator with ultra-simple English, global RSS sources, and real-time search.</div>', unsafe_allow_html=True)

# Massive Expanded RSS Feed Directory
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

# Helper Functions
def fetch_feed(url):
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        )
        xml_data = urllib.request.urlopen(req, timeout=10).read()
        return feedparser.parse(xml_data)
    except Exception as e:
        return None

def fetch_google_news_search(query):
    encoded_query = urllib.parse.quote(query)
    google_rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
    return fetch_feed(google_rss_url)

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

def get_ai_generated_image(title):
    safe_title = title if title else "agriculture farm field"
    clean_prompt = re.sub(r'[^\w\s]', '', safe_title)
    formatted_prompt = f"agricultural science photography of {clean_prompt}, high resolution, realistic farm background"
    encoded_prompt = urllib.parse.quote(formatted_prompt)
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=600&height=400&nologo=true"

def extract_image_url(entry):
    if 'enclosures' in entry:
        for enc in entry.enclosures:
            if enc.get('type', '').startswith('image'):
                return enc.get('href')
    
    summary_raw = getattr(entry, 'summary', '')
    img_match = re.search(r'<img [^>]*src=["\']([^"\' text]+)["\']', summary_raw)
    if img_match:
        return img_match.group(1)
        
    return get_ai_generated_image(getattr(entry, 'title', 'Agriculture News'))

# Ultra-Simple English AI Prompt
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
                        "3. Do NOT use scientific or hard words. Replace 'yield' with 'crop production', 'pathogen' with 'disease', 'pesticide' with 'pest killer spray'.\n"
                        "4. Write in 3 short bullet points starting with clear emoji."
                    )
                },
                {"role": "user", "content": text}
            ],
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as err:
        return f"AI Service Error: {err}"

# Complete PDF Generator
class AgriPDFReport(FPDF):
    def header(self):
        self.set_fill_color(27, 94, 32)
        self.rect(0, 0, 210, 22, 'F')
        self.set_font('Arial', 'B', 13)
        self.set_text_color(255, 255, 255)
        self.cell(0, 6, 'Agri Pulse AI -- Easy News Report', 0, 1, 'L')
        self.set_font('Arial', '', 9)
        self.cell(0, 4, 'Simple English Notes for Easy Reading', 0, 1, 'L')
        self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()} | Generated by Agri Pulse AI Dashboard', 0, 0, 'C')

def generate_pdf_report(source_name, entries):
    pdf = AgriPDFReport()
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(35, 6, "News Source:", 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(60, 6, source_name, 0, 0)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(46, 125, 50)
    pdf.cell(35, 6, "Report Date:", 0, 0)
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 6, datetime.now().strftime("%B %d, %Y"), 0, 1)
    
    pdf.ln(4)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(27, 94, 32)
    pdf.cell(0, 8, f"Complete News List (Total Items: {len(entries)})", 0, 1)
    pdf.ln(2)

    for item in entries:
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(27, 94, 32)
        title_str = getattr(item, 'title', 'Untitled Article')
        safe_title = title_str.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 5, f"{safe_title}")
        
        pub_date = getattr(item, 'published', getattr(item, 'updated', 'Recent'))
        pdf.set_font('Arial', 'I', 8)
        pdf.set_text_color(128, 128, 128)
        pdf.cell(0, 4, f"Published Date: {pub_date}", 0, 1)
        
        summary_text = clean_html(getattr(item, 'summary', 'No summary available.'))
        safe_summary = summary_text.encode('latin-1', 'replace').decode('latin-1')
        
        pdf.set_font('Arial', '', 9)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 4.5, safe_summary)
        pdf.ln(5)

    return bytes(pdf.output())

# Session State Setup
if "pinned_articles" not in st.session_state:
    st.session_state.pinned_articles = []

if "last_source" not in st.session_state:
    st.session_state.last_source = ""

if "shuffled_entries" not in st.session_state:
    st.session_state.shuffled_entries = []

# Sidebar Controls
with st.sidebar:
    st.header("⚙️ Controls & Options")
    selected_source = st.selectbox("📰 Choose News Source", list(rss_feeds.keys()))
    
    st.divider()
    if st.button("🔀 Shuffle & Load New Articles"):
        st.cache_data.clear()
        st.session_state.last_source = "" 
        st.rerun()

    st.divider()
    st.header("🤖 Simple AI Notes Helper")
    
    default_key = st.secrets.get("GROQ_API_KEY", "") if "GROQ_API_KEY" in st.secrets else ""
    ai_key = st.text_input("Paste Groq / OpenAI API Key", value=default_key, type="password", help="Enter key to enable easy English AI notes")
    ai_enabled = st.checkbox("Turn On Very Simple AI Notes", value=True)

# Main Screen Quick Action
if st.button("🔀 Get Fresh Random Articles", type="primary", use_container_width=True):
    st.cache_data.clear()
    st.session_state.last_source = ""
    st.rerun()

st.divider()

# Fetch Dynamic & Unlimited Feeds
if selected_source != st.session_state.last_source or not st.session_state.shuffled_entries:
    all_entries = []
    if rss_feeds[selected_source] == "COMBINED":
        for name, url in rss_feeds.items():
            if url != "COMBINED":
                parsed = fetch_feed(url)
                if parsed and parsed.entries:
                    all_entries.extend(parsed.entries)
    else:
        parsed = fetch_feed(rss_feeds[selected_source])
        if parsed and parsed.entries:
            all_entries = parsed.entries

    # Deduplicate articles
    seen_titles = set()
    unique_entries = []
    for entry in all_entries:
        title = getattr(entry, 'title', '')
        if title not in seen_titles:
            seen_titles.add(title)
            unique_entries.append(entry)

    # Randomize order across all sources
    random.shuffle(unique_entries)
    st.session_state.shuffled_entries = unique_entries
    st.session_state.last_source = selected_source

current_entries = st.session_state.shuffled_entries

search_term = st.text_input("🌐 Universal Search (Search ANY word or topic from across the globe)", "").strip()

if search_term:
    search_lower = search_term.lower()
    filtered_entries = [
        entry for entry in current_entries 
        if search_lower in getattr(entry, 'title', '').lower() or search_lower in clean_html(getattr(entry, 'summary', '')).lower()
    ]
    
    # Universal Fallback: If no local feed results found, query Google News live
    if not filtered_entries:
        st.info(f"🌐 Fetching live global news results for **'{search_term}'** from across the web...")
        live_search_parsed = fetch_google_news_search(search_term)
        if live_search_parsed and live_search_parsed.entries:
            filtered_entries = live_search_parsed.entries
else:
    filtered_entries = current_entries

if current_entries:
    col1, col2, col3 = st.columns(3)
    col1.metric("Selected Channel", selected_source.split(" - ")[0])
    col2.metric("Total Articles Loaded", len(filtered_entries))
    col3.metric("Live Feed Status", "Active & Fresh 🟢")

    st.divider()

    # Keep pinned articles at top
    pinned_titles = st.session_state.pinned_articles
    filtered_entries.sort(key=lambda x: 0 if getattr(x, 'title', '') in pinned_titles else 1)

    st.subheader(f"Showing News Articles ({len(filtered_entries)} Items)")

    for idx, entry in enumerate(filtered_entries):
        title = getattr(entry, 'title', 'Untitled Article')
        link = getattr(entry, 'link', '#')
        clean_summary = clean_html(getattr(entry, 'summary', 'No description available.'))
        pub_date = getattr(entry, 'published', getattr(entry, 'updated', 'Recent'))
        article_slug = clean_filename(title)
        image_url = extract_image_url(entry)
        
        is_pinned = title in st.session_state.pinned_articles

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
                st.image(
                    image_url, 
                    caption="✨ AI Generated Visual", 
                    use_container_width=True
                )

            with content_col:
                # Article title without numbers
                st.markdown(f"### [{title}]({link})")
                st.caption(f"📅 Date: {pub_date}")
                st.write(clean_summary)
                
                if ai_enabled:
                    if ai_key:
                        with st.expander("✨ Click to view Super Simple English Explanation"):
                            with st.spinner("AI is writing ultra-simple notes..."):
                                summary_result = call_ai_summary(clean_summary, ai_key)
                                st.success(f"**Easy Notes:**\n\n{summary_result}")
                    else:
                        st.caption("🔑 *Enter your API key in the left sidebar to unlock easy AI notes.*")

            d_col1, d_col2 = st.columns(2)
            
            single_csv = pd.DataFrame([{
                "Title": title,
                "Published Date": pub_date,
                "Link": link,
                "Summary": clean_summary
            }]).to_csv(index=False).encode('utf-8')
            
            d_col1.download_button(
                label="📊 Save CSV",
                data=single_csv,
                file_name=f"{article_slug}.csv",
                mime="text/csv",
                key=f"csv_btn_{idx}"
            )
            
            single_pdf = generate_pdf_report(selected_source, [entry])
            d_col2.download_button(
                label="📄 Save PDF",
                data=single_pdf,
                file_name=f"{article_slug}.pdf",
                mime="application/pdf",
                key=f"pdf_btn_{idx}"
            )
            
            st.divider()

    st.subheader(f"📥 Export All News ({len(filtered_entries)} Articles)")
    all_col1, all_col2 = st.columns(2)
    
    full_export_data = []
    for e in filtered_entries:
        full_export_data.append({
            "Title": getattr(e, 'title', 'Untitled'),
            "Published Date": getattr(e, 'published', getattr(e, 'updated', 'N/A')),
            "Link": getattr(e, 'link', '#'),
            "Summary": clean_html(getattr(e, 'summary', ''))
        })
    
    full_csv = pd.DataFrame(full_export_data).to_csv(index=False).encode('utf-8')
    full_pdf = generate_pdf_report(selected_source, filtered_entries)
    
    source_slug = clean_filename(selected_source)
    
    all_col1.download_button(
        label=f"📊 Download All ({len(filtered_entries)}) Items CSV",
        data=full_csv,
        file_name=f"Full_News_{source_slug}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        key="full_csv_btn"
    )
    
    all_col2.download_button(
        label=f"📄 Download All ({len(filtered_entries)}) Items PDF",
        data=full_pdf,
        file_name=f"Full_News_{source_slug}_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        key="full_pdf_btn"
    )

else:
    st.warning("No news items found right now. Click 'Get Fresh Random Articles' to try pulling new sources!")
