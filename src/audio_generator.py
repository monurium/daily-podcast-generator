import os
import re
import struct
import asyncio
from typing import Dict, Any, List

DEFAULT_EDGE_VOICE = "en-US-AndrewNeural"

def raw_pcm_to_wav_bytes(pcm_bytes: bytes, sample_rate: int = 24000, num_channels: int = 1, bits_per_sample: int = 16) -> bytes:
    """Wraps raw 24kHz 16-bit PCM audio bytes from Google AI Studio into a standard, fully-playable RIFF WAV format."""
    if pcm_bytes.startswith(b'RIFF'):
        return pcm_bytes
        
    byte_rate = sample_rate * num_channels * (bits_per_sample // 8)
    block_align = num_channels * (bits_per_sample // 8)
    data_size = len(pcm_bytes)
    chunk_size = 36 + data_size

    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        chunk_size,
        b'WAVE',
        b'fmt ',
        16,
        1,
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b'data',
        data_size
    )
    return header + pcm_bytes

def generate_silent_mp3_bytes(duration_ms: int = 600) -> bytes:
    """Generates a clean silent MP3 frame buffer of specified millisecond duration for Edge-TTS backup."""
    num_frames = max(1, int(duration_ms / 100))
    silent_frame = b'\xff\xfb\x90\xc4' + b'\x00' * 413
    return silent_frame * num_frames

class AudioGenerator:
    """Dual-Engine Audio Generator: Primary Google AI Studio (gemini-2.5-flash-preview-tts) with Edge-TTS backup."""

    def __init__(self, edge_voice: str = DEFAULT_EDGE_VOICE):
        self.edge_voice = edge_voice
        self.gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def _generate_gemini_audio(self, script_text: str, output_path: str) -> bool:
        """Synthesizes high-realism lively native audio using Google AI Studio gemini-2.5-flash-preview-tts with Aoede voice."""
        if not self.gemini_api_key:
            print("ℹ️ No GEMINI_API_KEY set. Using Edge-TTS backup engine.")
            return False

        print("✨ Synthesizing lively native audio via Google AI Studio (Voice: Aoede)...")
        candidate_models = ["gemini-2.5-flash-preview-tts", "gemini-2.5-pro-preview-tts"]
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.gemini_api_key)

            prompt = (
                "You are an enthusiastic, clear, lively, and articulate daily news podcast host. "
                "Narrate the following news script with clear vocal dynamics, engaging rhythm, natural pauses after sentences, "
                "and a warm, energetic presentation style so listeners can follow effortlessly:\n\n"
                f"{script_text}"
            )

            config = types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Aoede"
                        )
                    )
                )
            )

            for model_name in candidate_models:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config
                    )

                    if response.candidates and response.candidates[0].content.parts:
                        for part in response.candidates[0].content.parts:
                            if hasattr(part, "inline_data") and part.inline_data:
                                pcm_data = part.inline_data.data
                                wav_data = raw_pcm_to_wav_bytes(pcm_data)
                                
                                os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
                                with open(output_path, "wb") as f:
                                    f.write(wav_data)
                                
                                file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                                duration_sec = int(len(pcm_data) / 48000)
                                print(f"🎉 Google AI Studio audio generated successfully via model '{model_name}': {output_path} ({file_size_mb:.2f} MB, {duration_sec // 60}m {duration_sec % 60}s)")
                                return True
                except Exception as model_err:
                    print(f"⚠️ Model '{model_name}' attempt failed: {model_err}")

            print("⚠️ Google AI Studio models unavailable. Falling back to Edge-TTS backup.")
            return False

        except Exception as e:
            print(f"⚠️ Google AI Studio error ({e}). Falling back to Edge-TTS backup.")
            return False

    async def _synthesize_sentence_edge(self, index: int, text: str, output_dir: str) -> str:
        """Synthesizes a single sentence with Edge-TTS, safely handling exceptions per chunk."""
        import edge_tts

        temp_file = os.path.join(output_dir, f"part_{index:04d}.mp3")
        try:
            communicate = edge_tts.Communicate(text, self.edge_voice, rate="-3%", pitch="+0Hz")
            await communicate.save(temp_file)
            return temp_file
        except Exception:
            return ""

    async def build_audio_monologue_edge(self, script_text: str, output_mp3: str) -> str:
        """Fallback Edge-TTS audio generator with sentence-by-sentence pitch contours and silence breaks."""
        print(f"🎙️ Using Edge-TTS backup engine with voice '{self.edge_voice}'...")
        
        paragraphs = [p.strip() for p in script_text.strip().split("\n\n") if p.strip()]
        all_sentence_tasks = []
        sentence_map = []
        
        base_dir = os.path.dirname(output_mp3) if os.path.dirname(output_mp3) else "."
        os.makedirs(base_dir, exist_ok=True)
        
        global_idx = 0
        for para in paragraphs:
            clean_para = re.sub(r'\[.*?\]|\(.*?\)', '', para).strip()
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_para) if s.strip()]
            
            for s_idx, sentence in enumerate(sentences):
                alphanumeric_chars = re.sub(r'[^a-zA-Z0-9]', '', sentence)
                if len(alphanumeric_chars) >= 2:
                    is_last_in_para = (s_idx == len(sentences) - 1)
                    sentence_map.append((global_idx, is_last_in_para))
                    all_sentence_tasks.append(self._synthesize_sentence_edge(global_idx, sentence, base_dir))
                    global_idx += 1

        if not all_sentence_tasks:
            raise ValueError("Script text contains no valid non-empty sentences for audio synthesis.")

        temp_files = await asyncio.gather(*all_sentence_tasks)

        short_pause_bytes = generate_silent_mp3_bytes(650)
        long_pause_bytes = generate_silent_mp3_bytes(1400)

        try:
            with open(output_mp3, 'wb') as outfile:
                for idx, fname in enumerate(temp_files):
                    if fname and os.path.exists(fname):
                        with open(fname, 'rb') as infile:
                            outfile.write(infile.read())
                        
                        is_para_end = sentence_map[idx][1] if idx < len(sentence_map) else False
                        if is_para_end:
                            outfile.write(long_pause_bytes)
                        else:
                            outfile.write(short_pause_bytes)
        finally:
            for fname in temp_files:
                if fname and os.path.exists(fname):
                    try:
                        os.remove(fname)
                    except OSError:
                        pass

        print(f"🎉 Edge-TTS audio generated successfully: {output_mp3}")
        return output_mp3

    def text_to_audio(self, script_text: str, output_path: str) -> Dict[str, Any]:
        """Dual-engine runner: tries Google AI Studio first, falls back to Edge-TTS."""
        audio_created = False

        if self.gemini_api_key:
            audio_created = self._generate_gemini_audio(script_text, output_path)

        if not audio_created:
            asyncio.run(self.build_audio_monologue_edge(script_text, output_path))

        file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        
        if audio_created and file_size > 44:
            duration_seconds = max(30, int((file_size - 44) / 48000))
        else:
            words = len(script_text.split())
            duration_seconds = max(30, int((words / 130.0) * 60))

        return {
            "file_path": output_path,
            "file_size": file_size,
            "duration_seconds": duration_seconds,
            "duration_formatted": f"{duration_seconds // 3600:02d}:{(duration_seconds % 3600) // 60:02d}:{duration_seconds % 60:02d}"
        }
