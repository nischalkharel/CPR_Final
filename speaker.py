from pathlib import Path
import subprocess, threading, sys

# -- 1.  Absolute path to the audio folder ---------------------------
# This version never depends on where the script is launched from.
PROJECT_ROOT = Path(__file__).resolve().parent          # …/ChessPlayingRobot‑main
AUDIO_ROOT   = PROJECT_ROOT / "audio"                   # …/audio/*.mp3

# -- 2.  The exact mpg123 command that worked in the shell ----------
DEVICE  = "plughw:0,0"                                  # <-- your USB speaker
PLAYER  = ["mpg123", "-q", "-o", "alsa", "-a", DEVICE]   # -q = quiet

# -- 3.  Worker ------------------------------------------------------
def _play(path: Path) -> None:
    cmd = PLAYER + [str(path)]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[audio] playback failed: {e}", file=sys.stderr)

# -- 4.  Public helper ----------------------------------------------
def play_sound(name: str, block: bool = False) -> None:
    """
    Play AUDIO_ROOT/<name>.mp3 on the USB speaker.

        play_sound("BlackTurn")          # non‑blocking
        play_sound("illegal_move", True) # block until done
    """
    path = AUDIO_ROOT / f"{name}.mp3"
    if not path.exists():
        raise FileNotFoundError(path)

    if block:
        _play(path)
    else:
        threading.Thread(target=_play, args=(path,), daemon=True).start()

