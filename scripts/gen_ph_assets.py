"""
Generate Product Hunt assets for ContentForge:
  - thumbnail_240.png  (240x240 — PH thumbnail)
  - gallery_hero.png   (1270x760 — PH gallery / social preview)
Saves to ~/Desktop/contentforge_ph/
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = os.path.expanduser("~/Desktop/contentforge_ph")
os.makedirs(OUT_DIR, exist_ok=True)

FONT_PATH = os.path.join(os.path.dirname(__file__), "../fonts/bold_font.ttf")

BG_DARK   = (15, 15, 17)
BG_CARD   = (24, 24, 28)
ORANGE    = (249, 115, 22)
GREEN     = (74, 222, 128)
PURPLE    = (192, 132, 252)
WHITE     = (240, 240, 244)
GREY      = (120, 120, 130)
BORDER    = (42, 42, 50)


def load_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()


def rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)


# ── THUMBNAIL 240x240 ────────────────────────────────────────────────────────
def make_thumbnail():
    W, H = 240, 240
    img = Image.new("RGB", (W, H), BG_DARK)
    draw = ImageDraw.Draw(img)

    # Subtle gradient-like background stripe
    for i in range(H):
        alpha = int(10 * (i / H))
        draw.line([(0, i), (W, i)], fill=(ORANGE[0]//6, ORANGE[1]//6, ORANGE[2]//6 + alpha))

    # Icon circle
    cx, cy, r = 120, 88, 46
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=ORANGE)

    # "CF" initials
    font_lg = load_font(42)
    initials = "CF"
    bb = draw.textbbox((0, 0), initials, font=font_lg)
    tw, th = bb[2]-bb[0], bb[3]-bb[1]
    draw.text((cx - tw//2, cy - th//2 - 2), initials, font=font_lg, fill=BG_DARK)

    # Name
    font_name = load_font(26)
    name = "ContentForge"
    try:
        bb = draw.textbbox((0, 0), name, font=font_name)
        tw = bb[2] - bb[0]
        draw.text((W//2 - tw//2, 148), name, font=font_name, fill=WHITE)
    except Exception:
        draw.text((30, 148), name, font=font_name, fill=WHITE)

    # Tagline
    font_sub = load_font(13)
    sub = "Score before you post"
    try:
        bb = draw.textbbox((0, 0), sub, font=font_sub)
        tw = bb[2] - bb[0]
        draw.text((W//2 - tw//2, 182), sub, font=font_sub, fill=GREY)
    except Exception:
        draw.text((50, 182), sub, font=font_sub, fill=GREY)

    # Small version tag
    font_tiny = load_font(10)
    rounded_rect(draw, [W//2-22, 208, W//2+22, 224], radius=4, fill=(40, 40, 50))
    try:
        bb = draw.textbbox((0, 0), "v1.0.0", font=font_tiny)
        tw = bb[2] - bb[0]
        draw.text((W//2 - tw//2, 211), "v1.0.0", font=font_tiny, fill=GREY)
    except Exception:
        pass

    path = os.path.join(OUT_DIR, "thumbnail_240.png")
    img.save(path)
    print(f"  Saved: {path}")


# ── GALLERY HERO 1270x760 ────────────────────────────────────────────────────
def make_hero():
    W, H = 1270, 760
    img = Image.new("RGB", (W, H), BG_DARK)
    draw = ImageDraw.Draw(img)

    # Subtle glow top-left
    for r in range(320, 0, -1):
        alpha = max(0, int(18 - r * 0.055))
        draw.ellipse([0 - r, -60 - r, 0 + r, -60 + r],
                     fill=(ORANGE[0], ORANGE[1]//3, 0))

    # ── LEFT COLUMN ──────────────────────────────────────────────────────────
    lx = 80

    # Badge
    font_badge = load_font(13)
    badge_text = "  FREE TIER AVAILABLE  "
    rounded_rect(draw, [lx, 90, lx + 185, 114], radius=6, fill=(40, 28, 10))
    draw.text((lx + 12, 94), "FREE TIER AVAILABLE", font=font_badge, fill=ORANGE)

    # Main headline
    font_h1 = load_font(52)
    font_h1b = load_font(52)
    draw.text((lx, 128), "Score your content", font=font_h1, fill=WHITE)
    draw.text((lx, 186), "before you post.", font=font_h1b, fill=ORANGE)

    # Sub
    font_sub = load_font(18)
    lines = [
        "28-endpoint API for creators & developers.",
        "16 instant scorers. 12 AI generators.",
        "Zero guesswork.",
    ]
    y = 260
    for line in lines:
        draw.text((lx, y), line, font=font_sub, fill=GREY)
        y += 28

    # Platform pills
    font_pill = load_font(12)
    platforms = ["Twitter", "LinkedIn", "Instagram", "TikTok", "YouTube", "Pinterest", "Email", "Ad Copy"]
    px, py = lx, 356
    for name in platforms:
        try:
            bb = draw.textbbox((0, 0), name, font=font_pill)
            pw = bb[2] - bb[0] + 20
        except Exception:
            pw = 70
        rounded_rect(draw, [px, py, px+pw, py+22], radius=5, fill=BG_CARD, outline=BORDER, width=1)
        draw.text((px + 10, py + 4), name, font=font_pill, fill=GREY)
        px += pw + 8
        if px > lx + 420:
            px = lx
            py += 30

    # CTA button
    font_cta = load_font(16)
    rounded_rect(draw, [lx, 448, lx + 200, 482], radius=8, fill=ORANGE)
    draw.text((lx + 28, 455), "Get free API key", font=font_cta, fill=BG_DARK)

    # ── RIGHT COLUMN — mock JSON card ────────────────────────────────────────
    rx = 700
    card_w, card_h = 490, 400
    card_x, card_y = rx, 100

    rounded_rect(draw, [card_x, card_y, card_x+card_w, card_y+card_h], radius=12, fill=BG_CARD, outline=BORDER, width=1)

    # Card header bar
    rounded_rect(draw, [card_x, card_y, card_x+card_w, card_y+38], radius=12, fill=(30, 30, 36))
    # Traffic lights
    for cx_dot, col in [(card_x+18, (255,90,90)), (card_x+36, (255,190,60)), (card_x+54, (40,200,90))]:
        draw.ellipse([cx_dot-5, card_y+14, cx_dot+5, card_y+24], fill=col)
    font_mono_sm = load_font(11)
    draw.text((card_x + 75, card_y + 12), "POST /v1/score_tweet", font=font_mono_sm, fill=GREY)

    # JSON content
    font_mono = load_font(13)
    lines_json = [
        ('{ "text": "I built this in 48hrs.', WHITE),
        ('  Made $500 last month 💸', WHITE),
        ('  Here\'s how: #buildinpublic" }', WHITE),
        ('', WHITE),
        ('// Response:', GREY),
        ('{', WHITE),
        ('  "score":  83,', GREEN),
        ('  "grade":  "A",', GREEN),
        ('  "hashtag_count":  1,', PURPLE),
        ('  "emoji_count":  1,', PURPLE),
        ('  "power_words_found": ["built"],', ORANGE),
        ('  "suggestions": []', GREEN),
        ('}', WHITE),
    ]
    jy = card_y + 50
    for text, color in lines_json:
        draw.text((card_x + 24, jy), text, font=font_mono, fill=color)
        jy += 22

    # Second mini-card below
    card2_y = card_y + card_h + 16
    card2_h = 124
    rounded_rect(draw, [card_x, card2_y, card_x+card_w, card2_y+card2_h], radius=12, fill=BG_CARD, outline=BORDER, width=1)
    font_tag = load_font(11)
    draw.text((card_x + 20, card2_y + 16), "batch_score — ranked best draft:", font=font_tag, fill=GREY)
    items = [
        ("1st", '"Here are 5 lessons I learned..."', "57", "C"),
        ("2nd", '"Building in public day 1"',         "30", "D"),
    ]
    iy = card2_y + 34
    for rank, preview, score, grade in items:
        grade_color = GREEN if grade == "A" else (ORANGE if grade == "B" else (PURPLE if grade == "C" else (200,80,80)))
        rounded_rect(draw, [card_x+16, iy, card_x+36, iy+18], radius=3, fill=(40,40,50))
        draw.text((card_x+20, iy+2), rank, font=font_tag, fill=GREY)
        draw.text((card_x+44, iy+2), preview, font=font_tag, fill=WHITE)
        rounded_rect(draw, [card_x+card_w-54, iy, card_x+card_w-16, iy+18], radius=3, fill=grade_color)
        draw.text((card_x+card_w-46, iy+2), f"{score} {grade}", font=font_tag, fill=BG_DARK)
        iy += 26

    # ── BOTTOM STATS BAR ─────────────────────────────────────────────────────
    bar_y = H - 80
    draw.line([(0, bar_y), (W, bar_y)], fill=BORDER, width=1)
    stats = [
        ("28", "endpoints"),
        ("16", "instant, no AI"),
        ("12", "AI generators"),
        ("0ms*", "scoring latency"),
        ("Free", "tier available"),
    ]
    font_stat_n = load_font(22)
    font_stat_l = load_font(12)
    step = W // len(stats)
    for i, (num, label) in enumerate(stats):
        sx = step * i + step // 2
        try:
            bb = draw.textbbox((0, 0), num, font=font_stat_n)
            tw = bb[2] - bb[0]
            draw.text((sx - tw//2, bar_y + 10), num, font=font_stat_n, fill=ORANGE)
            bb2 = draw.textbbox((0, 0), label, font=font_stat_l)
            tw2 = bb2[2] - bb2[0]
            draw.text((sx - tw2//2, bar_y + 38), label, font=font_stat_l, fill=GREY)
        except Exception:
            draw.text((sx - 20, bar_y + 10), num, font=font_stat_n, fill=ORANGE)
            draw.text((sx - 30, bar_y + 38), label, font=font_stat_l, fill=GREY)

    path = os.path.join(OUT_DIR, "gallery_hero_1270x760.png")
    img.save(path)
    print(f"  Saved: {path}")


if __name__ == "__main__":
    print("Generating ContentForge Product Hunt assets...")
    make_thumbnail()
    make_hero()
    print(f"\nDone! Files in: {OUT_DIR}")
    print("  thumbnail_240.png      → upload as PH Thumbnail")
    print("  gallery_hero_1270x760.png → upload as first Gallery image")
