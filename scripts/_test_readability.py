#!/usr/bin/env python3
"""Quick test for the readability scorer."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from api_prototype import score_readability

tests = [
    ("Simple text",
     "Short sentences work best. They keep the reader engaged. Use simple words too."),
    ("Academic text",
     "The epistemological ramifications of quantum mechanical indeterminacy fundamentally "
     "preclude the possibility of establishing comprehensive ontological frameworks for "
     "subatomic phenomena."),
    ("Blog post",
     "I started my SaaS three months ago. The first month was rough. Nobody signed up. "
     "But I kept building and sharing progress. By month three I had 50 paying customers. "
     "Here is what worked for me."),
    ("Tweet-length",
     "Just shipped my first API endpoint!"),
    ("Long with breaks",
     "Content marketing is changing fast.\n\nShort posts win on Twitter. "
     "Longer posts win on LinkedIn.\n\nBut the best posts share one thing: clarity.\n\n"
     "Write like you talk. Keep it simple. Cut the jargon."),
    ("Empty",
     ""),
]

passed = 0
for name, text in tests:
    r = score_readability(text)
    ok = (
        isinstance(r["score"], int)
        and 0 <= r["score"] <= 100
        and r["grade"] in ("A", "B", "C", "D", "F")
        and isinstance(r["suggestions"], list)
        and len(r["suggestions"]) > 0
    )
    status = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    print(f"  [{status}] {name:20s}  score={r['score']:3d}/{r['grade']}  "
          f"FRE={r['flesch_reading_ease']:5.1f}  FKGL={r['flesch_kincaid_grade']:4.1f}  "
          f"level={r.get('reading_level','?'):15s}  "
          f"sents={r['sentence_count']}  words={r['word_count']}")
    if not ok:
        print(f"       DETAILS: {json.dumps(r, indent=2)}")

print(f"\n{passed}/{len(tests)} passed")
assert passed == len(tests), f"FAILED: {len(tests) - passed} tests failed"
print("ALL TESTS PASSED")
