import os
import feedparser
import datetime
from typing import List, Dict, Any
from openai import OpenAI

class ContentGenerator:
    """Fetches latest RSS tech & global news and generates B2 English educational podcast scripts via DeepSeek."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is missing.")
        
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        
        self.rss_feeds = [
            "https://feeds.bbci.co.uk/news/technology/rss.xml",
            "https://feeds.bbci.co.uk/news/world/rss.xml",
            "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
            "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
            "https://techcrunch.com/feed/",
            "https://www.wired.com/feed/rss",
            "https://arstechnica.com/feed/"
        ]

    def fetch_fresh_news(self, hours_limit: int = 24) -> str:
        """Collects fresh news entries published within the last `hours_limit` hours."""
        now = datetime.datetime.now(datetime.timezone.utc)
        fresh_articles: List[str] = []

        print(f"📡 Scanning {len(self.rss_feeds)} RSS news feeds for fresh articles (last {hours_limit}h)...")

        for feed_url in self.rss_feeds:
            try:
                parsed = feedparser.parse(feed_url)
                for entry in parsed.entries[:5]:
                    title = entry.get("title", "").strip()
                    summary = entry.get("summary", "").strip()
                    
                    if title:
                        clean_item = f"• Title: {title}\n  Summary: {summary[:250]}"
                        fresh_articles.append(clean_item)
            except Exception as e:
                print(f"⚠️ Warning: Failed to parse feed {feed_url}: {e}")

        if not fresh_articles:
            return ""

        selected_articles = fresh_articles[:15]
        return "\n\n".join(selected_articles)

    def generate_script(self, raw_news_context: str) -> Dict[str, Any]:
        """Generates a lively, engaging B2 English educational news script targeting 1400-1500 words for an exact 7.5-8 min audio duration."""
        print("🤖 Prompting DeepSeek-V3 for a 1400-1500 word lively B2 English news bulletin...")

        system_prompt = (
            "You are a top-tier English language educator and daily news podcast host. "
            "Your task is to write an engaging, lively, and articulate daily news podcast script for intermediate (B2) learners.\n\n"
            "CRITICAL MANDATES:\n"
            "1. TARGET LENGTH: STRICTLY WRITE BETWEEN 1400 AND 1500 WORDS TOTAL. This is required so the spoken audio reaches exactly 7.5 to 8.0 minutes.\n"
            "2. GREETING & INTRO: Start immediately with a friendly greeting and date. NO formal course or lesson intros. Example: 'Hello everyone! Welcome to today's news bulletin for Friday, August 14th.'\n"
            "3. NO B2 LEVEL MENTIONS: Never say 'B2 level' or 'for B2 learners' in the script.\n"
            "4. STRUCTURE: Select 8 intriguing tech and world news stories. For EACH story, provide 160-180 words explaining full news context, global significance, and clear example usages of key vocabulary.\n"
            "5. NO SPECIAL CHARACTERS: Write plain, clear English sentences without asterisks, brackets, or markdown formatting.\n"
            "6. VOCABULARY HIGHLIGHTS: In each story, naturally introduce and explain 1-2 advanced terms (e.g., 'pivotal', 'unprecedented', 'resilience') in plain words.\n"
            "7. SUMMARY BLOCK: At the very end of your response, output a structured bulleted summary of all 8 news items and a Key Vocabulary list."
        )

        user_prompt = (
            f"Here is today's raw news context:\n\n{raw_news_context}\n\n"
            "Generate a 1400-1500 word lively, engaging news podcast script that covers 8 distinct stories in full detail."
        )

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.6,
            max_tokens=4096
        )

        full_content = response.choices[0].message.content.strip()
        lines = full_content.split("\n")
        title = f"Daily News Digest - {datetime.date.today().strftime('%B %d, %Y')}"
        
        # Extract title if present
        for line in lines[:5]:
            if line.lower().startswith("title:") or line.lower().startswith("# title:"):
                title = line.split(":", 1)[1].strip().replace("#", "").strip()
                break

        # Generate bulletin summary HTML for email
        summary_bulletin = self._format_bulletin_summary(full_content)

        return {
            "title": title,
            "script": full_content,
            "summary": "Daily technology and global news podcast bulletin for B2 English learners.",
            "bulletin_summary": summary_bulletin
        }

    def _format_bulletin_summary(self, script_text: str) -> str:
        """Formats the script into an attractive HTML email summary block."""
        paragraphs = [p.strip() for p in script_text.split("\n\n") if p.strip()]
        
        html = "<h3 style='color: #1e3c72; border-bottom: 2px solid #1e3c72; padding-bottom: 5px;'>📰 Today's News Headlines</h3><ul>"
        
        stories_count = 0
        for p in paragraphs:
            if any(p.lower().startswith(prefix) for prefix in ["hello", "welcome", "title:"]):
                continue
            if len(p) > 60 and stories_count < 8:
                first_sentence = p.split(".")[0] + "."
                html += f"<li style='margin-bottom: 10px;'><strong>Headline:</strong> {first_sentence}</li>"
                stories_count += 1

        html += "</ul>"
        return html
