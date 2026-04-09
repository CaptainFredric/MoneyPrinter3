#!/usr/bin/env python3
"""Focused regression checks for the headline scorer."""

from scripts.api_prototype import analyze_headline


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    renewable = analyze_headline("Renewable energy guide for first-time founders")
    assert_true(
        "new" not in renewable["power_words_found"],
        "substring matching should not count 'new' inside 'renewable'",
    )

    strong = analyze_headline("7 pricing mistakes that quietly kill SaaS revenue")
    weak = analyze_headline("ACT NOW: 100% FREE money online!!!")

    assert_true(strong["score"] > weak["score"], "specific headline should beat spammy headline")
    assert_true(strong["quality_gate"] in {"REVIEW", "PASSED"}, "strong headline should be viable")
    assert_true(weak["quality_gate"] == "FAILED", "spammy headline should fail the gate")
    assert_true(
        any(signal["signal"] == "spam_phrases" for signal in weak["signal_breakdown"]),
        "spammy headline should expose spam phrase penalty",
    )

    question = analyze_headline("Why 3 tiny landing page tweaks doubled demo requests")
    assert_true(question["headline_type"] in {"question", "listicle"}, "headline type should be detected")
    assert_true(question["score"] >= 70, "question headline with specificity should score well")

    print("headline scorer checks passed")


if __name__ == "__main__":
    main()
