import feedparser
import requests
import ssl
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

NEWS_FEED_URL = "https://aws.amazon.com/about-aws/whats-new/recent/feed/"
BLOG_FEED_URL = "https://aws.amazon.com/blogs/aws/feed/"
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', "https://chat.googleapis.com/v1/spaces/")

def fetch_daily_entries(feed_url):
    feed = feedparser.parse(feed_url)
    cutoff_time = datetime.now() - timedelta(days=1)
    return [e for e in feed.entries if datetime(*e.published_parsed[:6]) >= cutoff_time]

def lambda_handler(event, context):
    ssl._create_default_https_context = ssl._create_unverified_context
    
    # Fetch news updates
    logger.info("Fetching AWS news feed")
    news_entries = fetch_daily_entries(NEWS_FEED_URL)
    logger.info(f"Found {len(news_entries)} news entries from last 24 hours")
    
    if news_entries:
        updates = "\n\n".join([f"• {e.title}\n{e.link}" for e in news_entries])
        message = {"text": f"AWS Daily Updates ({len(news_entries)} new):\n\n{updates}"}
        requests.post(WEBHOOK_URL, json=message)
    
    # Fetch blog updates
    logger.info("Fetching AWS blog feed")
    blog_entries = fetch_daily_entries(BLOG_FEED_URL)
    logger.info(f"Found {len(blog_entries)} blog entries from last 24 hours")
    
    if blog_entries:
        updates = "\n\n".join([f"• {e.title}\n{e.link}" for e in blog_entries])
        message = {"text": f"AWS Daily Blog Updates ({len(blog_entries)} new):\n\n{updates}"}
        requests.post(WEBHOOK_URL, json=message)
    
    return {'statusCode': 200, 'body': f'Posted {len(news_entries)} news + {len(blog_entries)} blog updates'}
