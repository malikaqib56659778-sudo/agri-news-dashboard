import streamlit as st
import feedparser
import ollama

# Page Configuration
st.set_page_config(page_title="Agri News Daily", page_icon="🌾", layout="wide")

st.title("🌾 Agri News AI Summary Dashboard")
st.write("Fetch latest agricultural updates summarized by local AI.")

# Sidebar Options
st.sidebar.header("Feed Settings")
feed_url = st.sidebar.text_input(
    "RSS Feed URL", 
    value="https://www.usda.gov/rss/latest-releases.xml"
)
num_articles = st.sidebar.slider("Number of articles to fetch", 1, 10, 3)

# Main Button to Run
if st.button("Fetch & Summarize News"):
    with st.spinner("Fetching news feeds..."):
        feed = feedparser.parse(feed_url)
        articles = feed.entries[:num_articles]

    if not articles:
        st.warning("No articles found.")
    else:
        for item in articles:
            st.subheader(item.title)
            st.caption(f"Source: {item.link}")
            
            # AI Summarization using local Ollama
            with st.spinner("Generating AI Summary..."):
                prompt = f"Summarize this agricultural news story in 2 concise bullet points:\n\nTitle: {item.title}\nContent: {item.get('summary', '')}"
                response = ollama.chat(
                    model='llama3.2:1b', 
                    messages=[{'role': 'user', 'content': prompt}]
                )
                summary = response['message']['content']
            
            st.markdown(summary)
            st.markdown("---")