# 🎙️ AI Pulse Daily — Automated AI & Tech Podcast Generator

An automated Python-powered daily podcast pipeline that curates fresh Artificial Intelligence (AI) and technology news, generates engaging 2-host English conversational scripts via DeepSeek-V3, synthesizes distinct **Male (Alex)** and **Female (Sarah)** voices via Google AI Studio (Gemini 2.5 TTS), and publishes Spotify & Apple Podcasts-compliant RSS feeds (`podcast.xml`) hands-free via GitHub Actions.

---

## 🌟 Key Features

- 🤖 **2-Host Conversational Dialogue (Alex & Sarah)**: Generates lively, natural English dialogues between Alex (energetic male interviewer) and Sarah (knowledgeable female AI expert).
- 🔊 **Multi-Speaker Voice Synthesis**: Synthesizes distinct **Male (Alex: Puck / Christopher)** and **Female (Sarah: Aoede / Ava)** voices per dialogue turn.
- 📡 **AI & Tech RSS Scanner**: Scans top tech publications (TechCrunch AI, Wired, Ars Technica, NYT Tech, BBC Tech) for 24-hour fresh news.
- 🛡️ **Spotify Family-Friendly Content Guardrails**: Code-level negative keyword filtering and LLM prompt mandates prohibiting +18, war, suicide, crime, or graphic violence.
- 🗜️ **MP3 Compression (`lameenc`)**: Direct 24kHz PCM-to-MP3 encoding (~82% file size reduction down to ~3-4MB per episode).
- 🧪 **Local Dry-Run / Test Mode (`python main.py --test`)**: Safely preview generated scripts and MP3 audio locally without publishing to Spotify or modifying live RSS feeds.
- ⚙️ **Automated Daily GitHub Actions**: Runs on a daily schedule (06:00 UTC / 09:00 TRT) to generate, build, and publish new episodes automatically.

---

## 📁 Repository Structure

```
daily-podcast-generator/
├── config/
│   └── podcast_config.json    # Podcast metadata (Title, Author, Cover, Category)
├── src/
│   ├── content_generator.py   # AI news fetcher & DeepSeek script generator
│   ├── audio_generator.py     # Gemini 2.5 TTS & Edge-TTS multi-speaker synthesis
│   ├── rss_builder.py         # Spotify & Apple Podcasts iTunes RSS 2.0 builder
│   └── publisher.py           # Manifest manager & dist folder publisher
├── output/                    # Local test outputs (scripts & test MP3s)
├── dist/                      # Published web hosting folder (podcast.xml & MP3s)
├── .github/workflows/
│   └── daily_podcast.yml      # GitHub Actions daily automated workflow
├── cover.jpg                  # Minimalist luxury podcast cover artwork (1400x1400)
├── main.py                    # Pipeline execution & CLI entry point
├── requirements.txt           # Python dependencies
└── README.md
```

---

## 🧪 Local Setup & Development (Testing Mode)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your API keys:
```env
DEEPSEEK_API_KEY=your_deepseek_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### 3. Run Local Test Mode (Dry-Run)
To test script generation and voice synthesis without updating Spotify or live RSS feeds:
```bash
python main.py --test
```
- **Output:**
  - 📄 `output/dialogue_script.txt` (Generated test script)
  - 🎧 `output/test_dialogue_podcast.mp3` (Generated Male & Female test audio)
  - 🛡️ **Spotify & `podcast.xml` are NOT modified.**

---

## 🚀 Production Publishing Mode

To manually run a full production build and update `podcast.xml`:
```bash
python main.py
```
Output files will be updated in `./podcast.xml` and `dist/`:
- `./podcast.xml` (Live RSS feed for Spotify & Apple Podcasts)
- `dist/episodes/*.mp3` (Episode audio files)

---

## 🟢 Submitting to Spotify for Podcasters

1. Enable **GitHub Pages** on your repository (Source: `Deploy from a branch`, Branch: `main`, `/ (root)`).
2. Your public RSS Feed URL is:
   ```text
   https://monurium.github.io/daily-podcast-generator/podcast.xml
   ```
3. Go to [Spotify for Podcasters](https://podcasters.spotify.com/).
4. Click **Add your podcast** -> Select **I already have an RSS feed**.
5. Paste your `podcast.xml` URL.
6. Verify the 8-digit PIN sent to your email.
7. Spotify will automatically fetch and publish new daily episodes every morning!

---

## 📄 License
MIT License
