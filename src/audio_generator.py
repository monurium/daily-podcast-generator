import os
import re
import asyncio
from typing import Dict, Any, List

# Top-tier Microsoft Neural Broadcaster Voices
# en-US-GuyNeural: Authentic American news anchor / radio broadcaster voice
# en-US-AndrewNeural: Warm storytelling / podcast narrator voice
DEFAULT_VOICE = "en-US-GuyNeural"

class AudioGenerator:
    """Renders a single narrator educational English lesson into an MP3 audio file using edge-tts with SSML human-like breath pauses and prosody tuning."""

    def __init__(self, voice: str = DEFAULT_VOICE):
        self.voice = voice

    def _format_ssml_text(self, text: str) -> str:
        """Wraps clean text into SSML with natural sentence pauses (<break time='350ms'/>) for ElevenLabs-like realistic pacing."""
        # Replace sentence endings (. ! ?) with explicit human pause breaks
        ssml_body = re.sub(r'([.!?])\s+', r'\1 <break time="350ms"/> ', text)
        return ssml_body

    async def _synthesize_paragraph(self, index: int, text: str, output_dir: str) -> str:
        """Synthesizes a single paragraph into a temporary MP3 file using SSML formatting."""
        import edge_tts

        temp_file = os.path.join(output_dir, f"part_{index:03d}.mp3")
        ssml_text = self._format_ssml_text(text)
        
        # Steady broadcast-quality cadence (rate="-1%", pitch="+0Hz")
        communicate = edge_tts.Communicate(ssml_text, self.voice, rate="-1%", pitch="+0Hz")
        await communicate.save(temp_file)
        return temp_file

    async def build_audio_monologue(self, script_text: str, output_mp3: str) -> str:
        """Synthesizes script text into clear, human-like educational single-speaker audio narration using parallel SSML tasks."""
        print(f"🎙️ Synthesizing human-like news narration using voice '{self.voice}' with SSML micro-pauses...")
        paragraphs = [p.strip() for p in script_text.strip().split("\n\n") if p.strip()]
        temp_files: List[str] = []
        base_dir = os.path.dirname(output_mp3) if os.path.dirname(output_mp3) else "."
        os.makedirs(base_dir, exist_ok=True)

        tasks = []
        for idx, para in enumerate(paragraphs):
            clean_text = re.sub(r'\[.*?\]|\(.*?\)', '', para).strip()
            if clean_text:
                tasks.append(self._synthesize_paragraph(idx, clean_text, base_dir))

        if not tasks:
            raise ValueError("Script text contains no valid non-empty paragraphs for audio synthesis.")

        print(f"⚡ Synthesizing {len(tasks)} paragraph audio chunks with SSML formatting in parallel...")
        temp_files = await asyncio.gather(*tasks)

        try:
            print(f"🎛️ Concatenating {len(temp_files)} paragraph segments into {output_mp3}...")
            with open(output_mp3, 'wb') as outfile:
                for fname in temp_files:
                    if os.path.exists(fname):
                        with open(fname, 'rb') as infile:
                            outfile.write(infile.read())
        finally:
            # Guarantee cleanup of all temporary audio chunk files
            for fname in temp_files:
                if os.path.exists(fname):
                    try:
                        os.remove(fname)
                    except OSError:
                        pass

        print(f"🎉 Enhanced audio monologue generated successfully: {output_mp3}")
        return output_mp3

    def text_to_audio(self, script_text: str, output_path: str) -> Dict[str, Any]:
        """Synchronous wrapper for text-to-audio monologue synthesis."""
        asyncio.run(self.build_audio_monologue(script_text, output_path))

        file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        
        words = len(script_text.split())
        duration_seconds = max(30, int((words / 135.0) * 60))

        return {
            "file_path": output_path,
            "file_size": file_size,
            "duration_seconds": duration_seconds,
            "duration_formatted": f"{duration_seconds // 3600:02d}:{(duration_seconds % 3600) // 60:02d}:{duration_seconds % 60:02d}"
        }
