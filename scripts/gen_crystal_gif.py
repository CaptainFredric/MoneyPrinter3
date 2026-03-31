"""
Generate an animated GIF of the ContentForge crystal logo.
- Crystal floats up and down in a smooth loop
- Sparkle rays / dashes constantly emanate outward from the crystal
- Website palette: dark #0f0f11, purple #7c6af7, teal #5ec8a0
- Output: ~/Desktop/ContentForge-PH-Assets/00_thumbnail_240x240.gif
"""
import math
import os
import pathlib

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = pathlib.Path.home() / "Desktop" / "ContentForge-PH-Assets"
OUT_DIR.mkdir(parents=True, exist_ok=True)

S = 240  # canvas size

# ── Website palette ───────────────────────────────────────────────────────────
BG_PAGE = "#0f0f11"
PURPLE  = "#7c6af7"
TEAL    = "#5ec8a0"
WHITE   = "#f0f0f5"
TEXT_SUB = "#9999aa"
BORDER  = "#2e2e40"


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold
        else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def accent_bar_s(draw, y, thickness=3):
    """Purple-to-teal gradient bar at given y."""
    r1, g1, b1 = hex_rgb(PURPLE)
    r2, g2, b2 = hex_rgb(TEAL)
    for x in range(S):
        t = x / S
        c = (int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t))
        draw.line([(x, y), (x, y + thickness)], fill=c)


