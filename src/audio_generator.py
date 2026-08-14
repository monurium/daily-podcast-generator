import os
import re
import asyncio
from typing import Dict, Any, List

VOICE_ALEX = "en-US-ChristopherNeural"  # Male Voice (Alex)
VOICE_SAM = "en-US-JennyNeural"        # Female Voice (Sam)

class AudioGenerator:
    """Renders energetic multi-host dialogue (Alex & Sam) into a single unified MP3 audio file using edge-tts."""

    def __init__(self, voice_alex: str = VOICE_ALEX, voice_sam: str = VOICE_SAM):
        self.voice_alex = voice_alex
        self.voice_sam = voice_sam

    async def build_audio_podcast(self, script_text: str, output_mp3: str) -> str:
        """Parses dialogue line-by-line, synthesizes with pitch/rate tuning, and concatenates audio chunks."""
        import edge_tts

        print("🎙️ Synthesizing multi-speaker dialogue (Alex & Sam)...")
        lines = script_text.strip().split("\n")
        temp_files: List[str] = []

        os.makedirs(os.path.dirname(output_mp3) if os.path.dirname(output_mp3) else ".", exist_ok=True)

        for idx, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            voice = None
            clean_text = ""

            # Speaker line matching & cleaning
            if re.match(r'^\*?\*?Alex\b', line, re.IGNORECASE):
                voice = self.voice_alex
                clean_text = re.sub(r'^\*?\*?Alex\*?\*?\s*:\s*', '', line, flags=re.IGNORECASE)
            elif re.match(r'^\*?\*?Sam\b', line, re.IGNORECASE):
                voice = self.voice_sam
                clean_text = re.sub(r'^\*?\*?Sam\*?\*?\s*:\s*', '', line, flags=re.IGNORECASE)
            elif line:
                voice = self.voice_alex
                clean_text = line

            clean_text = re.sub(r'\[.*?\]|\(.*?\)', '', clean_text).strip()

            if clean_text and voice:
                temp_file = os.path.join(os.path.dirname(output_mp3) if os.path.dirname(output_mp3) else ".", f"part_{idx:03d}.mp3")

                # Energetic & natural speech settings (rate="+6%", pitch="+3Hz")
                communicate = edge_tts.Communicate(clean_text, voice, rate="+6%", pitch="+3Hz")
                await communicate.save(temp_file)
                temp_files.append(temp_file)

        print(f"🎛️ Concatenating {len(temp_files)} audio segments into {output_mp3}...")
        with open(output_mp3, 'wb') as outfile:
            for fname in temp_files:
                if os.path.exists(fname):
                    with open(fname, 'rb') as infile:
                        outfile.write(infile.read())
                    os.remove(fname)

        print(f"🎉 Podcast audio generated successfully: {output_mp3}")
        return output_mp3

    def text_to_audio(self, script_text: str, output_path: str) -> Dict[str, Any]:
        """Synchronous wrapper for text-to-audio synthesis."""
        asyncio.run(self.build_audio_podcast(script_text, output_path))

        file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        
        # Calculate estimated duration (word count / ~150 wpm)
        words = len(script_text.split())
        duration_seconds = max(30, int((words / 150.0) * 60))

        return {
            "file_path": output_path,
            "file_size": file_size,
            "duration_seconds": duration_seconds,
            "duration_formatted": f"{duration_seconds // 3600:02d}:{(duration_seconds % 3600) // 60:02d}:{duration_seconds % 60:02d}"
        }
