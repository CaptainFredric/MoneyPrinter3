#!/usr/bin/env python3
"""Quick tests for TikTok scorer and hashtag analyzer."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from api_prototype import score_tiktok_caption, analyze_hashtags

print("=== TikTok Scorer ===")
tests_tiktok = [
    ("Optimal",
     "POV: you stop guessing and start scoring your content 🎯 Try this free tool #contenttips #tiktokmarketing #growthhack #viral"),
    ("Too short",
     "#viral"),
    ("No hashtags no CTA",
     "This is a tutorial about content marketing."),
    ("Over-tagged",
     "Watch this #viral #fyp #foryou #trending #hack #content #tips #creator #growth #engagement #lol #omg #follow #save #share #likes"),
    ("Empty",
     ""),
]

passed = 0
for name, text in tests_tiktok:
    r = score_tiktok_caption(text)
    ok = (isinstance(r["score"], int) and 0 <= r["score"] <= 100
          and r["grade"] in ("A","B","C","D","F"))
    status = "PASS" if ok else "FAIL"
    if ok: passed += 1
    print(f"  [{status}] {name:25s}  score={r['score']:3d}/{r['grade']}  "
          f"tags={r['hashtag_count']}  emojis={r['emoji_count']}  cta={r['has_cta']}")

print(f"\n=== Hashtag Analyzer ===")
tests_ht = [
    ("Twitter optimal", "#buildinpublic #indiehackers #saas", "twitter"),
    ("Instagram good", "#fitness #gym #workout #motivation #fitfam #bodybuilding #health #wellness", "instagram"),
    ("TikTok over-tagged", "#viral #fyp #foryou #trend #hack #creator #content #growth #seo #marketing #tips #love #life #fun #happy", "tiktok"),
    ("Duplicates", "#saas #buildinpublic #saas #indiehackers", "twitter"),
    ("Spam tags", "#followme #follow4follow #likeforlike", "twitter"),
    ("Empty", "", "twitter"),
]

for name, tags, platform in tests_ht:
    r = analyze_hashtags(tags, platform)
    ok = (isinstance(r["score"], int) and 0 <= r["score"] <= 100
          and r["grade"] in ("A","B","C","D","F"))
    status = "PASS" if ok else "FAIL"
    if ok: passed += 1
    print(f"  [{status}] {name:25s}  score={r['score']:3d}/{r['grade']}  "
          f"count={r['hashtag_count']}  ideal={r['platform_ideal_range']}  "
          f"spam={len(r['spam_risk_tags'])}  dups={len(r['duplicates'])}")

total = len(tests_tiktok) + len(tests_ht)
print(f"\n{passed}/{total} passed")
assert passed == total, f"FAILED: {total - passed} tests failed"
print("ALL TESTS PASSED")
