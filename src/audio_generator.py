import os
import asyncio
import os.path
from typing import Dict, Any

class AudioGenerator:
    """Converts script text into Apple Podcasts compatible MP3 audio files."""

    def __init__(self, voice: str = "en-US-ChristopherNeural"):
        self.voice = voice

    async def _generate_edge_tts(self, script_text: str, output_path: str):
        """Asynchronously synthesizes speech using edge-tts."""
        import edge_tts
        communicate = edge_tts.Communicate(script_text, self.voice)
        await communicate.save(output_path)

    def _generate_gtts(self, script_text: str, output_path: str):
        """Fallback TTS using gTTS."""
        from gtts import gTTS
        tts = gTTS(text=script_text, lang='en')
        tts.save(output_path)

    def text_to_audio(self, script_text: str, output_path: str) -> Dict[str, Any]:
        """Synthesizes MP3 file and returns audio metadata (file size, duration)."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        generated = False
        try:
            # Try high-quality Edge TTS first
            asyncio.run(self._generate_edge_tts(script_text, output_path))
            generated = True
        except Exception as e:
            print(f"Warning: Edge TTS failed ({e}), switching to gTTS fallback.")
            
        if not generated:
            try:
                self._generate_gtts(script_text, output_path)
                generated = True
            except Exception as e:
                raise RuntimeError(f"All TTS synthesis engines failed: {e}")

        # Get file metadata
        file_size = os.path.getsize(output_path)
        duration_seconds = 120 # Default fallback duration estimate

        # Attempt to get exact audio duration if pydub/mutagen is available
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_mp3(output_path)
            duration_seconds = int(len(audio) / 1000)
        except Exception:
            pass

        return {
            "file_path": output_path,
            "file_size": file_size,
            "duration_seconds": duration_seconds,
            "duration_formatted": f"{duration_seconds // 3600:02d}:{(duration_seconds % 3600) // 60:02d}:{duration_seconds % 60:02d}"
        }
