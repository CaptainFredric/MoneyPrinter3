#!/usr/bin/env python3
"""Quick validation for the 3 new scoring endpoints."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api_prototype import (
    score_instagram_caption,
    score_youtube_title,
    score_email_subject,
)

def t(name, result, min_score=None, max_score=None, expected_grade=None):
    s, g = result["score"], result["grade"]
    ok = True
    if min_score is not None and s < min_score:
        ok = False
    if max_score is not None and s > max_score:
        ok = False
    if expected_grade and g != expected_grade:
        ok = False
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}: {s}/{g}", end="")
    if not ok:
        print(f"  (expected: score {min_score}-{max_score}, grade={expected_grade})")
    else:
        print()
    return ok

print("=" * 60)
print("INSTAGRAM CAPTION SCORER")
print("=" * 60)

all_ok = True

# 1. Optimal: good length, emojis, hashtags, CTA, line breaks
r = score_instagram_caption(
    "Stop scrolling. This changed everything.\n\n"
    "I tried 30 days of cold showers and here's what happened 🧊💪\n\n"
    "The results surprised me:\n"
    "- More energy by 8 AM\n"
    "- Better focus all day\n"
    "- Skin cleared up in 2 weeks\n\n"
    "Save this for later 👇\n\n"
    "#morningroutine #coldshower #productivity #selfimprovement #lifehacks "
    "#wellness #healthtips #dailyhabits"
)
all_ok &= t("Optimal caption", r, min_score=80, expected_grade="A")

# 2. Bad: too short, no hashtags, no emojis
r = score_instagram_caption("nice pic")
all_ok &= t("Too short", r, max_score=40)

# 3. Medium: decent but missing elements
r = score_instagram_caption(
    "Monday motivation! Start your week right.\n\n#motivation #monday"
)
all_ok &= t("Medium caption", r, min_score=40, max_score=79)

# 4. Over-hashtagged (31+)
tags = " ".join(f"#tag{i}" for i in range(32))
r = score_instagram_caption(f"Cool photo! {tags}")
all_ok &= t("Over-hashtagged", r, max_score=60)

print()
print("=" * 60)
print("YOUTUBE TITLE SCORER")
print("=" * 60)

# 5. Optimal: good length, number, bracket, power word
r = score_youtube_title(
    "I Tried Making $1,000 in 24 Hours [Honest Results]",
    "MADE $1K??"
)
all_ok &= t("Optimal title + thumb", r, min_score=80, expected_grade="A")

# 6. Bare minimum title
r = score_youtube_title("vlog")
all_ok &= t("Too short title", r, max_score=45)

# 7. Good title, no thumbnail
r = score_youtube_title("5 SECRET Apps That Pay You Real Money (2026)")
all_ok &= t("Strong title no thumb", r, min_score=75)

# 8. ALL CAPS spam title
r = score_youtube_title("YOU WILL NEVER BELIEVE WHAT HAPPENED WHEN I DID THIS!!!")
all_ok &= t("Caps spam title", r, max_score=60)

print()
print("=" * 60)
print("EMAIL SUBJECT SCORER")
print("=" * 60)

# 9. Optimal: personalized, number, power word, good length
r = score_email_subject(
    "{first_name}, your 3-step plan is ready",
    "Open to see the strategy top creators use"
)
all_ok &= t("Optimal subject + preview", r, min_score=80, expected_grade="A")

# 10. Spammy subject
r = score_email_subject("BUY NOW!!! FREE CASH GUARANTEED!!! Click here!!!")
all_ok &= t("Spammy subject", r, max_score=35)

# 11. Decent newsletter subject
r = score_email_subject("3 proven ways to grow your email list")
all_ok &= t("Decent subject", r, min_score=55)

# 12. Too short
r = score_email_subject("Hi")
all_ok &= t("Too short subject", r, max_score=45)

print()
print("=" * 60)
if all_ok:
    print("ALL 12 TESTS PASSED")
else:
    print("SOME TESTS FAILED")
print("=" * 60)
