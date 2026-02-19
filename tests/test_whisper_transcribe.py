"""Whisper transcription smoke test using a tiny generated audio sample."""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


@pytest.mark.skipif(not shutil.which("whisper"), reason="whisper not installed")
def test_whisper_transcribe_tiny_sample():
    """Generate a tiny silent WAV and verify whisper can process it without error."""
    try:
        import wave
        import struct
    except ImportError:
        pytest.skip("wave/struct modules not available")

    with tempfile.TemporaryDirectory() as tmpdir:
        wav_path = Path(tmpdir) / "silence.wav"

        # Generate 1 second of silence (16kHz, 16-bit mono)
        with wave.open(str(wav_path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(struct.pack("<" + "h" * 16000, *([0] * 16000)))

        result = subprocess.run(
            ["whisper", str(wav_path), "--model", "tiny", "--language", "en"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=tmpdir,
        )
        # whisper should process without crashing (exit 0)
        assert result.returncode == 0, f"whisper failed: {result.stderr}"
