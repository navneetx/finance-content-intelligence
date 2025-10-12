"""
YouTube Finance Content Scraper - EXPANDED VERSION
Scrapes 15 channels × 60 videos = 900 videos total
Uses ~1,500 API quota units (15% of daily limit)
"""

import os
import json
import time
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Replace with YOUR YouTube API key
API_KEY = 'AIzaSyAyZublNWJbh244W-DZwYRJlgBR0G2jsmE'

# Expanded list of 15 finance channels
FINANCE_CHANNELS = [
    'Groww',
    'Finance with Sharan',
    'Akshat Shrivastava',
    'Pranjal Kamra',
    'CA Rachana Ranade',
    'Labour Law Advisor',
    'Ankur Warikoo',
    'ETMONEY',
    'Zerodha',
    'Nikhil Kamath',
    'Sahil Bloom India',
    'Power of Stocks',
    'Parimal Ade',
    'Investment Insights',
    'FinnovationZ',
]

def get_youtube_service():
    """Initialize YouTube API service"""
    return build('youtube', 'v3', developerKey=API_KEY)

def find_channel_by_name(youtube, channel_name):
    """Find channel ID by searching for channel name"""
    try:
        search_response = youtube.search().list(
            q=channel_name,
            type='channel',
            part='id,snippet',
            maxResults=1
        ).execute()
        
        if search_response.get('items'):
            channel_id = search_response['items'][0]['id']['channelId']
            actual_name = search_response['items'][0]['snippet']['title']
            print(f"  Found: {actual_name}")
            return channel_id, actual_name
        return None, None
    except HttpError as e:
        print(f"  Error finding channel: {e}")
        return None, None

def get_channel_videos(youtube, channel_id, max_results=60):
    """Fetch recent videos from a channel"""
    try:
        # Get uploads playlist ID
        channel_response = youtube.channels().list(
            part='contentDetails',
            id=channel_id
        ).execute()
        
        if not channel_response.get('items'):
            print(f"  ⚠ No channel data found")
            return []
        
        playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
        
        # Get videos from uploads playlist
        videos = []
        next_page_token = None
        
        while len(videos) < max_results:
            request = youtube.playlistItems().list(
                part='snippet',
                playlistId=playlist_id,
                maxResults=min(50, max_results - len(videos)),  # API max is 50 per request
                pageToken=next_page_token
            )
            
            response = request.execute()
            videos.extend(response['items'])
            
            next_page_token = response.get('nextPageToken')
            if not next_page_token or len(videos) >= max_results:
                break
            
            time.sleep(0.3)  # Small delay between pagination requests
        
        return videos[:max_results]
    
    except HttpError as e:
        print(f"  Error fetching videos: {e}")
        return []
    except KeyError as e:
        print(f"  Error parsing response: {e}")
        return []

def get_video_stats(youtube, video_ids):
    """Get detailed stats for videos in batches of 50"""
    try:
        stats = []
        # API allows max 50 IDs per request
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i+50]
            response = youtube.videos().list(
                part='statistics,contentDetails,snippet',
                id=','.join(batch)
            ).execute()
            stats.extend(response['items'])
            time.sleep(0.5)  # Small delay between batches
        return stats
    except HttpError as e:
        print(f"  Error fetching stats: {e}")
        return []

def parse_duration(duration):
    """Convert ISO 8601 duration to seconds"""
    import re
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if not match:
        return 0
    hours, minutes, seconds = match.groups()
    hours = int(hours) if hours else 0
    minutes = int(minutes) if minutes else 0
    seconds = int(seconds) if seconds else 0
    return hours * 3600 + minutes * 60 + seconds

