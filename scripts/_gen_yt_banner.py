#!/usr/bin/env python3
"""YouTube banner — ContentForge crystal, seamlessly looping GIF.

Design goals (user spec):
  - Crystal: 180°-symmetric diamond, FULL SIZE from frame 0, smooth continuous spin
  - Crystal spins 180° per GIF cycle — at 180° it looks identical to 0°, so the
    loop is invisible
  - Every element fully visible from frame 0 to last frame, same opacity throughout
  - No appearing / disappearing / fading
  - Only things that move: crystal spin, orbiters, scan line, halo pulse
  - All periodic animations use period = FRAMES so the GIF loops perfectly

Outputs: assets/yt_banner_2560x1440.gif + assets/yt_banner_2560x1440.png
"""

import math, random, os
from PIL import Image, ImageDraw, ImageFont

# ─── Canvas & Timing ───
W, H   = 2560, 1440
FRAMES = 60
DELAY  = 75          # ms per frame → 4.5-second loop

# ─── Palette ───
BG        = (15, 15, 17)
PURPLE    = (124, 106, 247)
TEAL      = (94,  200, 160)
WHITE     = (255, 255, 255)
DIM_P     = (50,  42,  100)
NAVY      = (22,  28,   52)
DARK_CARD = (22,  22,   28)
CARD_EDGE = (60,  55,  110)

FONT_PATH = os.path.join(os.path.dirname(__file__), "..", "fonts", "bold_font.ttf")

def font(sz):
    try:    return ImageFont.truetype(FONT_PATH, sz)
    except: return ImageFont.load_default()

def ac(base, a):
    """Return color tuple with clamped alpha."""
    return (*base[:3], max(0, min(255, int(a))))

def lerp(a, b, t):
    return tuple(int(a[i]*(1-t) + b[i]*t) for i in range(3))

def rot2d(px, py, cx, cy, angle):
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    dx, dy = px - cx, py - cy
    return (cx + dx*cos_a - dy*sin_a, cy + dx*sin_a + dy*cos_a)

def lsin(f, cycles=1, phase=0.0):
    """sin that completes exactly `cycles` full cycles over FRAMES → perfect loop."""
    return math.sin(2 * math.pi * cycles * f / FRAMES + phase)

# ─────────────────────────────────────────────────────
#  PRE-COMPUTE STATIC SCENE ELEMENTS
# ─────────────────────────────────────────────────────

# Constellation network (completely static)
random.seed(77)
NODES = [(random.randint(80, W-80), random.randint(80, H-80)) for _ in range(80)]
EDGES = []
for i, (x1, y1) in enumerate(NODES):
    nearby = sorted(range(len(NODES)),
                    key=lambda j: math.hypot(x1-NODES[j][0], y1-NODES[j][1]))
    for j in nearby[1:3]:
        dist = math.hypot(x1-NODES[j][0], y1-NODES[j][1])
        if (j, i) not in EDGES and dist < 350:
            EDGES.append((i, j))

# Hex grid (pre-compute polygon point lists)
def make_hex_grid():
    hex_r = 50
    dx = hex_r * 1.75
    dy = hex_r * 1.52
    polys = []
    for row in range(int(H / dy) + 2):
        for col in range(int(W / dx) + 2):
            hx = col * dx + (dy * 0.5 if row % 2 else 0)
            hy = row * dy
            pts = [(hx + hex_r * math.cos(math.pi/6 + k*math.pi/3),
                    hy + hex_r * math.sin(math.pi/6 + k*math.pi/3))
                   for k in range(6)]
            polys.append(pts)
    return polys

HEX_POLYS = make_hex_grid()

# Floating code panels (static: fixed positions, never move)
CODE_SNIPPETS = [
    ['POST /score_twitter',   '{"text": "just shipped it"}',   '→ {"score": 82}'],
    ['GET  /readability',     '{"text": "complex sentence"}',  '→ {"grade_level": 9}'],
    ['POST /generate_hooks',  '{"topic": "AI tools"}',         '→ ["Stop guessing..."]'],
    ['POST /score_linkedin',  '{"text": "excited to share"}',  '→ {"score": 45}'],
]
random.seed(88)
PANEL_POS = [
    (110, 240),
    (90,  820),
    (W - 530, 280),
    (W - 510, 860),
]

