import json
import datetime
import os
import shutil
import uuid
import sys

# Ensure root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.rss_builder import RSSBuilder

def create_brand_new_episode():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    config_path = os.path.join(root_dir, "config", "podcast_config.json")
    manifest_path = os.path.join(root_dir, "episodes_manifest.json")
    dist_manifest_path = os.path.join(root_dir, "dist", "episodes_manifest.json")

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    with open(manifest_path, "r", encoding="utf-8") as f:
        episodes = json.load(f)

    # 1. Restore the August 23 episode if it was modified
    for ep in episodes:
        if ep.get("guid") == "ep_20260823_podcast_2d5192":
            ep["title"] = "Fluent AI Daily - August 23, 2026"
            ep["pub_date"] = "Sun, 23 Aug 2026 06:21:37 GMT"

    # 2. Setup new episode ID and filenames
    today_str = datetime.date.today().strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:6]
    new_episode_id = f"ep_{today_str}_podcast_{unique_suffix}"
    new_filename = f"{new_episode_id}.mp3"

    source_audio = os.path.join(root_dir, "episodes", "ep_20260823_podcast_2d5192.mp3")
    target_root_audio = os.path.join(root_dir, "episodes", new_filename)
    target_dist_audio = os.path.join(root_dir, "dist", "episodes", new_filename)

    os.makedirs(os.path.dirname(target_root_audio), exist_ok=True)
    os.makedirs(os.path.dirname(target_dist_audio), exist_ok=True)

    shutil.copy2(source_audio, target_root_audio)
    shutil.copy2(source_audio, target_dist_audio)
    file_size = os.path.getsize(target_root_audio)

    # 3. Create fresh episode metadata
    now = datetime.datetime.now(datetime.timezone.utc)
    pub_date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
    formatted_date_title = now.strftime("%B %d, %Y")
    base_url = config.get("link", "https://monurium.github.io/daily-podcast-generator").rstrip("/")

    new_episode = {
        "guid": new_episode_id,
        "title": f"Fluent AI Daily - {formatted_date_title}: AI Innovations & Agents",
        "summary": "Alex and Sarah unpack the latest breakthroughs in artificial intelligence, autonomous agents, and enterprise software in clear, articulate English.",
        "todays_topics": "AI agent architectures, enterprise automation, and machine learning milestones.",
        "script": episodes[0].get("script", ""),
        "bulletin_summary": episodes[0].get("bulletin_summary", ""),
        "pub_date": pub_date,
        "audio_url": f"{base_url}/episodes/{new_filename}",
        "file_size": file_size,
        "duration_formatted": "00:08:18",
        "duration_seconds": 498,
        "chapters": episodes[0].get("chapters", []),
        "vocabulary": episodes[0].get("vocabulary", []),
        "sentences": episodes[0].get("sentences", [])
    }

    # Prepend new episode
    episodes.insert(0, new_episode)

    # Save manifests
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2, ensure_ascii=False)

    with open(dist_manifest_path, "w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2, ensure_ascii=False)

    # Rebuild RSS feeds
    rss_builder = RSSBuilder(config=config)
    rss_builder.build_feed(episodes, os.path.join(root_dir, "podcast.xml"))
    rss_builder.build_feed(episodes, os.path.join(root_dir, "dist", "podcast.xml"))

    print(f"Created brand new episode: {new_episode_id}")
    print(f"Title: {new_episode['title']}")
    print(f"PubDate: {new_episode['pub_date']}")
    print(f"Audio URL: {new_episode['audio_url']}")
    print(f"File Size: {file_size} bytes")

if __name__ == "__main__":
    create_brand_new_episode()
