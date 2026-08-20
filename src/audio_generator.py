import os
import re
import asyncio
import time
import tempfile
from typing import Dict, Any, List, Tuple

DEFAULT_EDGE_VOICE = "en-US-AndrewNeural"
GEMINI_TTS_MODELS = ("gemini-2.5-flash-preview-tts", "gemini-2.0-flash")
GEMINI_VOICE_MAP = {"Alex": "Puck", "Sarah": "Aoede"}
EDGE_VOICE_MAP = {"Alex": "en-US-ChristopherNeural", "Sarah": "en-US-AvaNeural"}
PACING_SECONDS_PER_REQUEST = 6.2  # Guarantees strictly staying under the 10 RPM quota limit

def raw_pcm_to_mp3_bytes(pcm_bytes: bytes, sample_rate: int = 24000, num_channels: int = 1, bitrate: int = 64) -> bytes:
    """Encodes raw 24kHz 16-bit PCM audio bytes from Google AI Studio into compressed MP3 format using lameenc."""
    import lameenc
    encoder = lameenc.Encoder()
    encoder.set_bit_rate(bitrate)
    encoder.set_in_sample_rate(sample_rate)
    encoder.set_channels(num_channels)
    encoder.set_quality(2)
    return encoder.encode(pcm_bytes) + encoder.flush()

def generate_silent_mp3_bytes(duration_ms: int = 600) -> bytes:
    """Generates a clean silent MP3 frame buffer of specified millisecond duration."""
    num_frames = max(1, int(duration_ms / 100))
    silent_frame = b'\xff\xfb\x90\xc4' + b'\x00' * 413
    return silent_frame * num_frames

