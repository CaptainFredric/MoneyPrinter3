"""Writes the new gen_ph_gallery.py keeping the existing palette header."""
import pathlib, textwrap

ROOT   = pathlib.Path(__file__).parent
TARGET = ROOT / "gen_ph_gallery.py"

# Keep only first 45 lines (palette block)
with open(TARGET) as f:
    lines = f.readlines()
header = "".join(lines[:45])

new_body = textwrap.dedent("""\


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
        img = Image.new("RGB", (w, h), BG_DEEP)
        draw = ImageDraw.Draw(img)
        r1, g1, b1 = hex_rgb(BG_DEEP)
        r2, g2, b2 = hex_rgb(BG_MID)
        for y in range(h):
            t = y / h
            c = (int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t))
            draw.line([(0, y), (w, y)], fill=c)
        return img, ImageDraw.Draw(img)


    def rr(draw, xy, r=12, fill=None, outline=None, w=1):
        draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=w)


    def gold_bar(img, y, thickness=4):
        draw = ImageDraw.Draw(img)
        r1, g1, b1 = hex_rgb(GOLD2)
        r2, g2, b2 = hex_rgb(PURPLE)
        for x in range(W):
            t = x / W
            c = (int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t))
            draw.line([(x, y), (x, y+thickness)], fill=c)


    def sparkles(draw, cx, cy, n=8, inner=22, outer=50, dot_r=3, color=GOLD):
        for i in range(n):
            angle = math.radians(i * 360 / n)
            x1 = cx + inner * math.cos(angle)
            y1 = cy + inner * math.sin(angle)
            x2 = cx + outer * math.cos(angle)
            y2 = cy + outer * math.sin(angle)
            draw.line([(x1, y1), (x2, y2)], fill=color, width=2)
        for i in range(n):
            angle = math.radians(i * 360/n + 360/(n*2))
            dist = outer * 1.35
            xd = cx + dist * math.cos(angle)
            yd = cy + dist * math.sin(angle)
            draw.ellipse((xd-dot_r, yd-dot_r, xd+dot_r, yd+dot_r), fill=color)


    def gem(draw, cx, cy, size=28):
        pts = [(cx, cy-size), (cx+size*0.75, cy), (cx, cy+size*0.7), (cx-size*0.75, cy)]
        draw.polygon(pts, fill=GOLD)
        inn = [(cx, cy-size*0.45), (cx+size*0.4, cy), (cx, cy+size*0.3), (cx-size*0.4, cy)]
        draw.polygon(inn, fill=GOLD2)
        draw.polygon([(cx, cy-size*0.45), (cx+size*0.4, cy), (cx, cy)], fill=GOLD)


    def save(img, name):
        p = OUT_DIR / name
        img.save(p, "PNG", optimize=True)
        print(f"  Saved -> {p}")
        return p


    # ────────────────────────────────────────────────────────────────────────
    # 01 Hero
    # ────────────────────────────────────────────────────────────────────────
    def make_hero():
        img, draw = new_canvas()
        gold_bar(img, 0)
        cx, cy = W // 2, 198
        r_c = 112
        draw.ellipse((cx-r_c, cy-r_c, cx+r_c, cy+r_c), fill=PURPLE)
        sparkles(draw, cx, cy, n=10, inner=r_c+8, outer=r_c+46)
        gem(draw, cx, cy, size=40)
        draw.text((W//2, 358), "CONTENT", font=_font(72, bold=True), fill=WHITE,      anchor="mm")
        draw.text((W//2, 438), "FORGE",   font=_font(72, bold=True), fill=GOLD,       anchor="mm")
        draw.line([(W//2-165, 464), (W//2+165, 464)], fill=GOLD2, width=1)
        draw.text((W//2, 490), "AI-Powered Content Scoring & Generation API",
                  font=_font(22), fill=TEXT_SUB, anchor="mm")
        stats = [("28","Endpoints"),("16","Scorers"),("12","AI Tools"),("9+","Platforms")]
        cw = 240; tot = len(stats)*cw + (len(stats)-1)*20; sx = (W-tot)//2; sy = 528
        for i, (val, lbl) in enumerate(stats):
            cx2 = sx + i * (cw+20)
            rr(draw, (cx2, sy, cx2+cw, sy+112), r=14, fill=BG_CARD, outline=BORDER)
            draw.text((cx2+cw//2, sy+40), val, font=_font(46, bold=True), fill=GOLD,      anchor="mm")
            draw.text((cx2+cw//2, sy+84), lbl, font=_font(18),            fill=TEXT_BODY, anchor="mm")
        gold_bar(img, H-4)
        return save(img, "01_hero.png")


    # ────────────────────────────────────────────────────────────────────────
    # 02 How It Works
    # ────────────────────────────────────────────────────────────────────────
    def make_how_it_works():
        img, draw = new_canvas()
        gold_bar(img, 0)
        draw.text((W//2, 70),  "How ContentForge Works",
                  font=_font(50, bold=True), fill=WHITE, anchor="mm")
        draw.text((W//2, 118), "From raw content idea to optimised copy instantly",
                  font=_font(22), fill=TEXT_SUB, anchor="mm")
        steps = [
            ("1","POST your content",
             "Send text to any endpoint.\\nTweet, headline, caption,\\nLinkedIn post — anything."),
            ("2","Instant analysis",
             "Heuristic engine scores 20+\\nfactors in <50 ms — no\\nAI latency for scoring."),
            ("3","Actionable output",
             "Score, grade, platform tips,\\nand AI rewrite suggestions\\nall returned in JSON."),
        ]
        cw = 330; ch = 422; tot = len(steps)*cw+(len(steps)-1)*40; sx = (W-tot)//2; sy = 176
        for i, (num, head, body) in enumerate(steps):
            cx = sx + i*(cw+40)
            rr(draw, (cx, sy, cx+cw, sy+ch), r=16, fill=BG_CARD, outline=BORDER)
            for x in range(cx, cx+cw):
                t = (x-cx)/cw
                r1,g1,b1 = hex_rgb(GOLD2); r2,g2,b2 = hex_rgb(PURPLE)
                draw.line([(x,sy),(x,sy+5)],
                          fill=(int(r1+(r2-r1)*t),int(g1+(g2-g1)*t),int(b1+(b2-b1)*t)))
            ccx = cx+cw//2; ccy = sy+86; cr = 38
            draw.ellipse((ccx-cr,ccy-cr,ccx+cr,ccy+cr), fill=PURPLE)
            sparkles(draw, ccx, ccy, n=8, inner=cr+5, outer=cr+26, dot_r=2, color=GOLD)
            draw.text((ccx, ccy), num, font=_font(42, bold=True), fill=GOLD, anchor="mm")
            draw.text((cx+cw//2, sy+164), head, font=_font(24,bold=True), fill=WHITE,     anchor="mm")
            for j, line in enumerate(body.split("\\n")):
                draw.text((cx+cw//2, sy+210+j*30), line, font=_font(19), fill=TEXT_BODY, anchor="mm")
            if i < len(steps)-1:
                ax = cx+cw+20; ay = sy+ch//2
                draw.polygon([(ax-12,ay-14),(ax+12,ay),(ax-12,ay+14)], fill=BORDER)
        draw.text((W//2, 668), "Scorer latency: <50 ms  |  AI endpoints: ~1-3 s",
                  font=_font(19), fill=TEXT_DIM, anchor="mm")
        gold_bar(img, H-4)
        return save(img, "02_how_it_works.png")


    # ────────────────────────────────────────────────────────────────────────
    # 03 Platform Coverage
    # ────────────────────────────────────────────────────────────────────────
    def make_platforms():
        img, draw = new_canvas()
        gold_bar(img, 0)
        draw.text((W//2, 66), "16 Platform Scorers — One API",
                  font=_font(48, bold=True), fill=WHITE, anchor="mm")
        draw.text((W//2, 112), "Benchmark content against platform-specific best practices instantly",
                  font=_font(21), fill=TEXT_SUB, anchor="mm")
        platforms = [
            ("Twitter / X",   GOLD,      "Hook, CTA, hashtag density"),
            ("LinkedIn",      "#7C6AE8", "Professional tone, length"),
            ("Instagram",     "#D4628A", "Hook, emoji, hashtag count"),
            ("TikTok",        "#FF6B9D", "Trend language, hook speed"),
            ("YouTube Title", GOLD2,     "SEO, click-through, length"),
            ("YouTube Desc",  GOLD2,     "Keywords, CTA, chapters"),
            ("Pinterest",     "#C0548A", "Keyword richness, visual cues"),
            ("Threads",       PURPLE,    "Conversation starters"),
            ("Facebook",      "#6B8AE8", "Engagement triggers, tone"),
            ("Email Subject", GOLD,      "Open-rate signals, spam"),
            ("Ad Copy",       "#BDB6FF", "AIDA structure, urgency"),
            ("Readability",   TEXT_SUB,  "Flesch-Kincaid grade"),
            ("Headlines",     GOLD,      "Power words, numbers, SEO"),
            ("Hashtags",      "#8AE8D4", "Density, relevance"),
            ("Batch Score",   TEXT_DIM,  "All platforms at once"),
            ("Score Multi",   TEXT_DIM,  "Up to 100 texts/request"),
        ]
        cols = 4; pad = 8; cw = (W-80)//cols; ch = (H-190)//4
        for idx, (name, color, desc) in enumerate(platforms):
            col = idx % cols; row = idx // cols
            cx = 40+col*cw; cy = 156+row*ch
            rr(draw, (cx+pad,cy+pad,cx+cw-pad,cy+ch-pad), r=10, fill=BG_CARD, outline=BORDER)
            rr(draw, (cx+pad,cy+pad,cx+pad+4, cy+ch-pad), r=2,  fill=color)
            draw.text((cx+24, cy+ch//2-12), name,     font=_font(17,bold=True), fill=color,     anchor="lm")
            draw.text((cx+24, cy+ch//2+14), desc[:36],font=_font(14),           fill=TEXT_BODY, anchor="lm")
        gold_bar(img, H-4)
        return save(img, "03_platforms.png")


    # ────────────────────────────────────────────────────────────────────────
    # 04 AI Generators
    # ────────────────────────────────────────────────────────────────────────
    def make_ai_endpoints():
        img, draw = new_canvas()
        gold_bar(img, 0)
        draw.text((W//2, 66), "12 AI-Powered Generators",
                  font=_font(48, bold=True), fill=WHITE, anchor="mm")
        draw.text((W//2, 112), "Powered by Gemini — generate ready-to-post content in seconds",
                  font=_font(21), fill=TEXT_SUB, anchor="mm")
        generators = [
            ("Content Calendar",  "/content_calendar",      "7-day platform-tailored plan"),
            ("Hook Generator",    "/generate_hooks",         "5 attention-grabbing openings"),
            ("Thread Outline",    "/thread_outline",         "Numbered X thread structure"),
            ("Tweet Ideas",       "/tweet_ideas",            "5 angles from any topic"),
            ("LinkedIn Post",     "/generate_linkedin_post", "Full article with formatting"),
            ("Bio Generator",     "/generate_bio",           "Platform-optimised bio"),
            ("Caption Generator", "/generate_caption",       "Instagram/TikTok + hashtags"),
            ("Email Sequence",    "/generate_email_seq",     "3-email warm-up sequence"),
            ("Improve Headline",  "/improve_headline",       "AI headline power-up"),
            ("Rewrite",           "/rewrite",                "Adapt for any platform/tone"),
            ("Content Brief",     "/generate_content_brief", "Angle, hooks, CTA, keywords"),
            ("Batch Score",       "/batch_score",            "Score 100 items at once"),
        ]
        cols = 4; rows = 3; cw = (W-60)//cols; ch = (H-190)//rows
        acc = [GOLD, PURPLE, "#7C6AE8", "#BDB6FF", "#D4628A", GOLD2,
               TEXT_SUB, GOLD, PURPLE, "#7C6AE8", GOLD2, "#D4628A"]
        for idx, (name, ep, desc) in enumerate(generators):
            col = idx % cols; row = idx // cols
            cx = 30+col*cw; cy = 154+row*ch; ac = acc[idx]
            rr(draw, (cx+6,cy+6,cx+cw-6,cy+ch-6), r=12, fill=BG_CARD, outline=BORDER)
            for x in range(cx+6, cx+cw-6):
                t = (x-cx-6)/(cw-12)
                r1,g1,b1 = hex_rgb(GOLD2); r2,g2,b2 = hex_rgb(PURPLE)
                draw.line([(x,cy+6),(x,cy+10)],
                          fill=(int(r1+(r2-r1)*t),int(g1+(g2-g1)*t),int(b1+(b2-b1)*t)))
            draw.text((cx+cw//2, cy+34), name, font=_font(19,bold=True), fill=WHITE,     anchor="mm")
            draw.text((cx+cw//2, cy+56), ep,   font=_font(13),           fill=ac,        anchor="mm")
            draw.text((cx+cw//2, cy+82), desc, font=_font(15),           fill=TEXT_BODY, anchor="mm")
        gold_bar(img, H-4)
        return save(img, "04_ai_generators.png")


    # ────────────────────────────────────────────────────────────────────────
    # 05 Quick Start
    # ────────────────────────────────────────────────────────────────────────
    def make_quickstart():
        img, draw = new_canvas()
        gold_bar(img, 0)
        draw.text((W//2, 66),  "Get Started in Seconds",
                  font=_font(46, bold=True), fill=WHITE, anchor="mm")
        draw.text((W//2, 110), "No SDK required — one HTTP request",
                  font=_font(21), fill=TEXT_SUB, anchor="mm")
        lw = 560; lh = 440; ly = 155

        def panel(px, py, pw, lbl):
            rr(draw, (px,py,px+pw,py+lh), r=14, fill="#07052B", outline=BORDER)
            rr(draw, (px,py,px+pw,py+46), r=14, fill=BG_CARD2,  outline=BORDER)
            for ci, col in enumerate(["#FF5F57","#FEBC2E","#28C840"]):
                draw.ellipse((px+16+ci*22,py+14,px+28+ci*22,py+26), fill=col)
            draw.text((px+pw//2, py+23), lbl, font=_font(14), fill=TEXT_DIM, anchor="mm")

        panel(55, ly, lw, "Terminal")
        curl = [
            ("# Score a tweet instantly",                    TEXT_DIM),
            ("curl -X POST \\\\",                            "#BDB6FF"),
            ('  "https://contentforge1.p',                   "#8A85C8"),
            ('   .rapidapi.com/score_tweet" \\\\',           "#8A85C8"),
            ('-H "Content-Type: application/json" \\\\',     GOLD),
            ('-H "X-RapidAPI-Key: YOUR_KEY" \\\\',           GOLD),
            ("-d '{\"text\": \"Just shipped ContentForge",  "#BDB6FF"),
            ("  28 endpoints live.\"}'",                    "#BDB6FF"),
        ]
        ty = ly+60
        for line, col in curl:
            draw.text((75, ty), line, font=_font(17), fill=col, anchor="lm"); ty += 28

        rx = 55+lw+40
        panel(rx, ly, W-rx-55, "Response")
        resp = [
            ("{",                         TEXT_BODY),
            ('  "score": 82,',            GOLD),
            ('  "grade": "B+",',          GOLD),
            ('  "platform": "twitter",',  "#BDB6FF"),
            ('  "feedback": [',           TEXT_SUB),
            ('    "Strong hook",',        TEXT_BODY),
            ('    "CTA present",',        TEXT_BODY),
            ('    "Good emoji use"',      TEXT_BODY),
            ('  ],',                      TEXT_SUB),
            ('  "latency_ms": 12',        "#BDB6FF"),
            ("}",                         TEXT_BODY),
        ]
        ty = ly+60
        for line, col in resp:
            draw.text((rx+18, ty), line, font=_font(17), fill=col, anchor="lm"); ty += 28

        draw.text((W//2, 658), "Free tier  |  No credit card  |  300 requests/month",
                  font=_font(19), fill=TEXT_DIM, anchor="mm")
        gold_bar(img, H-4)
        return save(img, "05_quickstart.png")


    # ────────────────────────────────────────────────────────────────────────
    # 06 Pricing
    # ────────────────────────────────────────────────────────────────────────
    def make_pricing():
        img, draw = new_canvas()
        gold_bar(img, 0)
        draw.text((W//2, 66),  "Simple, Transparent Pricing",
                  font=_font(48,bold=True), fill=WHITE, anchor="mm")
        draw.text((W//2, 112), "Start free. Scale as you grow.",
                  font=_font(21), fill=TEXT_SUB, anchor="mm")
        tiers = [
            ("BASIC","$0", "/mo",TEXT_DIM,["300 req/month","50 AI calls","All 16 scorers","Community support"],    False),
            ("PRO",  "$9", "/mo",PURPLE,  ["1,000 req/month","750 AI calls","All 28 endpoints","Email support"],   False),
            ("ULTRA","$29","/mo",GOLD,    ["4,000 req/month","3,000 AI calls","Priority routing","Slack support"], True),
            ("MEGA", "$99","/mo",GOLD2,   ["20k req/month","18k AI calls","Dedicated support","SLA guarantee"],    False),
        ]
        cw = 268; tot = len(tiers)*cw+(len(tiers)-1)*20; sx = (W-tot)//2; ch = 472; sy = 146
        for i, (tier, price, unit, color, feats, pop) in enumerate(tiers):
            cx = sx+i*(cw+20)
            rr(draw,(cx,sy,cx+cw,sy+ch),r=16,
               fill=BG_CARD2 if pop else BG_CARD,
               outline=color if pop else BORDER, w=2 if pop else 1)
            for x in range(cx, cx+cw):
                t = (x-cx)/cw
                r1,g1,b1 = hex_rgb(GOLD2 if pop else BG_CARD)
                r2,g2,b2 = hex_rgb(PURPLE if pop else BG_CARD2)
                draw.line([(x,sy),(x,sy+5)],
                          fill=(int(r1+(r2-r1)*t),int(g1+(g2-g1)*t),int(b1+(b2-b1)*t)))
            if pop:
                bf = _font(14,bold=True); bt = "MOST POPULAR"
                bb2 = draw.textbbox((0,0),bt,font=bf); bw = bb2[2]-bb2[0]+24
                rr(draw,(cx+cw//2-bw//2,sy-18,cx+cw//2+bw//2,sy+2),r=9,fill=GOLD)
                draw.text((cx+cw//2,sy-8),bt,font=bf,fill=BG_DEEP,anchor="mm")
            draw.text((cx+cw//2,sy+44),  tier,  font=_font(26,bold=True),fill=color,     anchor="mm")
            draw.text((cx+cw//2,sy+108), price, font=_font(52,bold=True),fill=WHITE,     anchor="mm")
            draw.text((cx+cw//2,sy+150), unit,  font=_font(17),          fill=TEXT_BODY, anchor="mm")
            draw.line([(cx+22,sy+170),(cx+cw-22,sy+170)],fill=BORDER)
            for j, feat in enumerate(feats):
                draw.text((cx+28,sy+198+j*46),"+ "+feat,font=_font(17),
                          fill=WHITE if pop else TEXT_BODY, anchor="lm")
        draw.text((W//2,684),"10% off with code  PH10OFF  on Product Hunt",
                  font=_font(19),fill=GOLD,anchor="mm")
        gold_bar(img,H-4)
        return save(img,"06_pricing.png")


    # ────────────────────────────────────────────────────────────────────────
    # 07 Score Demo
    # ────────────────────────────────────────────────────────────────────────
    def make_score_demo():
        img, draw = new_canvas()
        gold_bar(img, 0)
        draw.text((W//2, 66), "Real Score Output — Live Demo",
                  font=_font(46,bold=True), fill=WHITE, anchor="mm")
        draw.text((W//2, 112),
                  'POST /score_tweet  |  "Just shipped ContentForge — 28 endpoints live."',
                  font=_font(18), fill=TEXT_SUB, anchor="mm")
        ccx = 195; ccy = 390; r = 106
        draw.ellipse((ccx-r-8,ccy-r-8,ccx+r+8,ccy+r+8), fill=PURPLE)
        draw.ellipse((ccx-r,  ccy-r,  ccx+r,  ccy+r),   fill=BG_CARD)
        sparkles(draw, ccx, ccy, n=8, inner=r+10, outer=r+46, dot_r=3, color=GOLD)
        draw.text((ccx,ccy-18),"82",        font=_font(64,bold=True), fill=GOLD,     anchor="mm")
        draw.text((ccx,ccy+40),"B+  Score", font=_font(22,bold=True), fill=TEXT_SUB, anchor="mm")
        plat = [("Twitter/X",82,GOLD),("LinkedIn",67,PURPLE),("Instagram",75,"#D4628A"),("TikTok",70,"#FF6B9D")]
        bx = 352; by = 146; bw = 180; bh = 56
        for j, (pname, score, col) in enumerate(plat):
            bx2 = bx+j*(bw+20)
            rr(draw,(bx2,by,bx2+bw,by+bh),r=10,fill=BG_CARD,outline=col)
            draw.text((bx2+bw//2,by+16),pname,     font=_font(15),           fill=col,   anchor="mm")
            draw.text((bx2+bw//2,by+40),str(score),font=_font(22,bold=True), fill=WHITE, anchor="mm")
        feedback = [
            (GOLD,     "Strong opening hook — first 10 chars create curiosity"),
            (GOLD,     "CTA detected — actionable language present"),
            (GOLD,     "Emoji enhances engagement without cluttering"),
            (TEXT_SUB, "Hashtag count: 0 — consider 1-2 relevant tags"),
            (TEXT_SUB, "Length: 55 chars — expand to 120+ for more context"),
            ("#FF6B6B","No question/reply bait — add one to boost replies"),
        ]
        fy = 230
        for col, text in feedback:
            rr(draw,(348,fy,W-48,fy+36),r=6,fill=BG_CARD,outline=BORDER)
            draw.text((366,fy+18),text,font=_font(17),fill=col,anchor="lm"); fy += 46
        draw.text((W//2,700),"Latency: 12 ms  |  No AI required for instant scoring",
                  font=_font(17),fill=TEXT_DIM,anchor="mm")
        gold_bar(img,H-4)
        return save(img,"07_score_demo.png")


    # ────────────────────────────────────────────────────────────────────────
    # 08 GitHub Pages Card
    # ────────────────────────────────────────────────────────────────────────
    def make_github_card():
        import urllib.request, ssl, re, html as html_mod
        site = {
            "title":    "ContentForge",
            "subtitle": "28-endpoint REST API for creators & marketers",
            "url":      "captainfredric.github.io/ContentForge",
            "live":     False,
            "features": [],
        }
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(
                "https://captainfredric.github.io/ContentForge/",
                headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8, context=ctx) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            site["live"] = True
            headings = re.findall(r'<h[123][^>]*>(.*?)</h[123]>', raw, re.I|re.S)
            clean = [html_mod.unescape(re.sub(r'<[^>]+>','',h)).strip() for h in headings]
            site["features"] = [c for c in clean if c and len(c)>3][:6]
            m = re.search(r'<title>(.*?)</title>', raw, re.I)
            if m:
                t = html_mod.unescape(re.sub(r'<[^>]+>','',m.group(1)).strip())
                for sep in [' — ',' | ',' - ']:
                    if sep in t: t = t.split(sep)[0].strip(); break
                site["title"] = t[:36]
        except Exception as e:
            print(f"  [fetch] {e}")
        img, draw = new_canvas()
        gold_bar(img, 0)
        rr(draw,(55,118,W-55,H-50), r=16, fill="#07052B", outline=BORDER)
        rr(draw,(55,118,W-55,166),  r=16, fill=BG_CARD2,  outline=BORDER)
        for ci, col in enumerate(["#FF5F57","#FEBC2E","#28C840"]):
            draw.ellipse((76+ci*24,132,90+ci*24,146),fill=col)
        rr(draw,(200,130,W-200,156),r=10,fill=BG_DEEP,outline=BORDER)
        draw.text(((200+W-200)//2,143),"  "+site["url"],font=_font(18),fill=GOLD,anchor="mm")
        py = 222
        draw.text((W//2,py),    site["title"],         font=_font(44,bold=True),fill=WHITE,    anchor="mm")
        draw.text((W//2,py+55), site["subtitle"][:72], font=_font(22),          fill=TEXT_SUB, anchor="mm")
        badge_col = GOLD if site["live"] else "#FF6B6B"
        badge_txt = "LIVE" if site["live"] else "OFFLINE"
        bf = _font(15,bold=True)
        bb = draw.textbbox((0,0),badge_txt,font=bf); bw = bb[2]-bb[0]+28
        rr(draw,(W//2-bw//2,py+88,W//2+bw//2,py+116),r=12,fill=badge_col)
        draw.text((W//2,py+102),badge_txt,font=bf,fill=BG_DEEP,anchor="mm")
        if not site["features"]:
            site["features"] = ["28 REST endpoints","16 instant scorers","12 AI generators",
                                 "Zero-latency scoring","Free tier included","RapidAPI marketplace"]
        for i, feat in enumerate(site["features"][:6]):
            co = i%2; ro = i//2; fx = 165+co*460; fy = py+158+ro*48
            draw.text((fx,fy),"->  "+feat[:50],font=_font(18),fill=GOLD,anchor="lm")
        draw.text((W//2,H-70),"Evaluated live from captainfredric.github.io/ContentForge",
                  font=_font(16),fill=TEXT_DIM,anchor="mm")
        gold_bar(img,H-4)
        return save(img,"08_github_site.png")


    # ────────────────────────────────────────────────────────────────────────
    # 00 Thumbnail 240x240
    # ────────────────────────────────────────────────────────────────────────
    def make_thumbnail():
        S = 240
        img  = Image.new("RGB",(S,S),BG_DEEP)
        draw = ImageDraw.Draw(img)
        r1,g1,b1 = hex_rgb(BG_DEEP); r2,g2,b2 = hex_rgb(BG_MID)
        for y in range(S):
            t = y/S
            draw.line([(0,y),(S,y)],fill=(int(r1+(r2-r1)*t),int(g1+(g2-g1)*t),int(b1+(b2-b1)*t)))
        cx = S//2; cy = 85; r = 50
        draw.ellipse((cx-r,cy-r,cx+r,cy+r),fill=PURPLE)
        sparkles(draw,cx,cy,n=8,inner=r+5,outer=r+24,dot_r=2,color=GOLD)
        gem(draw,cx,cy,size=20)
        draw.text((cx,150),"CONTENT",font=_font(22,bold=True),fill=WHITE,    anchor="mm")
        draw.text((cx,176),"FORGE",  font=_font(22,bold=True),fill=GOLD,     anchor="mm")
        draw.line([(cx-54,188),(cx+54,188)],fill=GOLD2,width=1)
        draw.text((cx,204),"AI Content API",font=_font(11),fill=TEXT_BODY,anchor="mm")
        p = OUT_DIR/"00_thumbnail_240x240.png"; img.save(p,"PNG")
        print(f"  Saved -> {p}"); return p


    # ────────────────────────────────────────────────────────────────────────
    if __name__ == "__main__":
        print(f"\\nGenerating ContentForge PH assets (logo theme) -> {OUT_DIR}\\n")
        steps = [
            ("01  Hero",          make_hero),
            ("02  How it works",  make_how_it_works),
            ("03  Platforms",     make_platforms),
            ("04  AI generators", make_ai_endpoints),
            ("05  Quick start",   make_quickstart),
            ("06  Pricing",       make_pricing),
            ("07  Score demo",    make_score_demo),
            ("08  GitHub card",   make_github_card),
            ("00  Thumbnail",     make_thumbnail),
        ]
        ok = []
        for label, fn in steps:
            print(f"[{label}]")
            try: ok.append(fn())
            except Exception as e: print(f"  ERROR: {e}")
        print(f"\\n Done! {len(ok)}/9  ->  {OUT_DIR}")
        print("  All 1270x760  |  Thumbnail 240x240  |  Under 2000px\\n")
    """)

# dedent strips 4 spaces from the raw string above
new_body = "\n".join(line[4:] if line.startswith("    ") else line
                     for line in new_body.splitlines()) + "\n"

with open(TARGET, "w") as f:
    f.write(header + new_body)

line_count = (header + new_body).count("\n")
print(f"Written! ~{line_count} lines → {TARGET}")
