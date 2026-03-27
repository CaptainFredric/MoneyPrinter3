#!/usr/bin/env python3
"""Generate the ContentForge 500x500 logo for RapidAPI."""
from PIL import Image, ImageDraw, ImageFont
import math, os

W, H = 500, 500
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Gradient background: deep blue to purple
img = Image.new("RGB", (W, H))
draw = ImageDraw.Draw(img)
for y in range(H):
    r = int(15 + (45 - 15) * (y / H))
    g = int(20 + (10 - 20) * (y / H))
    b = int(80 + (140 - 80) * (y / H))
    draw.line([(0, y), (W, y)], fill=(r, g, b))

# Subtle radial glow in center
for radius in range(120, 0, -1):
    alpha = int(40 * (1 - radius / 120))
    cx, cy = W // 2, H // 2 - 20
    draw.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        fill=(50 + alpha, 30 + alpha, 160 + alpha // 2)
    )

# Spark lines radiating from center
anvil_cx, anvil_cy = 250, 200
for angle_deg in [30, 75, 120, 165, 210, 255, 300, 345]:
    angle = math.radians(angle_deg)
    inner_r, outer_r = 55, 85
    x1 = anvil_cx + inner_r * math.cos(angle)
    y1 = anvil_cy + inner_r * math.sin(angle)
    x2 = anvil_cx + outer_r * math.cos(angle)
    y2 = anvil_cy + outer_r * math.sin(angle)
    draw.line([(x1, y1), (x2, y2)], fill=(255, 200, 60), width=3)

# Center diamond shape
diamond_pts = [
    (anvil_cx, anvil_cy - 40),
    (anvil_cx + 35, anvil_cy),
    (anvil_cx, anvil_cy + 40),
    (anvil_cx - 35, anvil_cy),
]
draw.polygon(diamond_pts, fill=(255, 180, 40), outline=(255, 220, 100))
# Inner facets
draw.line([(anvil_cx, anvil_cy - 40), (anvil_cx + 15, anvil_cy), (anvil_cx, anvil_cy + 40)],
          fill=(255, 220, 100), width=2)
draw.line([(anvil_cx, anvil_cy - 40), (anvil_cx - 15, anvil_cy), (anvil_cx, anvil_cy + 40)],
          fill=(255, 220, 100), width=2)
draw.line([(anvil_cx - 35, anvil_cy), (anvil_cx + 35, anvil_cy)],
          fill=(255, 230, 120), width=1)

# Sparkle dots
for sx, sy in [(180, 140), (320, 150), (170, 250), (330, 240), (200, 170), (300, 175)]:
    draw.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill=(255, 255, 200))

# Fonts
try:
    font_big = ImageFont.truetype("/Library/Fonts/Arial Bold.ttf", 52)
    font_tag = ImageFont.truetype("/Library/Fonts/Arial.ttf", 18)
except Exception:
    font_big = ImageFont.load_default()
    font_tag = font_big

# "CONTENT"
text1 = "CONTENT"
bbox1 = draw.textbbox((0, 0), text1, font=font_big)
tw1 = bbox1[2] - bbox1[0]
draw.text(((W - tw1) // 2, 290), text1, fill=(255, 255, 255), font=font_big)

# "FORGE" in gold
text2 = "FORGE"
bbox2 = draw.textbbox((0, 0), text2, font=font_big)
tw2 = bbox2[2] - bbox2[0]
draw.text(((W - tw2) // 2, 345), text2, fill=(255, 200, 60), font=font_big)

# Thin gold separator
draw.line([(120, 408), (380, 408)], fill=(255, 200, 60), width=1)

# Tagline
tag = "AI-Powered Content Toolkit"
bbox_tag = draw.textbbox((0, 0), tag, font=font_tag)
tw_tag = bbox_tag[2] - bbox_tag[0]
draw.text(((W - tw_tag) // 2, 415), tag, fill=(180, 180, 220), font=font_tag)

# Bottom accent dots
for x_pos in range(180, 321, 20):
    draw.ellipse([x_pos - 2, 450, x_pos + 2, 454], fill=(100, 100, 180))

out_path = os.path.join(ROOT, "assets", "contentforge_logo_500x500.png")
img.save(out_path, "PNG")
print(f"Logo saved: {out_path}")
print(f"Size: {img.size}")
