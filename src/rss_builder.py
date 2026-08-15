import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime, timezone
from typing import Dict, Any, List

class RSSBuilder:
    """Generates and updates Apple Podcasts-compliant RSS 2.0 XML feeds with strict DTD validation standards."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def build_feed(self, episodes: List[Dict[str, Any]], output_xml_path: str):
        """Builds or updates the RSS podcast.xml file."""
        rss = ET.Element("rss", {
            "version": "2.0",
            "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
            "xmlns:content": "http://purl.org/rss/1.0/modules/content/",
            "xmlns:atom": "http://www.w3.org/2005/Atom"
        })

        channel = ET.SubElement(rss, "channel")

        base_url = self.config.get("link", "https://monurium.github.io/daily-podcast-generator").rstrip("/")
        feed_filename = self.config.get("feed_filename", "podcast.xml")
        feed_url = f"{base_url}/{feed_filename}"

        # Atom Self Link for Apple Podcasts feed validation
        ET.SubElement(channel, "atom:link", {
            "href": feed_url,
            "rel": "self",
            "type": "application/rss+xml"
        })

        # Basic Channel Metadata
        ET.SubElement(channel, "title").text = self.config.get("title", "Daily Podcast Digest")
        ET.SubElement(channel, "link").text = base_url
        ET.SubElement(channel, "language").text = self.config.get("language", "en-us")
        ET.SubElement(channel, "description").text = self.config.get("description", "Daily automated audio news bulletin")

        # iTunes Specific Channel Metadata
        ET.SubElement(channel, "itunes:author").text = self.config.get("author", "Monurium")
        ET.SubElement(channel, "itunes:summary").text = self.config.get("description", "")
        ET.SubElement(channel, "itunes:explicit").text = "true" if self.config.get("explicit", False) else "false"

        # iTunes Owner (Mandatory for Spotify & Apple Podcasts validation)
        owner_elem = ET.SubElement(channel, "itunes:owner")
        ET.SubElement(owner_elem, "itunes:name").text = self.config.get("author", "Monurium")
        ET.SubElement(owner_elem, "itunes:email").text = self.config.get("email", "podcast@example.com")

        # Category
        cat_elem = ET.SubElement(channel, "itunes:category", {"text": self.config.get("category", "Technology")})
        if self.config.get("subcategory"):
            ET.SubElement(cat_elem, "itunes:category", {"text": self.config.get("subcategory")})

        # Image
        if self.config.get("cover_image_url"):
            ET.SubElement(channel, "itunes:image", {"href": self.config["cover_image_url"]})
            image_elem = ET.SubElement(channel, "image")
            ET.SubElement(image_elem, "url").text = self.config["cover_image_url"]
            ET.SubElement(image_elem, "title").text = self.config.get("title", "Daily Podcast Digest")
            ET.SubElement(image_elem, "link").text = base_url

        # Add Episode Items
        for ep in episodes:
            item = ET.SubElement(channel, "item")
            ET.SubElement(item, "title").text = ep.get("title")
            ET.SubElement(item, "description").text = ep.get("summary")
            ET.SubElement(item, "pubDate").text = ep.get("pub_date", datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT"))
            ET.SubElement(item, "guid", {"isPermaLink": "false"}).text = ep.get("guid")

            # iTunes Item attributes
            ET.SubElement(item, "itunes:author").text = self.config.get("author", "Monurium")
            ET.SubElement(item, "itunes:duration").text = str(ep.get("duration_formatted", "00:06:00"))
            ET.SubElement(item, "itunes:explicit").text = "false"

            # Enclosure tag (Audio file download link for Apple Podcasts)
            ET.SubElement(item, "enclosure", {
                "url": ep.get("audio_url"),
                "length": str(ep.get("file_size", 0)),
                "type": "audio/mpeg"
            })

        # Format XML cleanly
        xml_str = ET.tostring(rss, encoding="utf-8")
        parsed = minidom.parseString(xml_str)
        pretty_xml = parsed.toprettyxml(indent="  ")
        
        # Clean extra blank lines
        clean_pretty_xml = "\n".join([line for line in pretty_xml.splitlines() if line.strip()])

        dir_name = os.path.dirname(output_xml_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(output_xml_path, "w", encoding="utf-8") as f:
            f.write(clean_pretty_xml)
        
        print(f"Successfully created/updated RSS feed at: {output_xml_path}")