# Orbiting particles — speeds are exact multiples of 2π/FRAMES → perfect loop
random.seed(42)
_ORBS = []
for i in range(28):
    base = (2 * math.pi / 28) * i
    k    = random.choice([-2, -1, 1, 1, 1, 2])   # integer orbits per GIF loop
    spd  = k * 2 * math.pi / FRAMES               # loop-safe speed
    rad  = random.uniform(138, 192)
    sz   = random.randint(2, 5)
    teal = random.random() > 0.4
    _ORBS.append((base, spd, rad, sz, teal))
ORBITERS = _ORBS

# Crystal position  (shifted 160 px left — centres group in YT safe zone)
CX = W // 2 - 470
CY = H // 2 + 8

# Crystal spin: π per GIF cycle.  At f=0 and f=FRAMES the diamond looks IDENTICAL
# because the shape has 180° rotational symmetry (NE↔SW same color, SE↔NW same color).
SPIN_INC = math.pi / FRAMES

# Crystal geometry constants
S     = 1.6            # scale (constant — never changes)
C_H   = 58 * S        # half-height of diamond
C_W   = 40 * S        # half-width of diamond

# Facet colours — 180° symmetric: NE==SW==BRIGHT, SE==NW==DARK
BRIGHT_TEAL = (100, 225, 174)
DARK_TEAL   = (38,  118,  88)
EDGE_COL    = (18,   52,  40)

# ─────────────────────────────────────────────────────
#  DRAW FUNCTIONS
# ─────────────────────────────────────────────────────

def draw_crystal(d, f):
    spin  = f * SPIN_INC
    scale = S   # keep the global scale value before local names shadow nothing

    # 5 points: Np, Ep, Sp, Wp (diamond tips) + center (never rotates)
    def R(px, py):
        return rot2d(CX + px, CY + py, CX, CY, spin)

    Np = R(0,    -C_H)
    Ep = R(C_W,   0)
    Sp = R(0,     C_H)
    Wp = R(-C_W,  0)
    Cp = (CX, CY)

    # 4 triangular facets (alternating bright/dark — gives 180° symmetry)
    d.polygon([Np, Ep, Cp], fill=BRIGHT_TEAL)   # NE
    d.polygon([Ep, Sp, Cp], fill=DARK_TEAL)     # SE
    d.polygon([Sp, Wp, Cp], fill=BRIGHT_TEAL)   # SW  (180° = NE)
    d.polygon([Wp, Np, Cp], fill=DARK_TEAL)     # NW  (180° = SE)

    # Divider lines & outer edge
    lw = max(1, int(1.8 * scale))
    d.polygon([Np, Ep, Sp, Wp], outline=EDGE_COL, width=lw)
    d.line([Np, Sp], fill=EDGE_COL, width=lw)
    d.line([Ep, Wp], fill=EDGE_COL, width=lw)

    # 4 tip sparkles — brightness based on how close each tip is to the top of screen
    for tip in [Np, Ep, Sp, Wp]:
        tx, ty = tip
        closeness = max(0, (CY - ty) / C_H)  # 1 when pointing straight up, 0 when down
        if closeness > 0.05:
            sz = int(6 * S * closeness)
            d.ellipse([tx-sz, ty-sz, tx+sz, ty+sz],
                      fill=ac(WHITE, int(200 * closeness)))


