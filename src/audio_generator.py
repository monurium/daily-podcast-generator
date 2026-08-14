import os
import re
import asyncio
from typing import Dict, Any, List

DEFAULT_VOICE = "en-US-ChristopherNeural"  # Clear, friendly teacher narrator voice

class AudioGenerator:
    """Renders a single narrator educational English lesson into an MP3 audio file using edge-tts."""

    def __init__(self, voice: str = DEFAULT_VOICE):
        self.voice = voice

    async def build_audio_monologue(self, script_text: str, output_mp3: str) -> str:
        """Synthesizes script text into clear, educational single-speaker audio narration."""
        import edge_tts

        print(f"🎙️ Synthesizing clear educational narration using voice '{self.voice}'...")
        paragraphs = [p.strip() for p in script_text.strip().split("\n\n") if p.strip()]
        temp_files: List[str] = []

        os.makedirs(os.path.dirname(output_mp3) if os.path.dirname(output_mp3) else ".", exist_ok=True)

        for idx, para in enumerate(paragraphs):
            clean_text = re.sub(r'\[.*?\]|\(.*?\)', '', para).strip()

            if clean_text:
                temp_file = os.path.join(os.path.dirname(output_mp3) if os.path.dirname(output_mp3) else ".", f"part_{idx:03d}.mp3")

                # Clear, steady educational pacing (rate="+1%", pitch="+1Hz" for max clarity)
                communicate = edge_tts.Communicate(clean_text, self.voice, rate="+1%", pitch="+1Hz")
                await communicate.save(temp_file)
                temp_files.append(temp_file)

        print(f"🎛️ Concatenating {len(temp_files)} paragraph segments into {output_mp3}...")
        with open(output_mp3, 'wb') as outfile:
            for fname in temp_files:
                if os.path.exists(fname):
                    with open(fname, 'rb') as infile:
                        outfile.write(infile.read())
                    os.remove(fname)

        print(f"🎉 Educational audio monologue generated successfully: {output_mp3}")
        return output_mp3

    def text_to_audio(self, script_text: str, output_path: str) -> Dict[str, Any]:
        """Synchronous wrapper for text-to-audio monologue synthesis."""
        asyncio.run(self.build_audio_monologue(script_text, output_path))

        file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        
        words = len(script_text.split())
        duration_seconds = max(30, int((words / 140.0) * 60))

        return {
            "file_path": output_path,
            "file_size": file_size,
            "duration_seconds": duration_seconds,
            "duration_formatted": f"{duration_seconds // 3600:02d}:{(duration_seconds % 3600) // 60:02d}:{duration_seconds % 60:02d}"
        }
