from pathlib import Path
import subprocess, threading, sys

# -- 1. Absolute path to the audio folder ---------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
AUDIO_ROOT = PROJECT_ROOT / "audio"

# -- 2. Working player command using PulseAudio ---------------------
PLAYER = ["mpg123", "-q", "-o", "pulse"]

# -- 3. Set speaker volume to 90% (run once on import) --------------
SINK_NAME = "alsa_output.usb-Jieli_Technology_UACDemoV1.0_4150344C3631390E-00.analog-stereo"
try:
    subprocess.run(["pactl", "set-sink-volume", SINK_NAME, "90%"], check=True)
except subprocess.CalledProcessError as e:
    print(f"[audio] failed to set volume: {e}", file=sys.stderr)

# -- 4. Worker function to play a sound ------------------------------
def _play(path: Path) -> None:
    cmd = PLAYER + [str(path)]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[audio] playback failed: {e}", file=sys.stderr)

# -- 5. Public helper to play a named mp3 ----------------------------
def play_sound(name: str, block: bool = False) -> None:
    path = AUDIO_ROOT / f"{name}.mp3"
    if not path.exists():
        raise FileNotFoundError(path)

    if block:
        _play(path)
    else:
        threading.Thread(target=_play, args=(path,), daemon=True).start()