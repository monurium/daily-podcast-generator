import os
import json
import uuid
import datetime
from dotenv import load_dotenv

from src.content_generator import ContentGenerator
from src.audio_generator import AudioGenerator
from src.rss_builder import RSSBuilder
from src.publisher import Publisher

load_dotenv()

def run_daily_podcast_pipeline():
    print("=" * 50)
    print("Starting Daily Podcast Generation & Publishing Pipeline")
    print("=" * 50)

    # 1. Load Configurations
    config_path = os.path.join("config", "podcast_config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    base_url = os.getenv("PODCAST_BASE_URL", config.get("link", "https://monurium.github.io/daily-podcast-generator"))
    output_dir = config.get("output_dir", "dist")

    # 2. Content Generation
    print("\n[Step 1/4] Generating daily episode script...")
    content_gen = ContentGenerator()
    script_data = content_gen.generate_daily_script()
    print(f"Title: {script_data['title']}")
    print(f"Summary: {script_data['summary']}")

    # 3. Audio Synthesis (TTS)
    episode_id = f"ep_{datetime.date.today().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}"
    temp_audio_path = os.path.join("output", "temp", f"{episode_id}.mp3")

    print("\n[Step 2/4] Synthesizing MP3 speech audio...")
    audio_gen = AudioGenerator()
    audio_meta = audio_gen.text_to_audio(script_data["script"], temp_audio_path)
    print(f"Audio generated successfully ({audio_meta['file_size']} bytes, duration: {audio_meta['duration_formatted']})")

    # 4. Publication & Manifest Sync
    print("\n[Step 3/4] Publishing episode and updating manifest...")
    publisher = Publisher(output_dir=output_dir)
    pub_date = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    episode_meta = {
        "id": episode_id,
        "title": script_data["title"],
        "summary": script_data["summary"],
        "script": script_data["script"],
        "pub_date": pub_date,
        "file_size": audio_meta["file_size"],
        "duration_formatted": audio_meta["duration_formatted"]
    }

    all_episodes = publisher.add_episode(episode_meta, temp_audio_path, base_url)

    # 5. RSS XML Feed Generation for Apple Podcasts
    print("\n[Step 4/4] Updating Apple Podcasts RSS feed (podcast.xml)...")
    rss_builder = RSSBuilder(config=config)
    rss_path = os.path.join(output_dir, config.get("feed_filename", "podcast.xml"))
    rss_builder.build_feed(all_episodes, rss_path)

    print("\n" + "=" * 50)
    print("SUCCESS: Podcast episode generated and Apple Podcasts RSS feed updated!")
    print(f"Feed path: {rss_path}")
    print(f"Feed URL target: {base_url.rstrip('/')}/{config.get('feed_filename', 'podcast.xml')}")
    print("=" * 50)

if __name__ == "__main__":
    run_daily_podcast_pipeline()
