import streamlit as st
import feedparser

# Multiple RSS feeds setup
rss_feeds = {
    "USDA News": "https://www.usda.gov/rss/latest-releases.xml",
    "FAO Ag News": "https://www.fao.org/newsroom/rss/en/"
}

# Sidebar dropdown to choose the source
selected_source = st.sidebar.selectbox("Choose News Source", list(rss_feeds.keys()))
feed_url = rss_feeds[selected_source]
