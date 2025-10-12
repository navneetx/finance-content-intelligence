#
# MODIFIED AND SECURE: test_channels.py
#
import os
from googleapiclient.discovery import build
from dotenv import load_dotenv

# This line loads the environment variables from your .env file
load_dotenv()

# This now safely reads the API key from the environment.
# It will be read from your .env file locally, or from Vercel's settings when deployed.
API_KEY = os.getenv('YOUTUBE_API_KEY')

# A crucial check to ensure the API key is available.
# The script will stop with a clear error if the key is not found.
if not API_KEY:
    raise ValueError("ERROR: YOUTUBE_API_KEY is not set. Please check your .env file or deployment settings.")

# Test each channel (this part of your code remains the same)
test_channels = {
    'Groww': 'UCvedphyZFjsd2M_RSbuBbDA',
    'Sharan Hegde': 'UC9rkzHvKH92S7tPW8W5j8Zg',
}

print("Building YouTube service...")
youtube = build('youtube', 'v3', developerKey=API_KEY)
print("Service built successfully. Checking channels...")

for name, channel_id in test_channels.items():
    try:
        response = youtube.channels().list(
            part='snippet,contentDetails',
            id=channel_id
        ).execute()
        
        if response.get('items'):
            print(f"✓ {name}: VALID")
        else:
            print(f"✗ {name}: INVALID - No items returned")
    except Exception as e:
        print(f"✗ {name}: ERROR - {e}")