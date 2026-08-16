import os
import shutil
import json
import uuid
import datetime
from dotenv import load_dotenv

from src.content_generator import ContentGenerator
from src.audio_generator import AudioGenerator
from src.rss_builder import RSSBuilder
from src.publisher import Publisher
import argparse
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

def run_daily_podcast_pipeline(test_mode: bool = False):
    print("=" * 60)
    if test_mode:
        print("🧪 RUNNING IN TEST / DRY-RUN MODE (Spotify & RSS will NOT be updated)")
    else:
        print("🎙️ Starting AI Pulse Daily Podcast Generation & Publishing Pipeline")
    print("=" * 60)

    # 1. Load Configurations
    config_path = os.path.join("config", "podcast_config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    base_url = os.getenv("PODCAST_BASE_URL", config.get("link", "https://monurium.github.io/daily-podcast-generator"))
    output_dir = config.get("output_dir", "dist")

    # 2. Fetch Fresh News & Generate Script via DeepSeek
    print("\n[Step 1/3] Fetching latest AI & Tech news (last 24 hours)...")
    content_gen = ContentGenerator()
    raw_news = content_gen.fetch_fresh_news(hours_limit=24)

    if not raw_news:
        print("⚠️ No fresh news found in the last 24 hours. Using default feed topics.")
        raw_news = "Global developments in artificial intelligence, technology, and future innovations."

    script_data = content_gen.generate_script(raw_news)
    dialogue_script_data = content_gen.generate_dialogue_script(raw_news)

    # Save script texts locally
    os.makedirs("output", exist_ok=True)
    script_file_path = os.path.join("output", "monologue_script.txt")
    dialogue_file_path = os.path.join("output", "dialogue_script.txt")
    
    with open(script_file_path, "w", encoding="utf-8") as f:
        f.write(script_data["script"])
    with open(dialogue_file_path, "w", encoding="utf-8") as f:
        f.write(dialogue_script_data["script"])
        
    print(f"📄 Monologue Script saved to: {script_file_path}")
    print(f"📄 Dialogue Script saved to: {dialogue_file_path}")

    # 3. Audio Synthesis (Alex: Male & Sarah: Female)
    audio_gen = AudioGenerator()
    today_str = datetime.date.today().strftime('%Y%m%d')
    pub_date = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    if test_mode:
        print("\n[Step 2/3] 🧪 Synthesizing 2-Host Test Episode (Alex: Male & Sarah: Female)...")
        test_audio_path = os.path.join("output", "test_dialogue_podcast.mp3")
        dialogue_audio_meta = audio_gen.dialogue_to_audio(dialogue_script_data["script"], test_audio_path)

        print("\n[Step 3/3] 🧪 Building Isolated Test RSS Feed & Manifest in ./output/...")
        test_publisher = Publisher(output_dir="output")
        test_episode_meta = {
            "id": "ep_test_dialogue",
            "title": "[TEST] " + dialogue_script_data["title"],
            "summary": dialogue_script_data["summary"],
            "script": dialogue_script_data["script"],
            "pub_date": pub_date,
            "file_size": dialogue_audio_meta["file_size"],
            "duration_formatted": dialogue_audio_meta["duration_formatted"],
            "chapters": dialogue_script_data.get("chapters", []),
            "vocabulary": dialogue_script_data.get("vocabulary", [])
        }
        test_episodes = test_publisher.add_episode(test_episode_meta, test_audio_path, base_url)

        test_rss_builder = RSSBuilder(config=config)
        test_xml_path = os.path.join("output", "test_podcast.xml")
        test_rss_builder.build_feed(test_episodes, test_xml_path)

        print("\n" + "=" * 60)
        print("🎉 ISOLATED TEST COMPLETED SUCCESSFULLY!")
        print(f"📄 Test Script: {dialogue_file_path}")
        print(f"🎧 Test Audio MP3: {test_audio_path}")
        print(f"📡 Test RSS Feed XML: {test_xml_path}")
        print("🛡️ Production podcast.xml, dist/ and episodes/ were NOT modified.")
        print("=" * 60)
        return

    # --- Production Publishing Mode ---
    publisher = Publisher(output_dir=output_dir)

    # 3. Synthesize Primary 2-Host Dialogue Podcast Episode
    dialogue_episode_id = f"ep_{today_str}_podcast_{uuid.uuid4().hex[:6]}"
    temp_dialogue_path = os.path.join("output", "temp", f"{dialogue_episode_id}.mp3")
    print("\n[Step 2/3] Synthesizing Primary 2-Host (Alex: Male & Sarah: Female) MP3 podcast...")

    try:
        dialogue_audio_meta = audio_gen.dialogue_to_audio(dialogue_script_data["script"], temp_dialogue_path)
        all_episodes = publisher.add_episode({
            "id": dialogue_episode_id,
            "title": dialogue_script_data["title"],
            "summary": dialogue_script_data["summary"],
            "script": dialogue_script_data["script"],
            "bulletin_summary": dialogue_script_data.get("bulletin_summary", dialogue_script_data["summary"]),
            "pub_date": pub_date,
            "file_size": dialogue_audio_meta["file_size"],
            "duration_formatted": dialogue_audio_meta["duration_formatted"],
            "chapters": dialogue_script_data.get("chapters", []),
            "vocabulary": dialogue_script_data.get("vocabulary", []),
            "sentences": dialogue_script_data.get("sentences", [])
        }, temp_dialogue_path, base_url)
    except Exception as dialogue_err:
        print(f"⚠️ Primary Dialogue Podcast synthesis failed ({dialogue_err}). Falling back to Monologue Backup...")
        mono_episode_id = f"ep_{today_str}_mono_{uuid.uuid4().hex[:6]}"
        temp_mono_path = os.path.join("output", "temp", f"{mono_episode_id}.mp3")
        mono_audio_meta = audio_gen.text_to_audio(script_data["script"], temp_mono_path)
        all_episodes = publisher.add_episode({
            "id": mono_episode_id,
            "title": script_data["title"],
            "summary": script_data["summary"],
            "script": script_data["script"],
            "bulletin_summary": script_data.get("bulletin_summary", script_data["summary"]),
            "pub_date": pub_date,
            "file_size": mono_audio_meta["file_size"],
            "duration_formatted": mono_audio_meta["duration_formatted"],
            "chapters": script_data.get("chapters", []),
            "vocabulary": script_data.get("vocabulary", []),
            "sentences": script_data.get("sentences", [])
        }, temp_mono_path, base_url)


    # 4. RSS XML Feed Generation for Spotify & Apple Podcasts
    print("\n[Step 3/3] Updating Spotify & Apple Podcasts RSS feeds & Web Landing Page...")
    rss_builder = RSSBuilder(config=config)
    rss_dist_path = os.path.join(output_dir, config.get("feed_filename", "podcast.xml"))
    rss_root_path = config.get("feed_filename", "podcast.xml")
    
    rss_builder.build_feed(all_episodes, rss_dist_path)
    rss_builder.build_feed(all_episodes, rss_root_path)

    # Copy web landing page and cover artwork to dist
    if os.path.exists("index.html"):
        shutil.copy2("index.html", os.path.join(output_dir, "index.html"))
    if os.path.exists("cover.jpg"):
        shutil.copy2("cover.jpg", os.path.join(output_dir, "cover.jpg"))

    print("\n" + "=" * 60)
    print("🎉 SUCCESS: Podcast episode generated and RSS feeds updated for Spotify!")
    print(f"Feed path: {rss_root_path}")
    print(f"Feed URL: {base_url.rstrip('/')}/{config.get('feed_filename', 'podcast.xml')}")
    print(f"Web Player URL: {base_url.rstrip('/')}/")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Pulse Daily Podcast Pipeline")
    parser.add_argument("--test", "--dry-run", action="store_true", help="Run in local test mode without updating Spotify/RSS feeds")
    args = parser.parse_args()

    run_daily_podcast_pipeline(test_mode=args.test)
