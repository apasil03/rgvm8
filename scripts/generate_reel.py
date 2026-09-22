"""Render a short Ken-Burns style video from a branded card, for Reels.

100% original, locally rendered from the same real specs already in
queue.csv — no third-party video or audio, no network needed. Reels get
far more algorithmic reach than static feed posts, so this is the
legitimate way to get video content without a camera or someone else's
footage.
"""
import subprocess
from pathlib import Path

import imageio_ffmpeg

from generate_card import generate_reel_background

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
DURATION_S = 6
FPS = 30


def generate_reel(brand: str, product_name: str, key_points: str, output_path: str, post_type: str = "affiliate") -> None:
    tmp_bg = str(Path(output_path).with_suffix(".bg.jpg"))
    generate_reel_background(brand, product_name, key_points, tmp_bg, post_type=post_type)

    frames = DURATION_S * FPS
    # Subtle, centered "breathing" zoom (1.0 -> 1.08) — enough motion to
    # qualify as a Reel, mild enough that it never crops the text.
    vf = (
        "scale=2160:3840,"
        f"zoompan=z='min(zoom+0.0006,1.08)':d={frames}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={FPS}"
    )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            FFMPEG, "-y",
            "-loop", "1", "-i", tmp_bg,
            "-vf", vf,
            "-t", str(DURATION_S),
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            output_path,
        ],
        check=True, capture_output=True,
    )
    Path(tmp_bg).unlink(missing_ok=True)


if __name__ == "__main__":
    generate_reel(
        "RW Carbon",
        "BMW F91/F92/F93 M8 DTM Carbon Fiber Rear Diffuser",
        "Genuine carbon fiber with clear coat finish;100% bolt-on using factory diffuser mounting points;Fits all 2019+ M8",
        "/tmp/preview_reel.mp4",
    )
    print("wrote /tmp/preview_reel.mp4")