def draw_halo_and_beams(d, f):
    spin = f * SPIN_INC
    pulse = 0.72 + 0.28 * lsin(f, cycles=1, phase=math.pi / 5)

    # 12 radial beams — rotate with crystal, brightness pulses twice per loop
    for b in range(12):
        angle    = (2 * math.pi / 12) * b + spin
        inner_r  = 96 * S
        outer_r  = (148 + 18 * lsin(f, cycles=2, phase=b * 0.52)) * S
        x1 = CX + inner_r * math.cos(angle)
        y1 = CY + inner_r * math.sin(angle)
        x2 = CX + outer_r * math.cos(angle)
        y2 = CY + outer_r * math.sin(angle)
        ba = int((78 + 52 * lsin(f, cycles=2, phase=b * 0.6)) * pulse)
        d.line([(x1, y1), (x2, y2)], fill=ac(TEAL, ba), width=max(1, int(2.5*S)))
        ts = int(3.5 * S)
        d.ellipse([x2-ts, y2-ts, x2+ts, y2+ts], fill=ac(TEAL, min(255, ba + 45)))

    # Layered purple halo (radial gradient via concentric circles)
    max_r = int(110 * S)
    for r in range(max_r, 0, -2):
        frac = r / max_r
        glow_a = int(88 * (1 - frac) * pulse)
        d.ellipse([CX-r, CY-r, CX+r, CY+r], fill=ac(PURPLE, glow_a))

    # Inner dark fill
    ir = int(73 * S)
    d.ellipse([CX-ir, CY-ir, CX+ir, CY+ir], fill=ac(NAVY, 228))


# ─────────────────────────────────────────────────────
#  FRAME GENERATOR
# ─────────────────────────────────────────────────────
TITLE   = "DAN DeBUGGER"
TAGLINE = "builds things  ·  debugs stuff  ·  sometimes extra fries"
STATS   = "28 ENDPOINTS  ·  16 SCORERS  ·  12 AI TOOLS  ·  9+ PLATFORMS"

_title_f = None
_tag_f   = None
_stats_f = None
_code_f  = None
_wm_f    = None

def get_fonts():
    global _title_f, _tag_f, _stats_f, _code_f, _wm_f
    if _title_f is None:
        _title_f = font(130)
        _tag_f   = font(40)
        _stats_f = font(28)
        _code_f  = font(18)
        _wm_f    = font(22)

