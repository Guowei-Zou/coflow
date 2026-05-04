from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def find_project_root(path: Path) -> Path:
    for candidate in (path, *path.parents):
        if (candidate / "00_project_docs").exists() and (candidate / "setup.py").exists():
            return candidate
    raise RuntimeError("Could not locate project root")


ROOT = find_project_root(Path(__file__).resolve())
PAGE_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = PAGE_ROOT / "assets" / "appendix_keyframes"
OUT_FIG = PAGE_ROOT / "assets" / "appendix_keyframes_preview.png"
OUT_PDF = PAGE_ROOT / "assets" / "appendix_keyframes_preview.pdf"

FRACTIONS = [0.10, 0.35, 0.65, 0.90]

ROWS = [
    {
        "title": "Tag - Expert",
        "description": "Coordinated pressure around the prey.",
        "color": "#dc2626",
        "video": ROOT / "01_video_generation/rollout_rendering/source_tree/trajectory_visualization/mpe_single_videos/videos/mpe_tag_expert_1080p.mp4",
    },
    {
        "title": "World - Expert",
        "description": "Structured movement through food and forests.",
        "color": "#7c3aed",
        "video": ROOT / "01_video_generation/rollout_rendering/source_tree/trajectory_visualization/mpe_single_videos/videos/mpe_world_expert_1080p.mp4",
    },
    {
        "title": "5m_vs_6m - Good",
        "description": "Coordinated micro overcomes the extra enemy.",
        "color": "#db2777",
        "video": ROOT / "01_video_generation/rollout_rendering/source_tree/trajectory_visualization/smac_single_videos/videos/smac_5m_vs_6m_good_1080p.mp4",
    },
    {
        "title": "2-Ant - Good",
        "description": "Coordinated legs sustain locomotion.",
        "color": "#4f46e5",
        "video": ROOT / "01_video_generation/rollout_rendering/source_tree/trajectory_visualization/mamujoco_single_videos/videos/mamujoco_2ant_good_1080p.mp4",
    },
]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    path = Path("/usr/share/fonts/truetype/dejavu") / name
    return ImageFont.truetype(str(path), size)


def video_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    return float(result.stdout.strip())


def extract_frame(video: Path, timestamp: float, output: Path) -> None:
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{timestamp:.3f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            str(output),
        ],
        check=True,
    )


def wrap_text(draw: ImageDraw.ImageDraw, text: str, text_font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        candidate = word if not line else f"{line} {word}"
        if draw.textbbox((0, 0), candidate, font=text_font)[2] <= width:
            line = candidate
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def draw_rounded_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str, width: int) -> None:
    draw.rounded_rectangle(box, radius=18, fill=fill, outline=outline, width=width)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame_paths: dict[tuple[int, int], Path] = {}
    for row_idx, row in enumerate(ROWS):
        duration = video_duration(row["video"])
        for col_idx, frac in enumerate(FRACTIONS):
            ts = max(0.0, min(duration - 0.05, duration * frac))
            out = OUT_DIR / f"row{row_idx + 1}_frame{col_idx + 1}.png"
            extract_frame(row["video"], ts, out)
            frame_paths[(row_idx, col_idx)] = out

    margin = 24
    label_w = 78
    frame_size = 400
    gap = 22
    row_gap = 30
    header_h = 52
    row_h = frame_size + 44

    width = margin * 2 + label_w + gap + len(FRACTIONS) * frame_size + (len(FRACTIONS) - 1) * gap
    height = margin + header_h + len(ROWS) * row_h + (len(ROWS) - 1) * row_gap + margin

    image = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(image)

    label_font = font(36)
    header_font = label_font
    frame_x0 = margin + label_w + gap
    block_x0 = frame_x0 - gap

    for col_idx, frac in enumerate(FRACTIONS):
        x = frame_x0 + col_idx * (frame_size + gap)
        label = f"{int(frac * 100)}%"
        bbox = draw.textbbox((0, 0), label, font=header_font)
        label_x = x + (frame_size - (bbox[2] - bbox[0])) / 2
        draw.text((label_x, margin + 2), label, fill="#222222", font=header_font)

    y = margin + header_h
    for row_idx, row in enumerate(ROWS):
        color = row["color"]
        block = (block_x0, y, width - margin, y + row_h)
        draw_rounded_rect(draw, block, "#fbfbfc", color, 3)
        draw.rounded_rectangle((block_x0, y, block_x0 + 13, y + row_h), radius=8, fill=color)

        row_label = f"({chr(ord('a') + row_idx)})"
        bbox = draw.textbbox((0, 0), row_label, font=label_font)
        label_x = margin + (label_w - (bbox[2] - bbox[0])) / 2
        label_y = y + (row_h - (bbox[3] - bbox[1])) / 2 - 4
        draw.text((label_x, label_y), row_label, fill="#111111", font=label_font)

        for col_idx in range(len(FRACTIONS)):
            x = frame_x0 + col_idx * (frame_size + gap)
            frame = Image.open(frame_paths[(row_idx, col_idx)]).convert("RGB")
            frame.thumbnail((frame_size, frame_size), Image.Resampling.LANCZOS)
            tile = Image.new("RGB", (frame_size, frame_size), "#050b16")
            tile.paste(frame, ((frame_size - frame.width) // 2, (frame_size - frame.height) // 2))
            tile_y = y + 22
            image.paste(tile, (x, tile_y))
            draw.rounded_rectangle((x, tile_y, x + frame_size, tile_y + frame_size), radius=10, outline=color, width=4)

        y += row_h + row_gap

    image.save(OUT_FIG, quality=95)
    image.save(OUT_PDF)
    print(OUT_FIG)
    print(OUT_PDF)


if __name__ == "__main__":
    main()
