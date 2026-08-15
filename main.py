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
    dialogue_script_data = content_gen.generate_dialogue_script(raw_news)

    # Save script texts locally
    os.makedirs("output", exist_ok=True)
    script_file_path = os.path.join("output", "b2_script.txt")
    dialogue_file_path = os.path.join("output", "dialogue_script.txt")
    
    with open(script_file_path, "w", encoding="utf-8") as f:
        f.write(script_data["script"])
    with open(dialogue_file_path, "w", encoding="utf-8") as f:
        f.write(dialogue_script_data["script"])
        
    print(f"📄 Monologue Script saved to: {script_file_path}")
    print(f"📄 Dialogue Script saved to: {dialogue_file_path}")

    # 3. Audio Synthesis (Dual-Engine: Google AI Studio Primary with Edge-TTS Backup)
    audio_gen = AudioGenerator()
    today_str = datetime.date.today().strftime('%Y%m%d')
    pub_date = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    publisher = Publisher(output_dir=output_dir)

    # --- 3a. Synthesize Monologue Episode ---
    mono_episode_id = f"ep_{today_str}_mono_{uuid.uuid4().hex[:6]}"
    temp_mono_path = os.path.join("output", "temp", f"{mono_episode_id}.mp3")
    print("\n[Step 2a/5] Synthesizing 7-8 min MP3 audio monologue...")
    mono_audio_meta = audio_gen.text_to_audio(script_data["script"], temp_mono_path)

    mono_episode_meta = {
        "id": mono_episode_id,
        "title": script_data["title"] + " (Monologue)",
        "summary": script_data["summary"],
        "script": script_data["script"],
        "bulletin_summary": script_data.get("bulletin_summary", script_data["summary"]),
        "pub_date": pub_date,
        "file_size": mono_audio_meta["file_size"],
        "duration_formatted": mono_audio_meta["duration_formatted"]
    }
    publisher.add_episode(mono_episode_meta, temp_mono_path, base_url)

    # --- 3b. Synthesize 2-Host Dialogue Podcast Episode ---
    dialogue_episode_id = f"ep_{today_str}_podcast_{uuid.uuid4().hex[:6]}"
    temp_dialogue_path = os.path.join("output", "temp", f"{dialogue_episode_id}.mp3")
    print("\n[Step 2b/5] Synthesizing 2-Host (Alex & Sarah) MP3 audio podcast conversation...")
    dialogue_audio_meta = audio_gen.dialogue_to_audio(dialogue_script_data["script"], temp_dialogue_path)

    dialogue_episode_meta = {
        "id": dialogue_episode_id,
        "title": dialogue_script_data["title"],
        "summary": dialogue_script_data["summary"],
        "script": dialogue_script_data["script"],
        "bulletin_summary": dialogue_script_data.get("bulletin_summary", dialogue_script_data["summary"]),
        "pub_date": pub_date,
        "file_size": dialogue_audio_meta["file_size"],
        "duration_formatted": dialogue_audio_meta["duration_formatted"]
    }
    all_episodes = publisher.add_episode(dialogue_episode_meta, temp_dialogue_path, base_url)

    # 4. RSS XML Feed Generation for Apple Podcasts
    print("\n[Step 4/5] Updating Apple Podcasts RSS feed (podcast.xml)...")
    rss_builder = RSSBuilder(config=config)
    rss_path = os.path.join(output_dir, config.get("feed_filename", "podcast.xml"))
    rss_builder.build_feed(all_episodes, rss_path)

    # 5. Optional Email Delivery with Audio Attachment & News Summaries
    print("\n[Step 5/5] Checking email delivery configuration...")
    email_sender = EmailSender()
    email_sender.send_podcast_email(dialogue_episode_meta, temp_dialogue_path)

    print("\n" + "=" * 60)
    print("🎉 SUCCESS: Monologue & 2-Host Podcast episodes generated, RSS updated & email processed!")
    print(f"Feed path: {rss_path}")
    print(f"Feed URL: {base_url.rstrip('/')}/{config.get('feed_filename', 'podcast.xml')}")
    print("=" * 60)

if __name__ == "__main__":
    run_daily_podcast_pipeline()
