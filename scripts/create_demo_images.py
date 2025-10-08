"""Create demo SVG images for the spam quiz."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
IMAGES_DIR = BASE_DIR / "static" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

COLORS = {
    "sample1.svg": "#f7d7da",
    "sample2.svg": "#c8e6c9",
    "sample3.svg": "#c8d2f0",
}

SVG_TEMPLATE = """<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 600 400\">\n  <rect width=\"600\" height=\"400\" fill=\"#f6f6f8\" rx=\"40\" />\n  <rect x=\"50\" y=\"50\" width=\"500\" height=\"300\" rx=\"30\" fill=\"{card_color}\" />\n  <text x=\"300\" y=\"215\" font-family=\"'Arial', sans-serif\" font-size=\"56\" fill=\"#3c3c3c\" text-anchor=\"middle\">{label}</text>\n</svg>\n"""


def main() -> None:
    for filename, color in COLORS.items():
        label = filename.replace("sample", "Card ").replace(".svg", "")
        svg_content = SVG_TEMPLATE.format(card_color=color, label=label)
        (IMAGES_DIR / filename).write_text(svg_content, encoding="utf-8")
        print(f"Created {filename}")


if __name__ == "__main__":
    main()
