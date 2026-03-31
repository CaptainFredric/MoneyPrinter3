"""
Generate Product Hunt gallery images for ContentForge.
Theme: matches the live website — dark #0f0f11 bg, purple #7c6af7, teal #5ec8a0.
Output: ~/Desktop/ContentForge-PH-Assets/
"""
import os
import pathlib

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = pathlib.Path.home() / "Desktop" / "ContentForge-PH-Assets"
OUT_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1270, 760  # all gallery images (safely under 2000px)

# ── Website palette (matches index.html exactly) ─────────────────────────────
BG_PAGE   = "#0f0f11"   # body background
BG_CARD   = "#141418"   # card / pre / demo-card
BG_CARD2  = "#1e1e28"   # badge bg, stat border, slightly lighter card
BG_DEEP   = "#0d0d10"   # code block interior
BG_HERO_GLOW = (124, 106, 247, 18)  # rgba for radial purple glow
PURPLE    = "#7c6af7"   # primary accent — CTA, logo, numbers, step circles
PURPLE2   = "#6a57e6"   # gradient end for buttons / step circles
TEAL      = "#5ec8a0"   # success, grade A, fast badge, after-card border
RED       = "#e87777"   # grade C/D, before-card border
YELLOW    = "#f7c948"   # code value color (c-val)
WHITE     = "#f0f0f5"   # heading text (h1, h2, h3)
TEXT_MAIN = "#e8e8ec"   # body / code text
TEXT_SUB  = "#9999aa"   # muted — subtitles, labels, section-sub
TEXT_DIM  = "#555566"   # very dim — footnotes, ep-click-hint
BORDER    = "#2e2e40"   # card borders
BORDER2   = "#1e1e28"   # softer inner border (stats, demo)
AI_BG     = "#1e1532"   # ep-badge.ai background
FAST_BG   = "#0e2018"   # ep-badge.fast background
AFTER_BG  = "#0e2018"   # demo-card after bg tint
BEFORE_BG = "#2a1515"   # demo-card before bg tint


# ── Helpers ───────────────────────────────────────────────────────────────────

def _font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold
        else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSMono.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def new_canvas(w=W, h=H):
    """Flat dark background with subtle purple radial glow (matches website hero)."""
    img = Image.new("RGB", (w, h), BG_PAGE)
    # Draw soft radial purple glow in the upper-center area
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    cx2, cy2 = w // 2, h // 4
    for radius in range(320, 0, -4):
        alpha = int(BG_HERO_GLOW[3] * (1 - radius / 320) * 1.6)
        alpha = min(alpha, 40)
        od.ellipse(
            (cx2 - radius * 2, cy2 - radius, cx2 + radius * 2, cy2 + radius),
            fill=(BG_HERO_GLOW[0], BG_HERO_GLOW[1], BG_HERO_GLOW[2], alpha),
        )
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    return img, ImageDraw.Draw(img)


def rr(draw, xy, r=12, fill=None, outline=None, w=1):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=w)


def accent_bar(img, y, thickness=3):
    """Thin purple-to-teal gradient top/bottom accent bar."""
    draw = ImageDraw.Draw(img)
    r1, g1, b1 = hex_rgb(PURPLE)
    r2, g2, b2 = hex_rgb(TEAL)
    for x in range(W):
        t = x / W
        c = (int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t))
        draw.line([(x, y), (x, y+thickness)], fill=c)


