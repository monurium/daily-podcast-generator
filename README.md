# 🎙️ Daily Podcast Generator & Publisher

An automated Python pipeline that generates daily podcast episodes (script writing + TTS audio rendering), builds Apple Podcasts-compliant RSS feeds (`podcast.xml`), and publishes them automatically.

---

## 🌟 Features

- **Automated Script Generation**: Uses OpenAI API or offline daily summary templates to write engage 2-minute podcast scripts.
- **High-Quality TTS Audio Synthesis**: Converts scripts to natural-sounding MP3 speech using `edge-tts` / `gTTS`.
- **Apple Podcasts Compliant RSS Generator**: Automatically creates & updates valid iTunes RSS 2.0 XML (`podcast.xml`) with duration, file size enclosures, artwork links, and categories.
- **Daily Automated Runner**: GitHub Actions workflow runs every day at 06:00 UTC to produce and publish new episodes hands-free.

---

## 📁 Repository Structure

```
daily-podcast-generator/
├── src/
│   ├── content_generator.py   # Script generation (LLM / News)
│   ├── audio_generator.py     # Text-to-Speech audio rendering (MP3)
│   ├── rss_builder.py         # Apple Podcasts RSS 2.0 XML generator
│   └── publisher.py           # Output hosting & manifest manager
├── config/
│   └── podcast_config.json    # Podcast metadata (Title, Category, Cover)
├── .github/workflows/
│   └── daily_podcast.yml      # Daily GitHub Actions automated workflow
├── main.py                    # Entry point execution script
├── requirements.txt           # Python dependencies
└── README.md
```

---

## 🚀 Quick Start (Local Setup)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables (Optional)
Copy `.env.example` to `.env` and fill in your details:
```env
OPENAI_API_KEY=your_openai_key
PODCAST_BASE_URL=https://monurium.github.io/daily-podcast-generator
```

### 3. Run Pipeline
```bash
python main.py
```

Output files will be generated in `dist/`:
- `dist/podcast.xml` (RSS Feed for Apple Podcasts)
- `dist/episodes/*.mp3` (Episode audio files)

---

## 📱 Submitting to Apple Podcasts

1. Enable **GitHub Pages** on your repository (pointing to `main` or `gh-pages` / `dist` folder).
2. Your public RSS Feed URL will be:
   ```
   https://monurium.github.io/daily-podcast-generator/podcast.xml
   ```
3. Go to [Apple Podcasts Connect](https://podcastsconnect.apple.com/).
4. Click **+ Add Show** -> **Add a show with an RSS feed**.
5. Paste your `podcast.xml` URL.
6. Apple will validate your feed and approve your show. From then on, every daily run will automatically appear on Apple Podcasts!

---

## 📄 License
MIT License
