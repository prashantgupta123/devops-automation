import feedparser
import requests
import ssl
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

FEED_URL = "https://aws.amazon.com/about-aws/whats-new/recent/feed/"
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', "https://chat.googleapis.com/v1/spaces/")

def lambda_handler(event, context):
    ssl._create_default_https_context = ssl._create_unverified_context
    logger.info("Fetching AWS news feed")
    feed = feedparser.parse(FEED_URL)
    logger.info(f"Found {len(feed.entries)} entries")
    
    # Filter entries from last 24 hours
    cutoff_time = datetime.now() - timedelta(days=1)
    daily_entries = []
    for entry in feed.entries:
        published = datetime(*entry.published_parsed[:6])
        if published >= cutoff_time:
            daily_entries.append(entry)
    
    logger.info(f"Found {len(daily_entries)} entries from last 24 hours")
    
    if daily_entries:
        updates = "\n\n".join([f"• {e.title}\n{e.link}" for e in daily_entries])
        message = {"text": f"AWS Daily Updates ({len(daily_entries)} new):\n\n{updates}"}
        logger.info(f"Posting {len(daily_entries)} updates")
        response = requests.post(WEBHOOK_URL, json=message)
        logger.info(f"Webhook response: {response.status_code}")
        return {'statusCode': 200, 'body': f'Posted {len(daily_entries)} updates'}
    else:
        logger.info("No new updates in the last 24 hours")
        return {'statusCode': 200, 'body': 'No new updates'}