def badge_pill(draw, cx, cy, text, font=None, fg=PURPLE, bg=BG_CARD2,
               border=BORDER, pad_x=14, pad_y=5):
    """Draw a rounded pill badge centred at (cx, cy)."""
    if font is None:
        font = _font(16, bold=True)
    bb = draw.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]; th = bb[3] - bb[1]
    bw = tw + pad_x * 2; bh = th + pad_y * 2
    x0 = cx - bw // 2; y0 = cy - bh // 2
    rr(draw, (x0, y0, x0+bw, y0+bh), r=bh//2, fill=bg, outline=border)
    draw.text((cx, cy), text, font=font, fill=fg, anchor="mm")
    return bw, bh


def logo_text(draw, cx, cy, size=40):
    """Draw 'Content[white] Forge[purple]' wordmark centred at (cx, cy)."""
    fb = _font(size, bold=True)
    w1 = draw.textlength("Content", font=fb)
    w2 = draw.textlength("Forge",   font=fb)
    total = w1 + w2
    x0 = cx - total // 2
    draw.text((x0,    cy), "Content", font=fb, fill=WHITE,  anchor="lm")
    draw.text((x0+w1, cy), "Forge",   font=fb, fill=PURPLE, anchor="lm")


def save(img, name):
    p = OUT_DIR / name
    img.save(p, "PNG", optimize=True)
    print(f"  Saved -> {p}")
    return p


# ─────────────────────────────────────────────────────────────────────────────
# 01  Hero
# ─────────────────────────────────────────────────────────────────────────────
def make_hero():
    img, draw = new_canvas()
    accent_bar(img, 0)

    # Logo wordmark top-left
    logo_text(draw, W // 2, 62, size=36)

    # Badge pill
    badge_pill(draw, W // 2, 120,
               "⚡ 28 endpoints · 16 instant · 12 AI · Free tier",
               font=_font(17, bold=True))

    # H1
    line1 = "Stop guessing."
    line2_a = "Start "
    line2_b = "scoring"
    line2_c = " your content."
    draw.text((W // 2, 185), line1, font=_font(58, bold=True), fill=WHITE, anchor="mm")
    # Render line2 with purple "scoring"
    f58b = _font(58, bold=True)
    w_a = draw.textlength(line2_a, font=f58b)
    w_b = draw.textlength(line2_b, font=f58b)
    w_c = draw.textlength(line2_c, font=f58b)
    total_w = w_a + w_b + w_c
    x_start = (W - total_w) // 2
    y2 = 254
    draw.text((x_start,           y2), line2_a, font=f58b, fill=WHITE,  anchor="lm")
    draw.text((x_start + w_a,     y2), line2_b, font=f58b, fill=PURPLE, anchor="lm")
    draw.text((x_start + w_a + w_b, y2), line2_c, font=f58b, fill=WHITE, anchor="lm")

    # Sub text
    sub = "A REST API that scores content for Twitter, LinkedIn, Instagram, TikTok,"
    sub2 = "YouTube, Pinterest, email & ad copy — then rewrites with AI."
    draw.text((W // 2, 312), sub,  font=_font(20), fill=TEXT_SUB, anchor="mm")
    draw.text((W // 2, 338), sub2, font=_font(20), fill=TEXT_SUB, anchor="mm")

    # CTA buttons
    btn_w, btn_h = 320, 50
    bx1 = W // 2 - btn_w - 10; bx2 = W // 2 + 10; by = 370
    rr(draw, (bx1, by, bx1+btn_w, by+btn_h), r=10, fill=PURPLE)
    draw.text((bx1+btn_w//2, by+btn_h//2), "Start Free on RapidAPI →",
              font=_font(18, bold=True), fill=WHITE, anchor="mm")
    rr(draw, (bx2, by, bx2+btn_w, by+btn_h), r=10, fill=BG_CARD2, outline=BORDER)
    draw.text((bx2+btn_w//2, by+btn_h//2), "See All Endpoints",
              font=_font(18, bold=True), fill=TEXT_MAIN, anchor="mm")

    # Stat cards row
    stats = [("28", "Endpoints"), ("16", "Instant Scorers"), ("12", "AI Tools"), ("9+", "Platforms")]
    card_w = 260; card_h = 108; gap = 18
    total_cw = len(stats) * card_w + (len(stats) - 1) * gap
    sx = (W - total_cw) // 2; sy = 448
    # Separator line above stats (mimics website stats bar border-top)
    draw.line([(0, sy - 10), (W, sy - 10)], fill=BORDER2)
    for i, (val, lbl) in enumerate(stats):
        cx2 = sx + i * (card_w + gap)
        draw.text((cx2 + card_w // 2, sy + 42), val, font=_font(52, bold=True), fill=PURPLE, anchor="mm")
        draw.text((cx2 + card_w // 2, sy + 82), lbl, font=_font(18),            fill=TEXT_SUB, anchor="mm")
    draw.line([(0, sy + card_h + 8), (W, sy + card_h + 8)], fill=BORDER2)

    # Footer note
    draw.text((W // 2, 614), "Free tier included · No credit card required",
              font=_font(18), fill=TEXT_DIM, anchor="mm")

    accent_bar(img, H - 3)
    return save(img, "01_hero.png")


# ─────────────────────────────────────────────────────────────────────────────
# 02  How It Works
# ─────────────────────────────────────────────────────────────────────────────
def make_how_it_works():
    img, draw = new_canvas()
    accent_bar(img, 0)

    draw.text((W // 2, 72),  "How ContentForge Works",
              font=_font(50, bold=True), fill=WHITE, anchor="mm")
    draw.text((W // 2, 116), "From raw copy to optimised content in milliseconds",
              font=_font(21), fill=TEXT_SUB, anchor="mm")

    steps = [
        ("1", "POST Your Content",
         "Send text to any endpoint.\nTweet, headline, caption,\nLinkedIn post — anything."),
        ("2", "Instant Analysis",
         "Heuristic engine scores 20+\nfactors in <50 ms — no\nAI latency for scoring."),
        ("3", "Actionable Output",
         "Score, grade, platform tips,\nand AI rewrite suggestions\nall in clean JSON."),
    ]
    card_w = 340; card_h = 430; gap = 35
    total = len(steps) * card_w + (len(steps) - 1) * gap
    sx = (W - total) // 2; sy = 160

    for i, (num, head, body) in enumerate(steps):
        cx = sx + i * (card_w + gap)
        rr(draw, (cx, sy, cx+card_w, sy+card_h), r=14, fill=BG_CARD, outline=BORDER)
        # Purple-to-teal top accent on each card
        for x in range(cx, cx+card_w):
            t = (x - cx) / card_w
            r1, g1, b1 = hex_rgb(PURPLE); r2, g2, b2 = hex_rgb(TEAL)
            draw.line([(x, sy), (x, sy+3)],
                      fill=(int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t)))
        # Step number circle (gradient approximated as solid purple)
        ccx = cx + card_w // 2; ccy = sy + 90; cr = 36
        draw.ellipse((ccx-cr, ccy-cr, ccx+cr, ccy+cr), fill=PURPLE)
        draw.text((ccx, ccy), num, font=_font(38, bold=True), fill=WHITE, anchor="mm")

        draw.text((cx + card_w // 2, sy + 162), head,
                  font=_font(24, bold=True), fill=WHITE, anchor="mm")
        for j, line in enumerate(body.split("\n")):
            draw.text((cx + card_w // 2, sy + 210 + j * 30), line,
                      font=_font(19), fill=TEXT_SUB, anchor="mm")

        # Arrow connector
        if i < len(steps) - 1:
            ax = cx + card_w + gap // 2; ay = sy + card_h // 2
            draw.polygon([(ax-10, ay-13), (ax+10, ay), (ax-10, ay+13)], fill=PURPLE)

    draw.text((W // 2, 660), "Scorer latency: <50 ms  ·  AI endpoints: ~1-3 s",
              font=_font(19), fill=TEXT_DIM, anchor="mm")
    accent_bar(img, H - 3)
    return save(img, "02_how_it_works.png")


# ─────────────────────────────────────────────────────────────────────────────
# 03  Platform Coverage
# ─────────────────────────────────────────────────────────────────────────────
def make_platforms():
    img, draw = new_canvas()
    accent_bar(img, 0)

    draw.text((W // 2, 66), "16 Platform Scorers — One API",
              font=_font(48, bold=True), fill=WHITE, anchor="mm")
    draw.text((W // 2, 110), "Benchmark against platform-specific best practices instantly",
              font=_font(21), fill=TEXT_SUB, anchor="mm")

    platforms = [
        ("Twitter / X",    PURPLE, "Hook · CTA · hashtag density",     True),
        ("LinkedIn",       PURPLE, "Professional tone · length",        False),
        ("Instagram",      TEAL,   "Hook · emoji · hashtag count",      False),
        ("TikTok",         TEAL,   "Trend language · hook speed",       False),
        ("YouTube Title",  PURPLE, "SEO · click-through · length",      False),
        ("YouTube Desc",   PURPLE, "Keywords · CTA · chapter marks",    False),
        ("Pinterest",      TEAL,   "Keyword richness · visual cues",    False),
        ("Threads",        PURPLE, "Conversation starters",             False),
        ("Facebook",       TEAL,   "Engagement triggers · tone",        False),
        ("Email Subject",  PURPLE, "Open-rate signals · spam score",    False),
        ("Ad Copy",        TEAL,   "AIDA structure · urgency",          False),
        ("Readability",    PURPLE, "Flesch-Kincaid grade",              False),
        ("Headlines",      TEAL,   "Power words · numbers · SEO",       False),
        ("Hashtags",       PURPLE, "Density · relevance scoring",       False),
        ("Batch Score",    TEAL,   "All platforms at once",             False),
        ("Score Multi",    PURPLE, "Up to 100 texts/request",           False),
    ]
    cols = 4; pad = 7
    card_w = (W - 80) // cols
    card_h = (H - 190) // 4
    for idx, (name, color, desc, _) in enumerate(platforms):
        col = idx % cols; row = idx // cols
        cx = 40 + col * card_w; cy = 152 + row * card_h
        rr(draw, (cx+pad, cy+pad, cx+card_w-pad, cy+card_h-pad),
           r=10, fill=BG_CARD, outline=BORDER)
        # Left accent tab
        rr(draw, (cx+pad, cy+pad, cx+pad+4, cy+card_h-pad), r=2, fill=color)
        draw.text((cx + 22, cy + card_h // 2 - 11), name,
                  font=_font(17, bold=True), fill=WHITE, anchor="lm")
        draw.text((cx + 22, cy + card_h // 2 + 13), desc[:40],
                  font=_font(13), fill=TEXT_SUB, anchor="lm")

    accent_bar(img, H - 3)
    return save(img, "03_platforms.png")


# ─────────────────────────────────────────────────────────────────────────────
# 04  AI Generators
# ─────────────────────────────────────────────────────────────────────────────
def make_ai_endpoints():
    img, draw = new_canvas()
    accent_bar(img, 0)

    draw.text((W // 2, 66), "12 AI-Powered Generators",
              font=_font(48, bold=True), fill=WHITE, anchor="mm")
    draw.text((W // 2, 110), "Powered by Gemini — generate ready-to-post content in seconds",
              font=_font(21), fill=TEXT_SUB, anchor="mm")

    generators = [
        ("Content Calendar",  "/content_calendar",       "7-day platform-tailored plan",    "AI"),
        ("Hook Generator",    "/generate_hooks",          "5 attention-grabbing openings",   "AI"),
        ("Thread Outline",    "/thread_outline",          "Numbered X thread structure",     "AI"),
        ("Tweet Ideas",       "/tweet_ideas",             "5 angles from any topic",         "AI"),
        ("LinkedIn Post",     "/generate_linkedin_post",  "Full article with formatting",    "AI"),
        ("Bio Generator",     "/generate_bio",            "Platform-optimised bio",          "AI"),
        ("Caption Generator", "/generate_caption",        "Instagram/TikTok + hashtags",     "AI"),
        ("Email Sequence",    "/generate_email_seq",      "3-email warm-up sequence",        "AI"),
        ("Improve Headline",  "/improve_headline",        "AI headline power-up",            "AI"),
        ("Rewrite",           "/rewrite",                 "Adapt for any platform/tone",     "AI"),
        ("Content Brief",     "/generate_content_brief",  "Angle, hooks, CTA, keywords",     "AI"),
        ("Batch Score",       "/batch_score",             "Score 100 items at once",         "FAST"),
    ]
    cols = 4; rows = 3
    cw = (W - 60) // cols; ch = (H - 190) // rows
    for idx, (name, ep, desc, badge) in enumerate(generators):
        col = idx % cols; row = idx // cols
        cx = 30 + col * cw; cy = 150 + row * ch
        rr(draw, (cx+6, cy+6, cx+cw-6, cy+ch-6), r=12, fill=BG_CARD, outline=BORDER)
        # Top accent bar per card
        for x in range(cx+6, cx+cw-6):
            t = (x - cx - 6) / (cw - 12)
            r1, g1, b1 = hex_rgb(PURPLE); r2, g2, b2 = hex_rgb(TEAL)
            draw.line([(x, cy+6), (x, cy+9)],
                      fill=(int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t)))
        draw.text((cx+cw//2, cy+34), name, font=_font(19, bold=True), fill=WHITE, anchor="mm")
        draw.text((cx+cw//2, cy+57), ep,   font=_font(13),            fill=PURPLE, anchor="mm")
        draw.text((cx+cw//2, cy+82), desc, font=_font(14),            fill=TEXT_SUB, anchor="mm")
        # Badge pill bottom
        if badge == "AI":
            badge_pill(draw, cx+cw//2, cy+ch-28, "AI",
                       font=_font(12, bold=True), fg=PURPLE, bg=AI_BG, border="#2e2040", pad_x=10, pad_y=3)
        else:
            badge_pill(draw, cx+cw//2, cy+ch-28, "FAST",
                       font=_font(12, bold=True), fg=TEAL, bg=FAST_BG, border="#1e3028", pad_x=10, pad_y=3)

    accent_bar(img, H - 3)
    return save(img, "04_ai_generators.png")


# ─────────────────────────────────────────────────────────────────────────────
# 05  Quick Start
# ─────────────────────────────────────────────────────────────────────────────
def make_quickstart():
    img, draw = new_canvas()
    accent_bar(img, 0)

    draw.text((W // 2, 66),  "Get Started in Seconds",
              font=_font(46, bold=True), fill=WHITE, anchor="mm")
    draw.text((W // 2, 110), "No SDK required — one HTTP request gets you scoring",
              font=_font(21), fill=TEXT_SUB, anchor="mm")

    lw = 570; lh = 450; ly = 148

    def panel(px, py, pw, lbl):
        rr(draw, (px, py, px+pw, py+lh), r=12, fill=BG_DEEP, outline=BORDER)
        rr(draw, (px, py, px+pw, py+44), r=12, fill=BG_CARD, outline=BORDER)
        for ci, col in enumerate(["#FF5F57", "#FEBC2E", "#28C840"]):
            draw.ellipse((px+14+ci*22, py+13, px+26+ci*22, py+25), fill=col)
        draw.text((px+pw//2, py+22), lbl, font=_font(14), fill=TEXT_DIM, anchor="mm")

    panel(48, ly, lw, "Python")
    code = [
        ("# Score a tweet before posting",         TEXT_DIM),
        ("import requests",                         PURPLE),
        ("",                                        TEXT_DIM),
        ("HEADERS = {",                             TEXT_MAIN),
        ('  "X-RapidAPI-Key": "YOUR_KEY",',         TEAL),
        ('  "Content-Type": "application/json"',    TEAL),
        ("}",                                       TEXT_MAIN),
        ("",                                        TEXT_DIM),
        ("r = requests.post(",                      PURPLE),
        ('  "https://contentforge1.p',              TEXT_MAIN),
        ('   .rapidapi.com/score_tweet",',          TEXT_MAIN),
        ("  headers=HEADERS,",                      TEXT_MAIN),
        ('  json={"text": "Just shipped!"})',       TEAL),
        ("print(r.json())",                         PURPLE),
    ]
    ty = ly + 56
    for line, col in code:
        draw.text((66, ty), line, font=_font(16), fill=col, anchor="lm")
        ty += 26

    rx = 48 + lw + 32
    panel(rx, ly, W - rx - 48, "Response")
    resp = [
        ("{",                              TEXT_MAIN),
        ('  "score": 82,',                 YELLOW),
        ('  "grade": "B+",',               YELLOW),
        ('  "platform": "twitter",',       TEAL),
        ('  "feedback": [',                TEXT_MAIN),
        ('    "Strong hook",',             TEXT_SUB),
        ('    "CTA present",',             TEXT_SUB),
        ('    "Good emoji use"',           TEXT_SUB),
        ('  ],',                           TEXT_MAIN),
        ('  "latency_ms": 12',             PURPLE),
        ("}",                              TEXT_MAIN),
    ]
    ty = ly + 56
    for line, col in resp:
        draw.text((rx + 16, ty), line, font=_font(16), fill=col, anchor="lm")
        ty += 28

    draw.text((W // 2, 656), "Free tier · No credit card · 300 requests/month",
              font=_font(19), fill=TEXT_DIM, anchor="mm")
    accent_bar(img, H - 3)
    return save(img, "05_quickstart.png")


# ─────────────────────────────────────────────────────────────────────────────
# 06  Pricing
# ─────────────────────────────────────────────────────────────────────────────
def make_pricing():
    img, draw = new_canvas()
    accent_bar(img, 0)

    draw.text((W // 2, 66),  "Simple, Transparent Pricing",
              font=_font(48, bold=True), fill=WHITE, anchor="mm")
    draw.text((W // 2, 112), "Start free. Scale as you grow.",
              font=_font(21), fill=TEXT_SUB, anchor="mm")

    tiers = [
        ("BASIC", "$0",  "/mo", TEXT_SUB,
         ["300 req/month", "50 AI calls", "All 16 scorers", "Community support"], False),
        ("PRO",   "$9",  "/mo", PURPLE,
         ["1,000 req/month", "750 AI calls", "All 28 endpoints", "Email support"], False),
        ("ULTRA", "$29", "/mo", PURPLE,
         ["4,000 req/month", "3,000 AI calls", "Priority routing", "Slack support"], True),
        ("MEGA",  "$99", "/mo", TEXT_SUB,
         ["20k req/month", "18k AI calls", "Dedicated support", "SLA guarantee"], False),
    ]
    cw = 270; ch = 476; gap = 18
    total = len(tiers) * cw + (len(tiers) - 1) * gap
    sx = (W - total) // 2; sy = 148

    for i, (tier, price, unit, color, feats, pop) in enumerate(tiers):
        cx = sx + i * (cw + gap)
        card_bg = BG_CARD2 if pop else BG_CARD
        card_border = PURPLE if pop else BORDER
        card_bw = 2 if pop else 1
        rr(draw, (cx, sy, cx+cw, sy+ch), r=14, fill=card_bg,
           outline=card_border, w=card_bw)
        # "POPULAR" pill for featured card
        if pop:
            bf = _font(13, bold=True)
            badge_pill(draw, cx+cw//2, sy-11, "POPULAR",
                       font=bf, fg=WHITE, bg=PURPLE, border=PURPLE, pad_x=14, pad_y=4)
        tier_col = PURPLE if pop else color
        draw.text((cx+cw//2, sy+44),  tier,  font=_font(22, bold=True), fill=tier_col, anchor="mm")
        draw.text((cx+cw//2, sy+108), price, font=_font(54, bold=True), fill=WHITE,    anchor="mm")
        draw.text((cx+cw//2, sy+150), unit,  font=_font(17),            fill=TEXT_SUB, anchor="mm")
        draw.line([(cx+20, sy+170), (cx+cw-20, sy+170)], fill=BORDER)
        for j, feat in enumerate(feats):
            dot_col = TEAL if pop else PURPLE
            draw.text((cx+26, sy+196+j*48), "✓ "+feat, font=_font(16),
                      fill=(WHITE if pop else TEXT_SUB), anchor="lm")
        # CTA button at bottom of card
        btn_y = sy + ch - 52
        if pop:
            rr(draw, (cx+16, btn_y, cx+cw-16, btn_y+36), r=8, fill=PURPLE)
            draw.text((cx+cw//2, btn_y+18), "Get Started →",
                      font=_font(15, bold=True), fill=WHITE, anchor="mm")
        else:
            rr(draw, (cx+16, btn_y, cx+cw-16, btn_y+36), r=8, fill=BG_CARD2, outline=BORDER)
            draw.text((cx+cw//2, btn_y+18), "Get Started",
                      font=_font(15, bold=True), fill=PURPLE, anchor="mm")

    draw.text((W // 2, 686), "10% off with code  PH10OFF  on Product Hunt",
              font=_font(19), fill=TEAL, anchor="mm")
    accent_bar(img, H - 3)
    return save(img, "06_pricing.png")


# ─────────────────────────────────────────────────────────────────────────────
# 07  Score Demo  (Before / After — matches website demo section)
# ─────────────────────────────────────────────────────────────────────────────
def make_score_demo():
    img, draw = new_canvas()
    accent_bar(img, 0)

    draw.text((W // 2, 66), "See the Difference",
              font=_font(50, bold=True), fill=WHITE, anchor="mm")
    sub = "Run a weak headline through /v1/improve_headline — AI rewrites and scores both"
    draw.text((W // 2, 112), sub, font=_font(19), fill=TEXT_SUB, anchor="mm")

    # ── Before card ──────────────────────────────────────────────────────────
    card_w = 500; card_h = 300; gap = 80; top_y = 160
    bx = (W - card_w * 2 - gap) // 2
    ax = bx + card_w + gap

    rr(draw, (bx, top_y, bx+card_w, top_y+card_h), r=12, fill=BEFORE_BG, outline=RED, w=2)
    badge_pill(draw, bx + 80, top_y - 10, "BEFORE",
               font=_font(12, bold=True), fg=RED, bg=BEFORE_BG, border=RED, pad_x=12, pad_y=4)
    draw.text((bx+card_w//2, top_y+65), '"How to make money online"',
              font=_font(23, bold=True), fill=TEXT_MAIN, anchor="mm")
    draw.text((bx+card_w//2, top_y+110), "Score:",
              font=_font(20), fill=TEXT_SUB, anchor="mm")
    draw.text((bx+card_w//2 + 50, top_y+110), "49",
              font=_font(26, bold=True), fill=RED, anchor="mm")
    draw.text((bx+card_w//2 + 90, top_y+110), "Grade: C",
              font=_font(20, bold=True), fill=RED, anchor="mm")
    draw.text((bx+card_w//2, top_y+150), "Generic · no specificity · no hook",
              font=_font(17), fill=TEXT_DIM, anchor="mm")

    # Score circle left-panel
    ccx = bx + card_w // 2; ccy = top_y + card_h + 100; cr = 80
    draw.ellipse((ccx-cr-6, ccy-cr-6, ccx+cr+6, ccy+cr+6), fill=RED, outline=RED)
    draw.ellipse((ccx-cr,   ccy-cr,   ccx+cr,   ccy+cr),   fill=BG_CARD)
    draw.text((ccx, ccy - 10), "49",     font=_font(52, bold=True), fill=RED,      anchor="mm")
    draw.text((ccx, ccy + 38), "Grade C", font=_font(20, bold=True), fill=RED,      anchor="mm")

    # Arrow
    draw.text((W // 2, top_y + card_h // 2), "→",
              font=_font(60, bold=True), fill=PURPLE, anchor="mm")

    # ── After card ──────────────────────────────────────────────────────────
    rr(draw, (ax, top_y, ax+card_w, top_y+card_h), r=12, fill=AFTER_BG, outline=TEAL, w=2)
    badge_pill(draw, ax + 76, top_y - 10, "AFTER",
               font=_font(12, bold=True), fg=TEAL, bg=AFTER_BG, border=TEAL, pad_x=12, pad_y=4)
    draw.text((ax+card_w//2, top_y+55), '"Can You Really Earn $5,000/mo',
              font=_font(20, bold=True), fill=TEXT_MAIN, anchor="mm")
    draw.text((ax+card_w//2, top_y+82), 'Online? Discover the Secrets"',
              font=_font(20, bold=True), fill=TEXT_MAIN, anchor="mm")
    draw.text((ax+card_w//2, top_y+126), "Score:",
              font=_font(20), fill=TEXT_SUB, anchor="mm")
    draw.text((ax+card_w//2 + 50, top_y+126), "100",
              font=_font(26, bold=True), fill=TEAL, anchor="mm")
    draw.text((ax+card_w//2 + 98, top_y+126), "Grade: A",
              font=_font(20, bold=True), fill=TEAL, anchor="mm")
    draw.text((ax+card_w//2, top_y+168), "Power words · question hook · specific number",
              font=_font(17), fill=TEXT_DIM, anchor="mm")

    ccx2 = ax + card_w // 2; ccy2 = top_y + card_h + 100
    draw.ellipse((ccx2-cr-6, ccy2-cr-6, ccx2+cr+6, ccy2+cr+6), fill=TEAL, outline=TEAL)
    draw.ellipse((ccx2-cr,   ccy2-cr,   ccx2+cr,   ccy2+cr),   fill=BG_CARD)
    draw.text((ccx2, ccy2 - 10), "100",    font=_font(48, bold=True), fill=TEAL,     anchor="mm")
    draw.text((ccx2, ccy2 + 38), "Grade A", font=_font(20, bold=True), fill=TEAL,     anchor="mm")

    draw.text((W // 2, 700), "Latency: 12 ms  ·  No AI required for instant scoring",
              font=_font(17), fill=TEXT_DIM, anchor="mm")
    accent_bar(img, H - 3)
    return save(img, "07_score_demo.png")


# ─────────────────────────────────────────────────────────────────────────────
# 08  GitHub Pages / Live Site Card
# ─────────────────────────────────────────────────────────────────────────────
def make_github_card():
    import urllib.request, ssl, re, html as html_mod
    site = {
        "title":    "ContentForge",
        "subtitle": "Score. Improve. Generate. Ship better content.",
        "url":      "captainfredric.github.io/ContentForge",
        "live":     False,
        "features": [],
    }
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(
            "https://captainfredric.github.io/ContentForge/",
            headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        site["live"] = True
        headings = re.findall(r'<h[123][^>]*>(.*?)</h[123]>', raw, re.I | re.S)
        clean = [html_mod.unescape(re.sub(r'<[^>]+>', '', h)).strip() for h in headings]
        site["features"] = [c for c in clean if c and len(c) > 3][:6]
        m = re.search(r'<title>(.*?)</title>', raw, re.I)
        if m:
            t = html_mod.unescape(re.sub(r'<[^>]+>', '', m.group(1)).strip())
            for sep in [' — ', ' | ', ' - ']:
                if sep in t:
                    t = t.split(sep)[0].strip()
                    break
            site["title"] = t[:36]
    except Exception as e:
        print(f"  [fetch] {e}")

    img, draw = new_canvas()
    accent_bar(img, 0)

    # Browser chrome panel
    panel_y = 100
    rr(draw, (48, panel_y, W-48, H-50), r=14, fill=BG_DEEP, outline=BORDER)
    rr(draw, (48, panel_y, W-48, panel_y+48), r=14, fill=BG_CARD, outline=BORDER)
    # Traffic lights
    for ci, col in enumerate(["#FF5F57", "#FEBC2E", "#28C840"]):
        draw.ellipse((72+ci*24, panel_y+14, 84+ci*24, panel_y+26), fill=col)
    # URL bar
    rr(draw, (196, panel_y+10, W-196, panel_y+38), r=8, fill=BG_PAGE, outline=BORDER)
    draw.text(((196+W-196)//2, panel_y+24), "  " + site["url"],
              font=_font(16), fill=TEXT_SUB, anchor="mm")
    # LIVE badge
    badge_col = TEAL if site["live"] else RED
    badge_txt = "● LIVE" if site["live"] else "○ OFFLINE"
    badge_pill(draw, W-100, panel_y+24, badge_txt,
               font=_font(13, bold=True), fg=badge_col,
               bg=FAST_BG if site["live"] else BEFORE_BG,
               border=TEAL if site["live"] else RED, pad_x=10, pad_y=4)

    # Site title + subtitle
    py = panel_y + 88
    logo_text(draw, W // 2, py, size=46)
    draw.text((W // 2, py + 56), site["subtitle"][:72],
              font=_font(21), fill=TEXT_SUB, anchor="mm")

    # Hero badge from the live site
    badge_pill(draw, W // 2, py + 106,
               "⚡ 28 endpoints · 16 instant · 12 AI · Free tier",
               font=_font(16, bold=True))

    # Feature bullets in a 2-column grid
    if not site["features"]:
        site["features"] = [
            "28 REST endpoints", "16 instant scorers",
            "12 AI generators", "Zero-latency scoring",
            "Free tier included", "RapidAPI marketplace",
        ]
    for i, feat in enumerate(site["features"][:6]):
        co = i % 2; ro = i // 2
        fx = 170 + co * 480; fy = py + 160 + ro * 46
        ficon = "→"
        draw.text((fx, fy), f"{ficon}  {feat[:48]}", font=_font(18), fill=TEXT_SUB, anchor="lm")

    draw.text((W // 2, H - 64),
              "Fetched live from captainfredric.github.io/ContentForge",
              font=_font(15), fill=TEXT_DIM, anchor="mm")
    accent_bar(img, H - 3)
    return save(img, "08_github_site.png")


# ─────────────────────────────────────────────────────────────────────────────
# 00  Thumbnail  240×240
# ─────────────────────────────────────────────────────────────────────────────
def make_thumbnail():
    S = 240
    img = Image.new("RGB", (S, S), BG_PAGE)
    draw = ImageDraw.Draw(img)

    # Subtle radial glow
    overlay = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for radius in range(90, 0, -3):
        alpha = int(30 * (1 - radius / 90))
        od.ellipse((S//2-radius*2, S//2-radius, S//2+radius*2, S//2+radius),
                   fill=(124, 106, 247, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ContentForge logotype
    logo_text(draw, S // 2, 102, size=24)
    draw.line([(S//2 - 66, 116), (S//2 + 66, 116)], fill=BORDER, width=1)
    draw.text((S // 2, 132), "Content Scoring API",
              font=_font(13), fill=TEXT_SUB, anchor="mm")

    # Small badge
    badge_pill(draw, S // 2, 162,
               "28 endpoints",
               font=_font(12, bold=True), pad_x=10, pad_y=4)

    # Accent bar top/bottom
    for x in range(S):
        t = x / S
        r1, g1, b1 = hex_rgb(PURPLE); r2, g2, b2 = hex_rgb(TEAL)
        c = (int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t))
        draw.line([(x, 0), (x, 2)], fill=c)
        draw.line([(x, S-3), (x, S-1)], fill=c)

    p = OUT_DIR / "00_thumbnail_240x240.png"
    img.save(p, "PNG")
    print(f"  Saved -> {p}")
    return p


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\nGenerating ContentForge PH assets (website theme) -> {OUT_DIR}\n")
    steps = [
        ("01  Hero",           make_hero),
        ("02  How it works",   make_how_it_works),
        ("03  Platforms",      make_platforms),
        ("04  AI generators",  make_ai_endpoints),
        ("05  Quick start",    make_quickstart),
        ("06  Pricing",        make_pricing),
        ("07  Score demo",     make_score_demo),
        ("08  GitHub card",    make_github_card),
        ("00  Thumbnail",      make_thumbnail),
    ]
    ok = []
    for label, fn in steps:
        print(f"[{label}]")
        try:
            ok.append(fn())
        except Exception as e:
            print(f"  ERROR: {e}")
    print(f"\n Done! {len(ok)}/9  ->  {OUT_DIR}")
    print("  All 1270x760  |  Thumbnail 240x240  |  Under 2000px\n")
