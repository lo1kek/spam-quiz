"""Create demo SVG images for the spam quiz."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
IMAGES_DIR = BASE_DIR / "static" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

CARD_PATTERNS = [
    ("activity01.svg", [70, 120, 60, 40, 80, 65, 50, 45, 55, 35]),
    ("activity02.svg", [180, 200, 160, 185, 210, 195, 170, 205, 190, 175]),
    ("activity03.svg", [60, 45, 70, 55, 40, 35, 50, 65, 55, 45]),
    ("activity04.svg", [150, 180, 40, 35, 160, 175, 45, 50, 165, 170]),
    ("activity05.svg", [95, 120, 110, 140, 135, 125, 90, 105, 115, 100]),
    ("activity06.svg", [40, 45, 50, 55, 45, 50, 55, 60, 50, 45]),
    ("activity07.svg", [200, 190, 210, 205, 195, 220, 215, 225, 200, 210]),
    ("activity08.svg", [85, 95, 75, 110, 120, 90, 105, 115, 80, 100]),
    ("activity09.svg", [55, 140, 45, 150, 50, 145, 60, 155, 65, 135]),
    ("activity10.svg", [130, 135, 140, 145, 150, 155, 160, 165, 170, 175]),
]

SVG_TEMPLATE = """<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 600 400\">\n  <defs>\n    <linearGradient id=\"bg\" x1=\"0\" y1=\"0\" x2=\"0\" y2=\"1\">\n      <stop offset=\"0%\" stop-color=\"#ffffff\" />\n      <stop offset=\"100%\" stop-color=\"#f2f4f8\" />\n    </linearGradient>\n  </defs>\n  <rect width=\"600\" height=\"400\" fill=\"url(#bg)\" rx=\"24\" />\n  <g transform=\"translate(60 60)\">\n    <rect width=\"480\" height=\"280\" rx=\"20\" fill=\"#ffffff\" stroke=\"#dbe1f0\" stroke-width=\"2\" />\n    <g transform=\"translate(40 40)\">\n      <line x1=\"0\" y1=\"0\" x2=\"400\" y2=\"0\" stroke=\"#f0f2f7\" stroke-width=\"1\" />\n      <line x1=\"0\" y1=\"80\" x2=\"400\" y2=\"80\" stroke=\"#f0f2f7\" stroke-width=\"1\" />\n      <line x1=\"0\" y1=\"160\" x2=\"400\" y2=\"160\" stroke=\"#f0f2f7\" stroke-width=\"1\" />\n      <line x1=\"0\" y1=\"240\" x2=\"400\" y2=\"240\" stroke=\"#f0f2f7\" stroke-width=\"1\" />\n      {bars}\n    </g>\n    <text x=\"240\" y=\"20\" font-family=\"'Manrope', 'Arial', sans-serif\" font-size=\"24\" fill=\"#2c2f36\" text-anchor=\"middle\">Активность #{index}</text>\n    <text x=\"240\" y=\"300\" font-family=\"'Manrope', 'Arial', sans-serif\" font-size=\"18\" fill=\"#5f6473\" text-anchor=\"middle\">Красные полоски показывают количество звонков и их длительность</text>\n  </g>\n</svg>\n"""


def make_bars(heights: list[int]) -> str:
    bars = []
    max_height = 220
    for idx, raw_height in enumerate(heights):
        height = max(10, min(max_height, raw_height))
        width = 24
        gap = 16
        x = idx * (width + gap)
        x_pos = x
        y_pos = 240 - height
        bars.append(
            f'<rect x="{x_pos}" y="{y_pos}" width="{width}" height="{height}" rx="6" fill="#d94a4a" />'
        )
    return "\n      ".join(bars)


def main() -> None:
    for index, (filename, heights) in enumerate(CARD_PATTERNS, start=1):
        bars = make_bars(heights)
        svg_content = SVG_TEMPLATE.format(index=str(index).zfill(2), bars=bars)
        (IMAGES_DIR / filename).write_text(svg_content, encoding="utf-8")
        print(f"Created {filename}")


if __name__ == "__main__":
    main()