def gen_frame(f):
    get_fonts()
    img = Image.new("RGBA", (W, H), BG + (255,))
    d   = ImageDraw.Draw(img, "RGBA")

    # ── 1. Static hex grid ──
    for pts in HEX_POLYS:
        d.polygon(pts, outline=ac(DIM_P, 16))

    # ── 2. Static constellation ──
    for (i, j) in EDGES:
        x1, y1 = NODES[i]
        x2, y2 = NODES[j]
        d.line([(x1,y1),(x2,y2)], fill=ac(DIM_P, 22), width=1)
    for (nx, ny) in NODES:
        d.ellipse([nx-2, ny-2, nx+2, ny+2], fill=ac(PURPLE, 32))

    # ── 3. Static code panels ──
    for idx, (px, py) in enumerate(PANEL_POS):
        pw, ph = 345, 90
        d.rounded_rectangle(
            [px, py, px+pw, py+ph], radius=8,
            fill=ac(DARK_CARD, 145), outline=ac(CARD_EDGE, 80), width=1
        )
        for li, line in enumerate(CODE_SNIPPETS[idx]):
            lc = TEAL if line.startswith("→") else (180, 175, 220)
            d.text((px+14, py+10+li*24), line, fill=ac(lc, 215), font=_code_f)

    # ── 4. Halo + rotating beams ──
    draw_halo_and_beams(d, f)

    # ── 5. Orbiting particles ──
    for (base, spd, rad, sz, is_teal) in ORBITERS:
        angle = base + f * spd
        ox = CX + rad * math.cos(angle)
        oy = CY + rad * math.sin(angle)
        oc = TEAL if is_teal else PURPLE
        d.ellipse([ox-sz, oy-sz, ox+sz, oy+sz], fill=ac(oc, 185))

    # ── 6. Crystal (on top of halo) ──
    draw_crystal(d, f)

    # ── 7. Static title + subtle pulsing glow ──
    tx, ty = W // 2 - 215, H // 2 - 112
    glow_a = int(18 + 8 * lsin(f, cycles=1))
    for gdx in range(-6, 7, 3):
        for gdy in range(-6, 7, 3):
            d.text((tx+gdx, ty+gdy), TITLE, fill=ac(PURPLE, glow_a), font=_title_f)
    d.text((tx, ty), TITLE, fill=WHITE, font=_title_f)

    # ── 8. Static tagline ──
    d.text((tx + 12, ty + 158), TAGLINE, fill=TEAL, font=_tag_f)

    # ── 9. Static stats bar — kept within all-devices safe zone (y ≤ 889) ──
    st_y = H // 2 + 130   # = 850, box spans y=841–889
    d.rounded_rectangle(
        [W//2 - 615, st_y - 9, W//2 + 445, st_y + 39],
        radius=6, fill=ac(DARK_CARD, 122), outline=ac(CARD_EDGE, 52), width=1
    )
    d.text((W//2 - 594, st_y), STATS, fill=ac(PURPLE, 200), font=_stats_f)

    # ── 10. Scan line — single sweep, off-screen at loop boundary ──
    # At f=0:  scan_y ≈ -200  (above screen, invisible)
    # At f=59: scan_y ≈ 1613  (below screen, invisible) → gap is off-screen ✓
    scan_y = int(f * (H + 400) / FRAMES) - 200
    for dy in range(-14, 15):
        yy = scan_y + dy
        if 0 <= yy < H:
            sa = int(26 * (1 - abs(dy) / 14))
            d.line([(0, yy), (W, yy)], fill=ac(PURPLE, sa))

    # ── 11. Static gradient accent bar — just below stats, within desktop safe zone ──
    bar_y, bar_h, bar_x, bar_w = H // 2 + 178, 4, W//2 - 615, 1060
    for bx in range(bar_w):
        c = lerp(PURPLE, TEAL, bx / bar_w)
        d.line([(bar_x+bx, bar_y), (bar_x+bx, bar_y+bar_h)], fill=ac(c, 200))

    # ── 12. Static HUD corner brackets ──
    cl, lw, cc = 72, 3, TEAL
    corners = [(40, 40, 1, 1), (W-40, 40, -1, 1), (40, H-40, 1, -1), (W-40, H-40, -1, -1)]
    for (bx, by, xs, ys) in corners:
        d.line([(bx, by), (bx + xs*cl, by)], fill=cc, width=lw)
        d.line([(bx, by), (bx, by + ys*cl)], fill=cc, width=lw)

    # ── 13. Static URL watermark — right-aligned inside stats box row ──
    d.text((W//2 + 220, H // 2 + 132), "captainfredric.github.io/ContentForge",
           fill=ac((140, 135, 180), 130), font=_wm_f)

    return img.convert("RGB")


# ─────────────────────────────────────────────────────
#  RENDER
# ─────────────────────────────────────────────────────
def main():
    out_dir  = os.path.join(os.path.dirname(__file__), "..", "assets")
    os.makedirs(out_dir, exist_ok=True)
    gif_path = os.path.join(out_dir, "yt_banner_2560x1440.gif")
    png_path = os.path.join(out_dir, "yt_banner_2560x1440.png")

    print(f"Rendering {FRAMES} frames at {W}×{H} …")
    frames = []
    for i in range(FRAMES):
        if i % 10 == 0: print(f"  {i+1}/{FRAMES}")
        frames.append(gen_frame(i))

    # Static PNG = last frame (for YouTube banner upload)
    frames[-1].save(png_path, "PNG", optimize=True)
    print(f"PNG  → {png_path}  ({os.path.getsize(png_path)//1024} KB)")

    # Animated GIF
    frames[0].save(gif_path, save_all=True, append_images=frames[1:],
                   duration=DELAY, loop=0, optimize=True)
    print(f"GIF  → {gif_path}  ({os.path.getsize(gif_path)//1024} KB,  "
          f"{FRAMES} frames @ {DELAY} ms)")


if __name__ == "__main__":
    main()