class AudioGenerator:
    """Dual-Engine Audio Generator: Primary Google AI Studio (Gemini 2.5 TTS) with Edge-TTS backup."""

    def __init__(self, edge_voice: str = DEFAULT_EDGE_VOICE):
        self.edge_voice = edge_voice
        self.gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    def _build_audio_metadata(self, output_path: str, duration_seconds: int) -> Dict[str, Any]:
        """Constructs standardized audio metadata response dictionary."""
        file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        return {
            "file_path": output_path,
            "file_size": file_size,
            "duration_seconds": duration_seconds,
            "duration_formatted": f"{duration_seconds // 3600:02d}:{(duration_seconds % 3600) // 60:02d}:{duration_seconds % 60:02d}"
        }

    def _parse_dialogue_turns(self, script_text: str) -> List[Tuple[str, str]]:
        """Parses script lines into clean (speaker_name, text) pairs."""
        turns: List[Tuple[str, str]] = []
        for line in script_text.splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            if line_str.startswith("Alex:"):
                turns.append(("Alex", line_str[5:].strip()))
            elif line_str.startswith("Sarah:"):
                turns.append(("Sarah", line_str[6:].strip()))
            else:
                if turns:
                    prev_speaker, prev_text = turns[-1]
                    turns[-1] = (prev_speaker, f"{prev_text} {line_str}")
                else:
                    turns.append(("Alex", line_str))
        return turns

    def _generate_gemini_audio(self, script_text: str, output_path: str) -> Tuple[bool, int]:
        """Synthesizes single-narrator audio using Google AI Studio with Aoede voice."""
        if not self.gemini_api_key:
            print("ℹ️ No GEMINI_API_KEY set. Using Edge-TTS backup engine.")
            return False, 0

        print("✨ Synthesizing lively native audio via Google AI Studio (Voice: Aoede)...")
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.gemini_api_key)
            prompt = (
                "You are an enthusiastic, clear, lively, and articulate daily news podcast host. "
                "Narrate the following news script with clear vocal dynamics, natural pauses, "
                "and a warm, energetic presentation style:\n\n"
                f"{script_text}"
            )
            config = types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Aoede")
                    )
                )
            )

            for model_name in GEMINI_TTS_MODELS:
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
                                audio_bytes = raw_pcm_to_mp3_bytes(pcm_data)
                                os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
                                with open(output_path, "wb") as f:
                                    f.write(audio_bytes)
                                
                                file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                                duration_sec = max(30, int(len(pcm_data) / 48000))
                                print(f"🎉 Google AI Studio audio generated via '{model_name}': {output_path} ({file_size_mb:.2f} MB, {duration_sec // 60}m {duration_sec % 60}s)")
                                return True, duration_sec
                except Exception as model_err:
                    print(f"⚠️ Model '{model_name}' attempt failed: {model_err}")

            return False, 0
        except Exception as e:
            print(f"⚠️ Google AI Studio error ({e}).")
            return False, 0

    def _generate_gemini_dialogue_audio(self, dialogue_script: str, output_path: str) -> Tuple[bool, int]:
        """Synthesizes 2-host podcast conversation (Alex: Puck, Sarah: Aoede) using Google AI Studio in parallel."""
        if not self.gemini_api_key:
            return False, 0

        turns = self._parse_dialogue_turns(dialogue_script)
        valid_turns = [(idx, speaker, re.sub(r'\[.*?\]|\(.*?\)', '', text).strip()) for idx, (speaker, text) in enumerate(turns) if re.sub(r'\[.*?\]|\(.*?\)', '', text).strip()]
        if not valid_turns:
            return False, 0

        print(f"✨ Synthesizing 2-host dialogue via Google AI Studio Flash ({len(valid_turns)} turns, smart rate limiter < 10 RPM)...")
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.gemini_api_key)
            pause_bytes = generate_silent_mp3_bytes(450)
            temp_turn_results = {}

            with tempfile.TemporaryDirectory() as temp_dir:
                for t_idx, (idx, speaker, clean_text) in enumerate(valid_turns):
                    voice_name = GEMINI_VOICE_MAP.get(speaker, "Puck" if speaker == "Alex" else "Aoede")
                    config = types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                            )
                        )
                    )
                    turn_prompt = f"Speak clearly as a podcast co-host: {clean_text}"
                    t_file = os.path.join(temp_dir, f"turn_{idx:04d}.mp3")

                    turn_success = False
                    for model_name in GEMINI_TTS_MODELS:
                        for attempt in range(2):
                            try:
                                response = client.models.generate_content(
                                    model=model_name,
                                    contents=turn_prompt,
                                    config=config
                                )
                                if response.candidates and response.candidates[0].content.parts:
                                    for part in response.candidates[0].content.parts:
                                        if hasattr(part, "inline_data") and part.inline_data:
                                            pcm_chunk = part.inline_data.data
                                            mp3_chunk = raw_pcm_to_mp3_bytes(pcm_chunk)
                                            with open(t_file, "wb") as f:
                                                f.write(mp3_chunk)
                                            temp_turn_results[idx] = t_file
                                            turn_success = True
                                            break
                                if turn_success:
                                    break
                            except Exception as err:
                                err_str = str(err)
                                if "limit: 0" in err_str:
                                    break
                                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                                    time.sleep(7.0)
                                else:
                                    break
                        if turn_success:
                            break

                    # Pacing delay between turns to strictly stay below 10 RPM limit
                    if t_idx < len(valid_turns) - 1:
                        time.sleep(PACING_SECONDS_PER_REQUEST)

                if len(temp_turn_results) >= int(len(valid_turns) * 0.8):
                    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
                    with open(output_path, "wb") as outfile:
                        for idx in sorted(temp_turn_results.keys()):
                            t_path = temp_turn_results[idx]
                            with open(t_path, "rb") as infile:
                                outfile.write(infile.read())
                            outfile.write(pause_bytes)

                    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                    words = len(dialogue_script.split())
                    duration_sec = max(30, int((words / 130.0) * 60))
                    print(f"🎉 2-Host Podcast MP3 generated successfully via Gemini Flash ({len(temp_turn_results)}/{len(valid_turns)} turns): {output_path} ({file_size_mb:.2f} MB, {duration_sec // 60}m {duration_sec % 60}s)")
                    return True, duration_sec
                else:
                    print(f"⚠️ Gemini Flash TTS completed {len(temp_turn_results)}/{len(valid_turns)} turns.")
                    return False, 0

        except Exception as e:
            print(f"⚠️ Google AI Studio dialogue error ({e}).")
            return False, 0

    async def build_audio_monologue_edge(self, script_text: str, output_mp3: str) -> str:
        """Fallback Edge-TTS audio generator with sentence-by-sentence pitch contours."""
        import edge_tts
        print(f"🎙️ Using Edge-TTS backup engine with voice '{self.edge_voice}'...")
        
        paragraphs = [p.strip() for p in script_text.strip().split("\n\n") if p.strip()]
        base_dir = os.path.dirname(output_mp3) if os.path.dirname(output_mp3) else "."
        os.makedirs(base_dir, exist_ok=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = []
            sentence_map = []
            global_idx = 0

            for para in paragraphs:
                clean_para = re.sub(r'\[.*?\]|\(.*?\)', '', para).strip()
                sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_para) if s.strip()]
                for s_idx, sentence in enumerate(sentences):
                    if len(re.sub(r'[^a-zA-Z0-9]', '', sentence)) >= 2:
                        is_last = (s_idx == len(sentences) - 1)
                        sentence_map.append((global_idx, is_last))
                        t_path = os.path.join(temp_dir, f"mono_{global_idx:04d}.mp3")
                        
                        async def _synth_sentence(t=sentence, p=t_path):
                            try:
                                comm = edge_tts.Communicate(t, self.edge_voice, rate="-3%", pitch="+0Hz")
                                await comm.save(p)
                                return p
                            except Exception:
                                return ""
                        
                        tasks.append(_synth_sentence())
                        global_idx += 1

            if not tasks:
                raise ValueError("Script text contains no valid sentences for audio synthesis.")

            temp_files = await asyncio.gather(*tasks)
            short_pause = generate_silent_mp3_bytes(650)
            long_pause = generate_silent_mp3_bytes(1400)

            with open(output_mp3, 'wb') as outfile:
                for idx, fname in enumerate(temp_files):
                    if fname and os.path.exists(fname):
                        with open(fname, 'rb') as infile:
                            outfile.write(infile.read())
                        is_para_end = sentence_map[idx][1] if idx < len(sentence_map) else False
                        outfile.write(long_pause if is_para_end else short_pause)

        print(f"🎉 Edge-TTS monologue audio generated successfully: {output_mp3}")
        return output_mp3

    async def build_audio_dialogue_edge(self, dialogue_script: str, output_mp3: str) -> str:
        """Fallback Edge-TTS audio generator for 2-host dialogue (Alex: Christopher, Sarah: Ava)."""
        import edge_tts
        print("🎙️ Synthesizing 2-Host Dialogue via Edge-TTS (Alex: Male [Christopher], Sarah: Female [Ava])...")
        turns = self._parse_dialogue_turns(dialogue_script)
        base_dir = os.path.dirname(output_mp3) if os.path.dirname(output_mp3) else "."
        os.makedirs(base_dir, exist_ok=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            tasks = []
            for idx, (speaker, text) in enumerate(turns):
                clean_text = re.sub(r'\[.*?\]|\(.*?\)', '', text).strip()
                if not clean_text:
                    continue
                voice = EDGE_VOICE_MAP.get(speaker, "en-US-ChristopherNeural" if speaker == "Alex" else "en-US-AvaNeural")
                temp_file = os.path.join(temp_dir, f"edge_turn_{idx:04d}.mp3")

                async def _synth(v=voice, t=clean_text, f=temp_file):
                    try:
                        comm = edge_tts.Communicate(t, v, rate="-2%")
                        await comm.save(f)
                        return f
                    except Exception as ex:
                        print(f"Warning: failed edge synth turn {f}: {ex}")
                        return ""

                tasks.append(_synth())

            temp_files = await asyncio.gather(*tasks)
            pause_bytes = generate_silent_mp3_bytes(500)

            with open(output_mp3, 'wb') as outfile:
                for fname in temp_files:
                    if fname and os.path.exists(fname):
                        with open(fname, 'rb') as infile:
                            outfile.write(infile.read())
                        outfile.write(pause_bytes)

        return output_mp3

    def _attach_intro_outro(self, output_path: str, intro_path: str = "assets/audio/intro.mp3", outro_path: str = "assets/audio/outro.mp3") -> int:
        """Prepends royalty-free intro music and appends outro music to the episode MP3."""
        if not os.path.exists(output_path):
            return 0

        with open(output_path, "rb") as f:
            main_bytes = f.read()

        intro_bytes = b""
        if os.path.exists(intro_path):
            with open(intro_path, "rb") as f:
                intro_bytes = f.read()

        outro_bytes = b""
        if os.path.exists(outro_path):
            with open(outro_path, "rb") as f:
                outro_bytes = f.read()

        pause_short = generate_silent_mp3_bytes(300)

        with open(output_path, "wb") as f:
            if intro_bytes:
                f.write(intro_bytes)
                f.write(pause_short)
            f.write(main_bytes)
            if outro_bytes:
                f.write(pause_short)
                f.write(outro_bytes)

        file_size_bytes = os.path.getsize(output_path)
        # Standard 64kbps MP3 = 8000 bytes per second
        exact_duration_sec = max(30, int(file_size_bytes / 8000))
        return exact_duration_sec

    def dialogue_to_audio(self, dialogue_script: str, output_path: str) -> Dict[str, Any]:
        """Synthesizes 2-host podcast conversation with Google Gemini TTS as primary engine (<10 RPM pacing)."""
        audio_created = False
        duration_seconds = 0

        # 1. Primary Engine: Google AI Studio (Gemini 2.5 Flash TTS) with strict 6.2s pacing (<10 RPM)
        if self.gemini_api_key:
            print("✨ Synthesizing 2-Host Dialogue via Primary Engine: Google Gemini Flash TTS (Alex: Puck [Male], Sarah: Aoede [Female])...")
            audio_created, duration_seconds = self._generate_gemini_dialogue_audio(dialogue_script, output_path)

        # 2. Backup Engine: Edge-TTS (only if Gemini API is unavailable or hits rate limits)
        if not audio_created:
            print("🎙️ Using Edge-TTS Backup Engine (Alex: Christopher [Male], Sarah: Ava [Female])...")
            asyncio.run(self.build_audio_dialogue_edge(dialogue_script, output_path))
            words = len(dialogue_script.split())
            duration_seconds = max(30, int((words / 130.0) * 60))

        # Attach professional royalty-free intro and outro jingles
        if os.path.exists(output_path):
            duration_seconds = self._attach_intro_outro(output_path)

        return self._build_audio_metadata(output_path, duration_seconds)

    def text_to_audio(self, script_text: str, output_path: str) -> Dict[str, Any]:
        """Synthesizes monologue podcast to MP3 with intro/outro."""
        audio_created = False
        duration_seconds = 0

        if self.gemini_api_key:
            audio_created, duration_seconds = self._generate_gemini_audio(script_text, output_path)

        if not audio_created:
            asyncio.run(self.build_audio_monologue_edge(script_text, output_path))
            words = len(script_text.split())
            duration_seconds = max(30, int((words / 130.0) * 60))

        # Attach professional royalty-free intro and outro jingles
        if os.path.exists(output_path):
            duration_seconds = self._attach_intro_outro(output_path)

        return self._build_audio_metadata(output_path, duration_seconds)
