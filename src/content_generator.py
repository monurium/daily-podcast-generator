import os
import datetime
from typing import Dict, Any

class ContentGenerator:
    """Generates daily podcast scripts using LLM APIs or curated daily news sources."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def generate_daily_script(self, topic: str = "Technology & AI Highlights") -> Dict[str, Any]:
        """Generates episode title, script summary, and full podcast speech text."""
        date_str = datetime.date.today().strftime("%B %d, %Y")
        
        if self.api_key:
            try:
                import openai
                client = openai.OpenAI(api_key=self.api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a professional daily news podcast host. Write an engaging 2-minute spoken script."},
                        {"role": "user", "content": f"Create a podcast episode for {date_str} about {topic}. Provide response in JSON format with 'title', 'summary', and 'script' keys."}
                    ],
                    response_format={"type": "json_object"}
                )
                import json
                result = json.loads(response.choices[0].message.content)
                return result
            except Exception as e:
                print(f"Warning: OpenAI script generation failed ({e}). Using default template.")

        # Default fallback template for local/offline run
        title = f"Daily AI & Tech Update - {date_str}"
        summary = f"Welcome to today's episode for {date_str}, covering key updates in tech, AI developments, and software engineering."
        script = (
            f"Hello everyone and welcome to your Daily AI and Tech Digest for {date_str}. "
            f"Today we are highlighting the latest breakthroughs in artificial intelligence, "
            f"cloud automation, and software development. "
            f"Automation tools are continuing to transform how developers build applications, "
            f"enabling faster deployments and seamless podcast publishing directly to platforms like Apple Podcasts. "
            f"Thank you for listening, and stay tuned for tomorrow's daily update!"
        )

        return {
            "title": title,
            "summary": summary,
            "script": script,
            "date": date_str
        }
