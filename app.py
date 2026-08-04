import streamlit as st
import feedparser

# App Title
st.title("🌾 Agricultural News Dashboard")

# Reliable Working Agricultural RSS Feeds
rss_feeds = {
    "AgWeb News": "https://www.agweb.com/rss/news",
    "Farm Progress": "https://www.farmprogress.com/rss.xml",
    "USDA ARS Research": "https://www.ars.usda.gov/rss/news.xml",
    "FAO News Feed": "https://www.fao.org/newsroom/rss/en/"
}

# Sidebar dropdown to choose the source
selected_source = st.sidebar.selectbox("Choose News Source", list(rss_feeds.keys()))
feed_url = rss_feeds[selected_source]

st.subheader(f"Latest Updates from {selected_source}")

# Fetch RSS Feed with custom User-Agent to bypass standard bot blocks
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

feed = feedparser.parse(feed_url, request_headers=headers)

if feed.entries:
    for entry in feed.entries[:10]:  # Displays the top 10 articles
        st.markdown(f"### [{entry.title}]({entry.link})")
        if hasattr(entry, 'published'):
            st.caption(f"Published on: {entry.published}")
        elif hasattr(entry, 'updated'):
            st.caption(f"Updated on: {entry.updated}")
            
        if hasattr(entry, 'summary'):
            st.write(entry.summary)
        st.divider()
else:
    st.warning("Unable to reach this specific feed right now. Please select another source from the sidebar menu.")
