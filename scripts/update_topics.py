#!/usr/bin/env python3
"""Update Twitter bot topics to feed the ContentForge content marketing funnel.

Usage:
    python scripts/update_topics.py           # apply updates
    python scripts/update_topics.py --dry-run # preview without writing
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / ".mp" / "twitter.json"

# ---------------------------------------------------------------------------
# Funnel-aligned topics — keep these in sync with ContentForge API positioning
# ---------------------------------------------------------------------------
TOPICS: dict[str, str] = {
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Align bot topics with ContentForge funnel")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()

    if not PATH.exists():
        print(f"ERROR: {PATH} not found — run the app once to initialise accounts.", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(PATH.read_text())
    except json.JSONDecodeError as exc:
        print(f"ERROR: {PATH} is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    accounts = data.get("accounts", [])
    if not accounts:
        print("No accounts found in twitter.json — nothing to update.")
        return

    updated = []
    skipped = []
    for acc in accounts:
        nick = acc.get("nickname")
        if nick in TOPICS:
            old = acc.get("topic", "")
            new = TOPICS[nick]
            if old != new:
                if not args.dry_run:
                    acc["topic"] = new
                updated.append(nick)
            else:
                skipped.append(nick)
        else:
            skipped.append(nick)

    if args.dry_run:
        print("[DRY RUN] The following accounts WOULD be updated:")
        for nick in updated:
            print(f"  {nick}")
        if skipped:
            print(f"Unchanged / not in TOPICS map: {', '.join(skipped)}")
        return

    if not updated:
        print("All accounts already have up-to-date topics.")
        return

    PATH.write_text(json.dumps(data, indent=4))
    for nick in updated:
        print(f"  {nick}: updated")
    if skipped:
        print(f"  Skipped (no change / not mapped): {', '.join(skipped)}")
    print("Done.")


if __name__ == "__main__":
    main()
