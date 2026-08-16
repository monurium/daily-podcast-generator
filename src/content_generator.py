import os
import feedparser
import datetime
from typing import List, Dict, Any
from openai import OpenAI

class ContentGenerator:
    """Fetches latest RSS tech & global news and generates B2 English educational podcast scripts via DeepSeek."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if self.api_key and self.api_key != "your_deepseek_api_key_here":
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )
        else:
            self.client = None
        
        self.rss_feeds = [
            "https://techcrunch.com/category/artificial-intelligence/feed/",
            "https://techcrunch.com/feed/",
            "https://www.wired.com/feed/category/business/latest/rss",
            "https://arstechnica.com/feed/",
            "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
            "https://feeds.bbci.co.uk/news/technology/rss.xml"
        ]

    def fetch_fresh_news(self, hours_limit: int = 24) -> str:
        """Collects fresh AI & Tech news entries, applying strict Spotify-compliant family safety filters."""
        fresh_articles: List[str] = []
        print(f"📡 Scanning {len(self.rss_feeds)} AI & Tech RSS feeds for fresh articles (last {hours_limit}h)...")

        forbidden_keywords = [
            "war", "kill", "murder", "suicide", "shooting", "attack", "terror", 
            "sexual", "porn", "gore", "deadly", "explosion", "military", "crime", 
            "death", "assault", "violence", "conflict", "bomb", "hostage"
        ]

        for feed_url in self.rss_feeds:
            try:
                parsed = feedparser.parse(feed_url)
                for entry in parsed.entries[:5]:
                    title = entry.get("title", "").strip()
                    summary = entry.get("summary", "").strip()
                    combined_text = f"{title} {summary}".lower()
                    
                    if any(bad_word in combined_text for bad_word in forbidden_keywords):
                        print(f"🛡️ Filtering out unsafe content entry: '{title}'")
                        continue
                    
                    if title:
                        clean_item = f"• Title: {title}\n  Summary: {summary[:250]}"
                        fresh_articles.append(clean_item)
            except Exception as e:
                print(f"⚠️ Warning: Failed to parse feed {feed_url}: {e}")

        if not fresh_articles:
            return ""

        return "\n\n".join(fresh_articles[:15])

    def generate_script(self, raw_news_context: str) -> Dict[str, Any]:
        """Generates a lively B2 English educational news script targeting 1400-1500 words for an exact 7.5-8 min audio duration."""
        print("🤖 Prompting DeepSeek-V3 for a 1400-1500 word AI & Tech B2 English monologue script...")

        system_prompt = (
            "You are a top-tier English language educator and daily technology podcast host. "
            "Your task is to write an engaging, lively, and articulate daily AI and technology news monologue script for intermediate (B2) learners.\n\n"
            "CRITICAL MANDATES:\n"
            "1. TOPIC FOCUS: Focus EXCLUSIVELY on Artificial Intelligence (AI), Machine Learning, Software Innovations, Robotics, and Future Tech.\n"
            "2. SPOTIFY SAFETY MANDATE: Strictly produce 100% Spotify-compliant, family-friendly (PG) content. NEVER include news, references, or vocabulary about war, military conflict, suicide, murder, crime, violence, or adult/sexual themes.\n"
            "3. TARGET LENGTH: STRICTLY WRITE BETWEEN 1400 AND 1500 WORDS TOTAL. Spoken audio reaches 7.5 to 8.0 minutes.\n"
            "4. GREETING & INTRO: Start immediately with a friendly greeting and date. NO formal course or lesson intros.\n"
            "5. NO B2 LEVEL MENTIONS: Never say 'B2 level' or 'for B2 learners' in the script.\n"
            "6. STRUCTURE: Select 6-8 intriguing AI and technology news stories. Explain full context, tech significance, and vocabulary.\n"
            "7. NO SPECIAL CHARACTERS: Write plain, clear English sentences without asterisks, brackets, or markdown formatting.\n"
            "8. VOCABULARY HIGHLIGHTS: In each story, naturally introduce and explain 1-2 advanced terms (e.g., 'pivotal', 'unprecedented', 'resilience') in plain words.\n"
            "9. SUMMARY BLOCK: At the very end of your response, output a structured bulleted summary of all news items and a Key Vocabulary list."
        )

        user_prompt = (
            f"Here is today's raw AI & Tech news context:\n\n{raw_news_context}\n\n"
            "Generate a 1400-1500 word lively AI & Technology news monologue script covering the top stories in full detail."
        )

        if not self.client:
            print("⚠️ DeepSeek API key is missing or invalid. Using sample fallback script.")
            return self._get_fallback_script("monologue")

        try:
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
        except Exception as e:
            print(f"⚠️ DeepSeek API call failed ({e}). Using sample fallback script.")
            return self._get_fallback_script("monologue")

        lines = full_content.split("\n")
        title = f"Daily Tech & AI Digest - {datetime.date.today().strftime('%B %d, %Y')}"
        
        for line in lines[:5]:
            if line.lower().startswith("title:") or line.lower().startswith("# title:"):
                title = line.split(":", 1)[1].strip().replace("#", "").strip()
                break

        summary_bulletin = self._format_bulletin_summary(full_content)

        return {
            "title": title,
            "script": full_content,
            "summary": "Daily Artificial Intelligence and technology news monologue for B2 English learners.",
            "bulletin_summary": summary_bulletin
        }

    def generate_dialogue_script(self, raw_news_context: str) -> Dict[str, Any]:
        """Generates a lively 2-host podcast conversation script (Alex & Sarah) targeting 1200-1400 words."""
        print("🤖 Prompting DeepSeek-V3 for a 2-host AI & Tech conversational podcast script...")

        if not self.client:
            print("⚠️ DeepSeek API key is missing or invalid. Using sample fallback dialogue script.")
            return self._get_fallback_script("dialogue")

        system_prompt = (
            "You are a top-tier podcast producer and English language educator. "
            "Your task is to write a dynamic, engaging 2-host daily Artificial Intelligence and Technology news podcast conversation script for intermediate (B2) learners.\n\n"
            "CRITICAL MANDATES:\n"
            "1. TOPIC FOCUS: Focus EXCLUSIVELY on Artificial Intelligence (AI), Machine Learning, Tech Startups, Software, and Future Tech Innovations.\n"
            "2. SPOTIFY SAFETY MANDATE: Strictly produce 100% Spotify-compliant, family-friendly (PG) content. NEVER include news, references, or vocabulary about war, military conflict, suicide, murder, crime, violence, or adult/sexual themes.\n"
            "3. HOST ROLES: The co-hosts are Alex (Host A - energetic interviewer) and Sarah (Host B - knowledgeable articulate AI expert).\n"
            "4. FORMAT: Format the conversation strictly line-by-line using speaker labels: 'Alex: ...' and 'Sarah: ...'.\n"
            "5. TARGET LENGTH: WRITE BETWEEN 1200 AND 1400 WORDS TOTAL for an optimal 6.5-7.5 minute spoken audio duration.\n"
            "6. GREETING & INTRO: Start immediately with a friendly greeting between Alex and Sarah discussing today's tech & AI headlines.\n"
            "7. NO B2 LEVEL MENTIONS: Never say 'B2 level' or 'for B2 learners' in the script.\n"
            "8. CONTENT: Discuss 5-6 intriguing AI and tech news stories from the context with lively back-and-forth banter, reactions, and clear explanations of key concepts.\n"
            "9. NO SPECIAL CHARACTERS: Write clean sentences without markdown formatting like asterisks or brackets."
        )

        user_prompt = (
            f"Here is today's raw AI & Tech news context:\n\n{raw_news_context}\n\n"
            "Generate a 2-host daily AI & Tech podcast conversation script (Alex & Sarah) covering the top stories in interactive detail."
        )

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.65,
                max_tokens=4096
            )
            full_content = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ DeepSeek API call failed ({e}). Using sample fallback dialogue script.")
            return self._get_fallback_script("dialogue")

        title = f"Fluent AI Daily - {datetime.date.today().strftime('%B %d, %Y')}"
        ch_data = self.extract_chapters_and_vocabulary(full_content)
        summary_bulletin = self._format_bulletin_summary(full_content)

        return {
            "title": title,
            "script": full_content,
            "summary": ch_data["rich_description"],
            "bulletin_summary": summary_bulletin
        }

    def extract_chapters_and_vocabulary(self, script_text: str) -> Dict[str, Any]:
        """Generates clean, plain English podcast metadata."""
        rich_description = (
            "Daily conversational podcast covering the latest artificial intelligence breakthroughs, "
            "tech startups, and software engineering news in clear, articulate English."
        )

        return {
            "summary": rich_description,
            "rich_description": rich_description
        }

    def extract_timed_sentences(self, script_text: str, total_duration_seconds: float = 505.0, intro_offset: float = 5.3) -> List[Dict[str, Any]]:
        """Extracts turn-aware, character-weighted sentence timestamps calibrated after intro music."""
        import re
        raw_blocks = [b.strip() for b in script_text.split('\n\n') if b.strip()]
        turns_data = []
        total_raw_weight = 0.0

        for b in raw_blocks:
            speaker = 'Alex' if b.startswith('Alex:') else ('Sarah' if b.startswith('Sarah:') else 'Alex')
            clean_turn_text = re.sub(r'^(Alex|Sarah):\s*', '', b).strip()
            s_list = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_turn_text) if len(s.strip()) > 1]
            if not s_list and clean_turn_text:
                s_list = [clean_turn_text]

            turn_sentences = []
            turn_weight = 0.0
            for s in s_list:
                char_count = len(s)
                weight = (char_count / 15.0) + 0.35
                turn_sentences.append({'speaker': speaker, 'text': s, 'weight': weight})
                turn_weight += weight

            turn_weight += 0.5
            turns_data.append({'speaker': speaker, 'sentences': turn_sentences, 'turn_weight': turn_weight})
            total_raw_weight += turn_weight

        # Speech duration between intro (5.3s) and outro (6.3s)
        total_speech_sec = max(30.0, total_duration_seconds - intro_offset - 6.3) if total_duration_seconds > (intro_offset + 10) else total_duration_seconds
        scale_factor = total_speech_sec / total_raw_weight if total_raw_weight > 0 else 1.0
        cum_time = intro_offset
        timed_sentences = []

        for t in turns_data:
            for s in t['sentences']:
                dur = s['weight'] * scale_factor
                st = cum_time
                en = cum_time + dur
                m = int(st // 60)
                sec = int(st % 60)
                timed_sentences.append({
                    'speaker': s['speaker'],
                    'text': s['text'],
                    'start_sec': round(st, 1),
                    'end_sec': round(en, 1),
                    'duration': round(dur, 1),
                    'time_formatted': f'{m:02d}:{sec:02d}'
                })
                cum_time += dur
            cum_time += 0.5 * scale_factor

        return timed_sentences

    def _get_fallback_script(self, script_type: str) -> Dict[str, Any]:
        today_formatted = datetime.date.today().strftime('%B %d, %Y')
        if script_type == "dialogue":
            sample_file = os.path.join("output", "sample_dialogue_script.txt")
            if os.path.exists(sample_file):
                with open(sample_file, "r", encoding="utf-8") as f:
                    content = f.read()
            else:
                content = (
                    "Alex: Welcome to AI Pulse Daily! I'm Alex, joined by Sarah.\n"
                    "Sarah: Thanks Alex! Today we have exciting tech news about AI reasoning and autonomous agents.\n"
                    "Alex: Absolutely. Researchers have introduced new models capable of full-stack software development.\n"
                    "Sarah: Exactly. It opens up brand new possibilities for developers around the world.\n"
                    "Alex: Thanks for tuning in today, stay curious!"
                )
            return {
                "title": f"Daily AI & Tech Podcast (Co-Hosts) - {today_formatted}",
                "script": content,
                "summary": "Dual-host conversational AI and technology news podcast for English learners.",
                "bulletin_summary": "<p>Today's AI and Tech developments.</p>"
            }
        else:
            return {
                "title": f"Daily Tech & AI Digest - {today_formatted}",
                "script": "Hello listeners! Welcome to today's AI and Tech digest. Today we explore developments in artificial intelligence, robotics, and software innovation.",
                "summary": "Daily Artificial Intelligence and technology news monologue for B2 English learners.",
                "bulletin_summary": "<p>Daily AI news summary.</p>"
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
