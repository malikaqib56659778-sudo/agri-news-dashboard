import streamlit as st
import feedparser

# App Title
st.title("🌾 Agricultural News Dashboard")

# Multiple RSS feeds setup
rss_feeds = {
    "USDA News": "https://www.usda.gov/rss/latest-releases.xml",
    "FAO Ag News": "https://www.fao.org/newsroom/rss/en/"
}

# Sidebar dropdown to choose the source
selected_source = st.sidebar.selectbox("Choose News Source", list(rss_feeds.keys()))
feed_url = rss_feeds[selected_source]

# Fetch RSS Feed with Request Headers
st.subheader(f"Latest Updates from {selected_source}")

# Passing agent headers prevents RSS servers from blocking Streamlit requests
feed = feedparser.parse(feed_url, request_headers={'User-Agent': 'Mozilla/5.0'})

if feed.entries:
    for entry in feed.entries[:10]:  # Displays the latest 10 articles
        st.markdown(f"### [{entry.title}]({entry.link})")
        if 'published' in entry:
            st.caption(f"Published on: {entry.published}")
        if 'summary' in entry:
            st.write(entry.summary)
        st.divider()
else:
    st.warning("No articles found or the feed is currently unavailable. Try switching sources in the sidebar.")
