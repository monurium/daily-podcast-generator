import json
import datetime
import os
import sys
from src.rss_builder import RSSBuilder

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def update_latest_episode_date():
    config_path = os.path.join("config", "podcast_config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    with open("episodes_manifest.json", "r", encoding="utf-8") as f:
        episodes = json.load(f)

    now = datetime.datetime.now(datetime.timezone.utc)
    new_pub_date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
    formatted_date_title = now.strftime("%B %d, %Y")

    print(f"Old Title: {episodes[0]['title']}")
    print(f"Old Date:  {episodes[0]['pub_date']}")

    episodes[0]["pub_date"] = new_pub_date
    episodes[0]["title"] = f"Fluent AI Daily - {formatted_date_title}"

    print(f"New Title: {episodes[0]['title']}")
    print(f"New Date:  {episodes[0]['pub_date']}")

    with open("episodes_manifest.json", "w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2, ensure_ascii=False)

    os.makedirs("dist", exist_ok=True)
    with open(os.path.join("dist", "episodes_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2, ensure_ascii=False)

    rss_builder = RSSBuilder(config=config)
    rss_builder.build_feed(episodes, "podcast.xml")
    rss_builder.build_feed(episodes, os.path.join("dist", "podcast.xml"))
    print("\nRSS feed and manifest successfully updated!")

if __name__ == "__main__":
    update_latest_episode_date()
