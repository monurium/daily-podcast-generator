import os
import re
import asyncio
from typing import Dict, Any, List

# High-warmth, natural story-teller and documentary narrator voice
# en-US-AndrewNeural: Warm, engaging, conversational narrator (not monotone)
# en-US-BrianNeural: Classic relaxed BBC news presenter
DEFAULT_VOICE = "en-US-AndrewNeural"

def generate_silent_mp3_bytes(duration_ms: int = 600) -> bytes:
    """Generates a clean silent MP3 frame buffer of specified millisecond duration."""
    # A standard silent MP3 frame at 128kbps / 24kHz is ~417 bytes for 100ms
    num_frames = max(1, int(duration_ms / 100))
    # Standard silent MP3 frame header (0xFF 0xFB) + silent frame data
    silent_frame = b'\xff\xfb\x90\xc4' + b'\x00' * 413
    return silent_frame * num_frames

class AudioGenerator:
    """Renders single narrator educational English lesson with sentence-level dynamic intonation and natural silence breaks."""

    def __init__(self, voice: str = DEFAULT_VOICE):
        self.voice = voice

    async def _synthesize_sentence(self, index: int, text: str, output_dir: str) -> str:
        """Synthesizes a single sentence with natural cadence and sentence-level pitch contour."""
        import edge_tts

        temp_file = os.path.join(output_dir, f"part_{index:04d}.mp3")
        # Calm, relaxed, natural speaking pace (-3% rate for maximum clarity and zero rush)
        communicate = edge_tts.Communicate(text, self.voice, rate="-3%", pitch="+0Hz")
        await communicate.save(temp_file)
        return temp_file

    async def build_audio_monologue(self, script_text: str, output_mp3: str) -> str:
        """Splits script into sentences, synthesizes each sentence individually for natural pitch variation, and inserts silence gaps."""
        print(f"🎙️ Synthesizing sentence-by-sentence audio narration using warm voice '{self.voice}'...")
        
        # 1. Split script into paragraphs (stories)
        paragraphs = [p.strip() for p in script_text.strip().split("\n\n") if p.strip()]
        
        # 2. Extract individual sentences across paragraphs
        all_sentence_tasks = []
        sentence_map = []  # Tracks (sentence_idx, is_paragraph_end)
        
        base_dir = os.path.dirname(output_mp3) if os.path.dirname(output_mp3) else "."
        os.makedirs(base_dir, exist_ok=True)
        
        global_idx = 0
        for p_idx, para in enumerate(paragraphs):
            # Clean formatting brackets
            clean_para = re.sub(r'\[.*?\]|\(.*?\)', '', para).strip()
            # Split paragraph into sentences by punctuation (. ! ?)
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_para) if s.strip()]
            
            for s_idx, sentence in enumerate(sentences):
                if len(sentence) > 3:
                    is_last_in_para = (s_idx == len(sentences) - 1)
                    sentence_map.append((global_idx, is_last_in_para))
                    all_sentence_tasks.append(self._synthesize_sentence(global_idx, sentence, base_dir))
                    global_idx += 1

        if not all_sentence_tasks:
            raise ValueError("Script text contains no valid non-empty sentences for audio synthesis.")

        print(f"⚡ Synthesizing {len(all_sentence_tasks)} individual sentences in parallel for natural pitch contours...")
        temp_files = await asyncio.gather(*all_sentence_tasks)

        # Generate silence buffers
        short_pause_bytes = generate_silent_mp3_bytes(650)   # 0.65s silence between sentences
        long_pause_bytes = generate_silent_mp3_bytes(1400)   # 1.4s silence between news stories

        try:
            print(f"🎛️ Concatenating sentence audio segments with natural silence breaks into {output_mp3}...")
            with open(output_mp3, 'wb') as outfile:
                for idx, fname in enumerate(temp_files):
                    if os.path.exists(fname):
                        with open(fname, 'rb') as infile:
                            outfile.write(infile.read())
                        
                        # Insert silence after sentence
                        is_para_end = sentence_map[idx][1] if idx < len(sentence_map) else False
                        if is_para_end:
                            outfile.write(long_pause_bytes)
                        else:
                            outfile.write(short_pause_bytes)

        finally:
            # Guarantee cleanup of all temporary audio chunk files
            for fname in temp_files:
                if os.path.exists(fname):
                    try:
                        os.remove(fname)
                    except OSError:
                        pass

        print(f"🎉 Relaxed, natural audio monologue generated successfully: {output_mp3}")
        return output_mp3

    def text_to_audio(self, script_text: str, output_path: str) -> Dict[str, Any]:
        """Synchronous wrapper for sentence-by-sentence text-to-audio monologue synthesis."""
        asyncio.run(self.build_audio_monologue(script_text, output_path))

        file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        
        words = len(script_text.split())
        duration_seconds = max(30, int((words / 130.0) * 60))

        return {
            "file_path": output_path,
            "file_size": file_size,
            "duration_seconds": duration_seconds,
            "duration_formatted": f"{duration_seconds // 3600:02d}:{(duration_seconds % 3600) // 60:02d}:{duration_seconds % 60:02d}"
        }