def render_frame(frame_idx, total_frames):
    """Render a single frame of the animation.

    frame_idx: 0 .. total_frames-1
    Returns an RGBA Image.
    """
    # Phase: 0 → 2π over the loop
    phase = (frame_idx / total_frames) * 2 * math.pi

    # Float offset: sinusoidal bob, ±6 px
    bob = math.sin(phase) * 6.0

    img = Image.new("RGB", (S, S), BG_PAGE)

    # Soft radial purple glow (centred on crystal rest position, shifts with bob)
    overlay = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    glow_cy = 82 + bob
    for radius in range(100, 0, -3):
        alpha = int(32 * (1 - radius / 100))
        od.ellipse(
            (S // 2 - radius, glow_cy - radius // 2,
             S // 2 + radius, glow_cy + radius * 1.4),
            fill=(124, 106, 247, alpha),
        )
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    cx = S // 2
    cy = 82 + bob  # floating center
    r = 62

    # Main purple circle (logo background)
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=PURPLE)

    # ── Emanating rays / dashes ──────────────────────────────────────────
    # Two concentric rings of animated dashes that rotate and pulse outward.
    # Ring 1: 10 long spokes (teal, rotating clockwise)
    # Ring 2: 10 shorter dashes (teal dim, rotating counter-clockwise)
    # Plus pulsing dots between spokes.

    # Rotation speed: spokes rotate slowly over the loop
    spoke_rot = phase * 0.5  # radians per loop
    dash_rot  = -phase * 0.8  # counter-rotate

    # Pulse: inner/outer radius of dashes oscillate
    pulse = 0.5 + 0.5 * math.sin(phase * 2)  # 0..1

    # Ring 1: 10 main spokes
    num_spokes = 10
    for i in range(num_spokes):
        angle = math.radians(i * 360 / num_spokes) + spoke_rot
        # Inner start: on the circle edge
        inner_r = r - 6
        # Outer end: past the circle, pulsing
        outer_base = r + 18
        outer_extent = r + 26 + pulse * 10  # 26-36 px past center
        x1 = cx + inner_r * math.cos(angle)
        y1 = cy + inner_r * math.sin(angle)
        x2 = cx + outer_extent * math.cos(angle)
        y2 = cy + outer_extent * math.sin(angle)
        # Fade alpha by pulse
        alpha_f = 0.6 + 0.4 * math.sin(phase * 2 + i * 0.6)
        col_r, col_g, col_b = hex_rgb(TEAL)
        spoke_color = (int(col_r * alpha_f), int(col_g * alpha_f), int(col_b * alpha_f))
        draw.line([(x1, y1), (x2, y2)], fill=spoke_color, width=2)

    # Ring 2: 10 shorter outer dashes (between spokes)
    for i in range(num_spokes):
        angle = math.radians(i * 360 / num_spokes + 18) + dash_rot
        # Short dash segment starting outside circle
        d_inner = r + 24 + pulse * 6
        d_outer = r + 34 + pulse * 8
        x1 = cx + d_inner * math.cos(angle)
        y1 = cy + d_inner * math.sin(angle)
        x2 = cx + d_outer * math.cos(angle)
        y2 = cy + d_outer * math.sin(angle)
        alpha_f = 0.4 + 0.6 * math.sin(phase * 3 + i * 0.8)
        col_r, col_g, col_b = hex_rgb(TEAL)
        dash_color = (int(col_r * alpha_f), int(col_g * alpha_f), int(col_b * alpha_f))
        draw.line([(x1, y1), (x2, y2)], fill=dash_color, width=2)

    # Dot tips: orbiting between spokes
    for i in range(num_spokes):
        angle = math.radians(i * 360 / num_spokes + 9) + spoke_rot * 0.3
        dist = r + 30 + pulse * 6
        xd = cx + dist * math.cos(angle)
        yd = cy + dist * math.sin(angle)
        dot_alpha = 0.5 + 0.5 * math.sin(phase * 2.5 + i * 1.2)
        col_r, col_g, col_b = hex_rgb(TEAL)
        dot_col = (int(col_r * dot_alpha), int(col_g * dot_alpha), int(col_b * dot_alpha))
        dot_r = 2 + pulse * 1.5
        draw.ellipse((xd - dot_r, yd - dot_r, xd + dot_r, yd + dot_r), fill=dot_col)

    # Ring 3: tiny twinkling particles at far distance
    num_particles = 16
    for i in range(num_particles):
        angle = math.radians(i * 360 / num_particles + 5) + phase * 0.2
        dist = r + 42 + math.sin(phase * 1.5 + i * 2.0) * 8
        xp = cx + dist * math.cos(angle)
        yp = cy + dist * math.sin(angle)
        # Only draw some particles (twinkle effect)
        twinkle = math.sin(phase * 4 + i * 1.7)
        if twinkle > 0.1:
            t_alpha = min(1.0, twinkle)
            col_r, col_g, col_b = hex_rgb(TEAL)
            p_col = (int(col_r * t_alpha * 0.6), int(col_g * t_alpha * 0.6), int(col_b * t_alpha * 0.6))
            draw.ellipse((xp - 1, yp - 1, xp + 1, yp + 1), fill=p_col)

    # ── Prism / diamond cube ─────────────────────────────────────────────
    gs = 26  # gem size
    top   = (cx, cy - gs)
    right = (cx + int(gs * 0.82), cy - 2)
    bot   = (cx, cy + int(gs * 0.72))
    left  = (cx - int(gs * 0.82), cy - 2)
    mid   = (cx, cy - 4)

    # Main teal body
    draw.polygon([top, right, bot, left], fill=TEAL)
    # Upper-right highlight (shifts brightness slightly with phase for shimmer)
    shimmer = 0.85 + 0.15 * math.sin(phase * 3)
    ur_base = (158, 252, 224)  # #9efce0
    ur_col = tuple(int(c * shimmer) for c in ur_base)
    draw.polygon([top, right, mid], fill=ur_col)
    # Lower-right shadow
    draw.polygon([mid, right, bot], fill="#3d9c7a")
    # Lower-left darkest
    draw.polygon([mid, bot, left], fill="#2d7a5e")
    # Upper-left mid
    ul_base = (94, 200, 160)  # #5ec8a0
    ul_shimmer = 0.9 + 0.1 * math.sin(phase * 3 + 1.5)
    ul_col = tuple(int(c * ul_shimmer) for c in ul_base)
    draw.polygon([top, mid, left], fill=ul_col)

    # ── Text (stays fixed, doesn't float) ────────────────────────────────
    text_cy = 82 + r + 14  # fixed position
    draw.text((S // 2, text_cy), "CONTENT", font=_font(17, bold=True),
              fill="#f0f0f5", anchor="mm")
    draw.text((S // 2, text_cy + 19), "FORGE", font=_font(17, bold=True),
              fill=PURPLE, anchor="mm")
    draw.line([(S // 2 - 46, text_cy + 29), (S // 2 + 46, text_cy + 29)],
              fill=BORDER, width=1)
    draw.text((S // 2, text_cy + 40), "AI Content API", font=_font(10),
              fill=TEXT_SUB, anchor="mm")

    # Accent bars (fixed)
    accent_bar_s(draw, 0)
    accent_bar_s(draw, S - 3)

    return img


def main():
    total_frames = 48  # smooth loop at ~24fps → 2 seconds
    duration_ms = 42   # ~24 fps per frame

    print(f"Generating {total_frames}-frame crystal GIF...")
    frames = []
    for f in range(total_frames):
        frame = render_frame(f, total_frames)
        frames.append(frame)
        if (f + 1) % 12 == 0:
            print(f"  Frame {f+1}/{total_frames}")

    out_path = OUT_DIR / "00_thumbnail_240x240.gif"
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,  # infinite loop
        optimize=True,
    )
    # File size check
    size_kb = out_path.stat().st_size / 1024
    print(f"\n  Saved -> {out_path}")
    print(f"  {total_frames} frames · {duration_ms}ms/frame · {size_kb:.0f} KB")
    if size_kb > 2048:
        print(f"  ⚠ File is {size_kb:.0f} KB — PH max is 2 MB. May need fewer frames or colors.")
    else:
        print(f"  ✓ Under 2 MB PH limit")


if __name__ == "__main__":
    main()
