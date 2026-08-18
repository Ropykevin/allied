"""Generate square elephant-mark favicons from the Allied wordmark."""
from pathlib import Path

from PIL import Image

brand = Path(__file__).resolve().parents[1] / "app" / "static" / "assets" / "brand"
# logo-light: white elephant + cream/gold text — readable on chocolate at small sizes
logo = Image.open(brand / "logo-light.png").convert("RGBA")
_w, h = logo.size  # 1600 x 386

# Elephant sits left-of-center; crop a square around the head/trunk only.
side = h
left = 80
elephant = logo.crop((left, 0, left + side, h))

CHOCOLATE = (65, 41, 25, 255)  # #412919


def make_icon(size: int) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), CHOCOLATE)
    pad = max(2, size // 8)
    target = size - pad * 2
    icon = elephant.copy()
    icon.thumbnail((target, target), Image.Resampling.LANCZOS)
    x = (size - icon.width) // 2
    y = (size - icon.height) // 2
    canvas.paste(icon, (x, y), icon)
    return canvas


make_icon(256).save(brand / "favicon.png", optimize=True)
make_icon(48).save(brand / "favicon-48.png", optimize=True)
make_icon(32).save(brand / "favicon-32.png", optimize=True)
make_icon(192).save(brand / "icon-192.png", optimize=True)
make_icon(512).save(brand / "icon-512.png", optimize=True)
make_icon(180).save(brand / "apple-touch-icon.png", optimize=True)

# Explicit multi-resolution ICO
ico_sizes = [16, 32, 48]
ico_images = [make_icon(s) for s in ico_sizes]

ico_images[0].save(
    brand / "favicon.ico",
    format="ICO",
    sizes=[(s, s) for s in ico_sizes],
    append_images=ico_images[1:],
)

print("Wrote favicon assets in", brand)
for p in sorted(brand.glob("favicon*")) + sorted(brand.glob("icon-*")) + [brand / "apple-touch-icon.png"]:
    if p.exists():
        print(f"  {p.name}: {p.stat().st_size} bytes")
