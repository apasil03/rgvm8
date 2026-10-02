"""Render a short Ken-Burns style video for Reels, either from a generated
branded card or from a real photo.

100% original, locally rendered — no third-party video or audio, no
network needed. Reels get far more algorithmic reach than static feed
posts, so this is the legitimate way to get video content without a
camera, someone else's footage, or licensed music.
"""
import subprocess
from pathlib import Path

import imageio_ffmpeg

from generate_card import generate_reel_background, generate_caption_overlay

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
DURATION_S = 6
FPS = 30


def _animate_to_reel(bg_image_path: str, output_path: str, overlay_path: str = None) -> None:
    """Shared zoom+audio treatment: takes any already-9:16 background image
    (a generated card, or a real photo already fitted to the canvas) and
    renders the final Reel with a subtle zoom and synthesized audio. An
    optional static text overlay (brand/product caption bar) is composited
    on top after the zoom, unscaled, so it stays sharp and in place."""
    frames = DURATION_S * FPS
    # Subtle, centered "breathing" zoom (1.0 -> 1.08) — enough motion to
    # qualify as a Reel, mild enough that it never crops the frame badly.
    vf = (
        "scale=2160:3840,"
        f"zoompan=z='min(zoom+0.0006,1.08)':d={frames}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={FPS}"
    )
    # Soft two-tone ambient pad, synthesized locally (not a real song --
    # the Graph API has no way to attach Meta's in-app licensed music
    # catalog to an API-uploaded video, and baking in an actual
    # copyrighted track ourselves would be the same rights problem as
    # reposting someone else's footage). Gives Reels a non-silent audio
    # bed without any third-party content.
    fade = min(0.6, DURATION_S / 4)
    af = (
        f"[1:a]volume=0.12[a1];[2:a]volume=0.08[a2];"
        f"[a1][a2]amix=inputs=2:duration=first,"
        f"afade=t=in:st=0:d={fade},afade=t=out:st={DURATION_S - fade}:d={fade}[a]"
    )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        FFMPEG, "-y",
        "-loop", "1", "-i", bg_image_path,
        "-f", "lavfi", "-i", f"sine=frequency=110:duration={DURATION_S}",
        "-f", "lavfi", "-i", f"sine=frequency=165:duration={DURATION_S}",
    ]
    if overlay_path:
        cmd += ["-loop", "1", "-i", overlay_path]
        video_chain = f"[0:v]{vf}[zoomed];[zoomed][3:v]overlay=0:0[v]"
    else:
        video_chain = f"[0:v]{vf}[v]"
    cmd += [
        "-filter_complex", f"{video_chain};{af}",
        "-map", "[v]", "-map", "[a]",
        "-t", str(DURATION_S),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "96k",
        "-movflags", "+faststart",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def generate_reel(brand: str, product_name: str, key_points: str, output_path: str, post_type: str = "affiliate") -> None:
    """Fallback path: no real media supplied, so render a branded text card
    and animate that instead."""
    tmp_bg = str(Path(output_path).with_suffix(".bg.jpg"))
    generate_reel_background(brand, product_name, key_points, tmp_bg, post_type=post_type)
    _animate_to_reel(tmp_bg, output_path)
    Path(tmp_bg).unlink(missing_ok=True)


def generate_reel_from_photo(
    photo_path: str, output_path: str,
    brand: str = None, product_name: str = None, post_type: str = "engagement",
) -> None:
    """Turn a real photo into a music-backed Reel instead of a static post
    -- static image posts can't carry audio at all, and Reels get far more
    reach. Fits the photo into the 9:16 canvas with a blurred fill behind
    it (rather than cropping) so nothing in the shot gets cut off.

    When brand/product_name are given, a branded caption bar is composited
    over the bottom of the Reel -- most viewers scroll with sound off, so
    the photo+music alone doesn't carry the message without on-screen text."""
    tmp_bg = str(Path(output_path).with_suffix(".bg.jpg"))
    subprocess.run(
        [
            FFMPEG, "-y",
            "-i", photo_path,
            "-vf",
            "split[bg][fg];"
            "[bg]scale=1080:1920,boxblur=30:5[bgblur];"
            "[fg]scale=1080:1920:force_original_aspect_ratio=decrease[fgscaled];"
            "[bgblur][fgscaled]overlay=(W-w)/2:(H-h)/2",
            "-frames:v", "1",
            tmp_bg,
        ],
        check=True, capture_output=True,
    )

    tmp_overlay = None
    if brand and product_name:
        tmp_overlay = str(Path(output_path).with_suffix(".overlay.png"))
        generate_caption_overlay(brand, product_name, post_type, tmp_overlay)

    _animate_to_reel(tmp_bg, output_path, overlay_path=tmp_overlay)
    Path(tmp_bg).unlink(missing_ok=True)
    if tmp_overlay:
        Path(tmp_overlay).unlink(missing_ok=True)


if __name__ == "__main__":
    generate_reel(
        "RW Carbon",
        "BMW F91/F92/F93 M8 DTM Carbon Fiber Rear Diffuser",
        "Genuine carbon fiber with clear coat finish;100% bolt-on using factory diffuser mounting points;Fits all 2019+ M8",
        "/tmp/preview_reel.mp4",
    )
    print("wrote /tmp/preview_reel.mp4")
