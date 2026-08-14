import os
import json
import uuid
import datetime
from dotenv import load_dotenv

from src.content_generator import ContentGenerator
from src.audio_generator import AudioGenerator
from src.rss_builder import RSSBuilder
from src.publisher import Publisher
from src.email_sender import EmailSender

load_dotenv()

def run_daily_podcast_pipeline():
    print("=" * 60)
    print("🎙️ Starting B2 English Daily News Podcast Generation Pipeline")
    print("=" * 60)

    # 1. Load Configurations
    config_path = os.path.join("config", "podcast_config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    base_url = os.getenv("PODCAST_BASE_URL", config.get("link", "https://monurium.github.io/daily-podcast-generator"))
    output_dir = config.get("output_dir", "dist")

    # 2. Fetch Fresh News & Generate Script via DeepSeek
    print("\n[Step 1/5] Fetching latest RSS news (last 24 hours)...")
    content_gen = ContentGenerator()
    raw_news = content_gen.fetch_fresh_news(hours_limit=24)

    if not raw_news:
        print("⚠️ No fresh news found in the last 24 hours. Using default feed topics.")
        raw_news = "Global developments in technology, environment, and economy continue to evolve today."

    script_data = content_gen.generate_script(raw_news)

    # Save script text locally
    os.makedirs("output", exist_ok=True)
    script_file_path = os.path.join("output", "b2_script.txt")
    with open(script_file_path, "w", encoding="utf-8") as f:
        f.write(script_data["script"])
    print(f"📄 Script saved to: {script_file_path}")

    # 3. Audio Synthesis (Multi-Host Edge-TTS)
    episode_id = f"ep_{datetime.date.today().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}"
    temp_audio_path = os.path.join("output", "temp", f"{episode_id}.mp3")

    print("\n[Step 2/5] Synthesizing MP3 audio with hosts Alex & Sam...")
    audio_gen = AudioGenerator()
    audio_meta = audio_gen.text_to_audio(script_data["script"], temp_audio_path)

    # 4. Publication & Manifest Sync
    print("\n[Step 3/5] Publishing episode to distribution directory...")
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
    print("\n[Step 4/5] Updating Apple Podcasts RSS feed (podcast.xml)...")
    rss_builder = RSSBuilder(config=config)
    rss_path = os.path.join(output_dir, config.get("feed_filename", "podcast.xml"))
    rss_builder.build_feed(all_episodes, rss_path)

    # 6. Optional Email Delivery with MP3 Attachment
    print("\n[Step 5/5] Checking email delivery configuration...")
    email_sender = EmailSender()
    email_sender.send_podcast_email(episode_meta, temp_audio_path)

    print("\n" + "=" * 60)
    print("🎉 SUCCESS: Daily B2 podcast episode generated, RSS updated & email processed!")
    print(f"Feed path: {rss_path}")
    print(f"Feed URL: {base_url.rstrip('/')}/{config.get('feed_filename', 'podcast.xml')}")
    print("=" * 60)

if __name__ == "__main__":
    run_daily_podcast_pipeline()