def scrape_all_channels(max_videos_per_channel=60):
    """Main scraping function"""
    youtube = get_youtube_service()
    all_data = []
    
    print("=" * 70)
    print("YouTube Finance Content Scraper - EXPANDED")
    print("=" * 70)
    print(f"Target: {len(FINANCE_CHANNELS)} channels")
    print(f"Videos per channel: {max_videos_per_channel}")
    print(f"Expected total: {len(FINANCE_CHANNELS) * max_videos_per_channel} videos")
    print(f"Estimated API quota usage: ~{len(FINANCE_CHANNELS) * 102} units")
    print("=" * 70 + "\n")
    
    successful_channels = 0
    failed_channels = []
    
    for idx, channel_name in enumerate(FINANCE_CHANNELS, 1):
        print(f"[{idx}/{len(FINANCE_CHANNELS)}] Processing: {channel_name}")
        
        # Find channel ID by name
        channel_id, actual_name = find_channel_by_name(youtube, channel_name)
        if not channel_id:
            print(f"  ✗ Could not find channel\n")
            failed_channels.append(channel_name)
            continue
        
        # Get video list
        print(f"  Fetching {max_videos_per_channel} videos...")
        videos = get_channel_videos(youtube, channel_id, max_videos_per_channel)
        if not videos:
            print(f"  ✗ No videos found\n")
            failed_channels.append(channel_name)
            continue
        
        video_ids = [v['snippet']['resourceId']['videoId'] for v in videos]
        
        # Get detailed stats
        print(f"  Getting statistics for {len(video_ids)} videos...")
        stats = get_video_stats(youtube, video_ids)
        
        if not stats:
            print(f"  ✗ Could not fetch video stats\n")
            failed_channels.append(channel_name)
            continue
        
        # Process and store data
        videos_added = 0
        for stat in stats:
            try:
                video_data = {
                    'video_id': stat['id'],
                    'channel': actual_name,
                    'title': stat['snippet']['title'],
                    'description': stat['snippet']['description'][:200],
                    'published_at': stat['snippet']['publishedAt'],
                    'views': int(stat['statistics'].get('viewCount', 0)),
                    'likes': int(stat['statistics'].get('likeCount', 0)),
                    'comments': int(stat['statistics'].get('commentCount', 0)),
                    'duration_seconds': parse_duration(stat['contentDetails']['duration']),
                    'thumbnail': stat['snippet']['thumbnails']['high']['url'],
                    'url': f"https://youtube.com/watch?v={stat['id']}"
                }
                all_data.append(video_data)
                videos_added += 1
            except KeyError as e:
                continue
        
        successful_channels += 1
        print(f"  ✓ Added {videos_added} videos")
        print(f"  Running total: {len(all_data)} videos\n")
        
        # Rate limiting: pause between channels
        if idx < len(FINANCE_CHANNELS):
            time.sleep(2)
    
    # Save to JSON
    if all_data:
        output_file = f'finance_content_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        print("=" * 70)
        print("✓ SCRAPING COMPLETE!")
        print("=" * 70)
        print(f"Successful channels: {successful_channels}/{len(FINANCE_CHANNELS)}")
        print(f"Total videos collected: {len(all_data)}")
        print(f"Data saved to: {output_file}")
        
        if failed_channels:
            print(f"\n⚠ Failed channels ({len(failed_channels)}): {', '.join(failed_channels)}")
        
        print("=" * 70)
        
        # Print summary stats
        print("\n📊 SUMMARY BY CHANNEL:")
        print("-" * 70)
        channel_counts = {}
        for video in all_data:
            channel = video['channel']
            channel_counts[channel] = channel_counts.get(channel, 0) + 1
        
        for channel, count in sorted(channel_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {channel}: {count} videos")
        
        return all_data
    else:
        print("\n✗ No data collected. Please check your API key and internet connection.")
        return []

def calculate_engagement_rate(video):
    """Calculate engagement score"""
    if video['views'] == 0:
        return 0
    return ((video['likes'] + video['comments']) / video['views']) * 100

def analyze_data(data):
    """Quick analysis of collected data"""
    if not data:
        return
    
    print("\n" + "=" * 70)
    print("📈 QUICK ANALYSIS")
    print("=" * 70)
    
    # Top videos by views
    print("\n🔥 TOP 10 VIDEOS BY VIEWS:")
    print("-" * 70)
    top_views = sorted(data, key=lambda x: x['views'], reverse=True)[:10]
    for i, video in enumerate(top_views, 1):
        print(f"\n{i}. {video['title'][:65]}...")
        print(f"   Channel: {video['channel']}")
        print(f"   Views: {video['views']:,} | Likes: {video['likes']:,}")
        print(f"   Duration: {video['duration_seconds']//60}m {video['duration_seconds']%60}s")
    
    # Top videos by engagement
    print("\n\n💎 TOP 10 VIDEOS BY ENGAGEMENT RATE:")
    print("-" * 70)
    top_engagement = sorted(data, key=calculate_engagement_rate, reverse=True)[:10]
    for i, video in enumerate(top_engagement, 1):
        engagement = calculate_engagement_rate(video)
        print(f"\n{i}. {video['title'][:65]}...")
        print(f"   Channel: {video['channel']}")
        print(f"   Engagement Rate: {engagement:.2f}%")
        print(f"   Views: {video['views']:,} | Likes: {video['likes']:,}")
    
    # Average stats
    print("\n\n📊 OVERALL STATISTICS:")
    print("-" * 70)
    avg_views = sum(v['views'] for v in data) / len(data)
    avg_likes = sum(v['likes'] for v in data) / len(data)
    avg_comments = sum(v['comments'] for v in data) / len(data)
    avg_duration = sum(v['duration_seconds'] for v in data) / len(data)
    avg_engagement = sum(calculate_engagement_rate(v) for v in data) / len(data)
    
    print(f"  Total Videos: {len(data)}")
    print(f"  Average Views: {avg_views:,.0f}")
    print(f"  Average Likes: {avg_likes:,.0f}")
    print(f"  Average Comments: {avg_comments:,.0f}")
    print(f"  Average Duration: {avg_duration//60:.0f}m {avg_duration%60:.0f}s")
    print(f"  Average Engagement Rate: {avg_engagement:.2f}%")
    
    # Duration distribution
    print("\n\n⏱ VIDEO LENGTH DISTRIBUTION:")
    print("-" * 70)
    short = len([v for v in data if v['duration_seconds'] < 300])
    medium = len([v for v in data if 300 <= v['duration_seconds'] < 600])
    long = len([v for v in data if 600 <= v['duration_seconds'] < 900])
    very_long = len([v for v in data if v['duration_seconds'] >= 900])
    
    print(f"  0-5 minutes: {short} ({short/len(data)*100:.1f}%)")
    print(f"  5-10 minutes: {medium} ({medium/len(data)*100:.1f}%)")
    print(f"  10-15 minutes: {long} ({long/len(data)*100:.1f}%)")
    print(f"  15+ minutes: {very_long} ({very_long/len(data)*100:.1f}%)")

# Main execution
if __name__ == "__main__":
    try:
        # Check if API key is set
        if API_KEY == 'YOUR_YOUTUBE_API_KEY_HERE':
            print("❌ ERROR: Please set your YouTube API key in the script!")
            print("Find this line: API_KEY = 'YOUR_YOUTUBE_API_KEY_HERE'")
            print("Replace with your actual key from Google Cloud Console")
            exit(1)
        
        # Run scraper
        print("Starting in 3 seconds... (Press Ctrl+C to cancel)\n")
        time.sleep(3)
        
        data = scrape_all_channels(max_videos_per_channel=60)
        
        # Analyze results
        if data:
            analyze_data(data)
            print("\n" + "=" * 70)
            print("✅ SUCCESS! You now have a comprehensive dataset.")
            print("Copy the JSON file to your dashboard's src/data/ folder")
            print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()