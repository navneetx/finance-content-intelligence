from googleapiclient.discovery import build

API_KEY = 'AIzaSyAyZublNWJbh244W-DZwYRJlgBR0G2jsmE'

# Test each channel
test_channels = {
    'Groww': 'UCvedphyZFjsd2M_RSbuBbDA',
    'Sharan Hegde': 'UC9rkzHvKH92S7tPW8W5j8Zg',
}

youtube = build('youtube', 'v3', developerKey=API_KEY)

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