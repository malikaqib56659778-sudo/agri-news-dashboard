import streamlit as st
import feedparser
import urllib.request

# Page configuration
st.set_page_config(page_title="Agri News Dashboard", page_icon="🌾", layout="wide")

st.title("🌾 Agricultural News & Market Dashboard")
st.write("Stay up-to-date with free, real-time agricultural news feeds from around the world.")

# Fully open, free, and cloud-friendly agricultural RSS sources
rss_feeds = {
    "ScienceDaily - Ag & Food Research": "https://www.sciencedaily.com/rss/plants_animals/agriculture_and_food.xml",
    "Farms.com - Industry News": "https://m.farms.com/farmspages/generate_rss_portal/tabid/2854/default.aspx",
    "USDA NASS - Reports & Events": "https://www.nass.usda.gov/Help/RSS/index.php",
    "BBC News - Science & Environment": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"
}

# Sidebar source selection
selected_source = st.sidebar.selectbox("📰 Select News Source", list(rss_feeds.keys()))
feed_url = rss_feeds[selected_source]

st.subheader(f"Latest Updates: {selected_source}")

# Robust Fetching Function to prevent Streamlit Cloud blocking
def fetch_feed(url):
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
        )
        xml_data = urllib.request.urlopen(req, timeout=10).read()
        return feedparser.parse(xml_data)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None

# Display News Articles
feed = fetch_feed(feed_url)

if feed and feed.entries:
    for entry in feed.entries[:10]:  # Display top 10 articles
        st.markdown(f"### [{entry.title}]({entry.link})")
        
        if hasattr(entry, 'published'):
            st.caption(f"📅 Published: {entry.published}")
        elif hasattr(entry, 'updated'):
            st.caption(f"📅 Updated: {entry.updated}")
            
        if hasattr(entry, 'summary'):
            # Basic cleanup of summary text
            summary_text = entry.summary.split('<')[0] if '<' in entry.summary else entry.summary
            st.write(summary_text)
            
        st.divider()
else:
    st.warning("No articles found or feed source is currently unreachable. Please choose another source from the sidebar menu.")
