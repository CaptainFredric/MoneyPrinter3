#!/usr/bin/env python3
"""Update Twitter bot topics to feed the ContentForge content marketing funnel."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
path = ROOT / ".mp" / "twitter.json"

d = json.loads(path.read_text())

TOPICS = {
    "niche_launch_1": (
        "content creation tips, copywriting psychology, headline writing, "
        "viral hooks, and why some posts get 10x more engagement than others. "
        "Mix formats: specific tips backed by data or numbers, hot takes on content strategy, "
        "short threads that teach one concrete skill per post. "
        "Occasionally mention ContentForge API as a free tool for scoring and improving headlines. "
        "Voice: sharp, knowledgeable, slightly contrarian. No generic motivational fluff."
    ),
    "EyeCatcher": (
        "psychology of attention and visual storytelling — why certain things stop the scroll, "
        "pattern interrupts in marketing, the science of color and emotion in content. "
        "Mix: surprising facts about human perception, breakdowns of why specific viral posts worked, "
        "questions that provoke genuine replies. "
        "Voice: curious, observational, the kind of account that makes people stop mid-scroll."
    ),
}

for acc in d.get("accounts", []):
    nick = acc.get("nickname")
    if nick in TOPICS:
        acc["topic"] = TOPICS[nick]
        print(f"  {nick}: updated")

path.write_text(json.dumps(d, indent=4))
print("Done.")
