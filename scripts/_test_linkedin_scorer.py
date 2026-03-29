#!/usr/bin/env python3
"""Quick test for score_linkedin_post()."""
import sys
sys.path.insert(0, "src")
sys.path.insert(0, "scripts")
from api_prototype import score_linkedin_post


def test(label, text):
    r = score_linkedin_post(text)
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  Score: {r['score']} / Grade: {r['grade']}")
    print(f"  Chars: {r['char_count']} / Words: {r['word_count']} / Paras: {r['paragraph_count']}")
    print(f"  Hook ({r['hook_length']} chars): {r['hook_preview']!r}")
    print(f"  List: {r['has_list']} ({r['list_items_detected']} items)")
    print(f"  Hashtags: {r['hashtag_count']} / Emoji: {r['emoji_count']}")
    print(f"  URL penalty: {r['url_penalty_applied']} / CTA: {r['has_cta']} / Q-end: {r['has_question_at_end']}")
    print(f"  Power words: {r['power_words_found']}")
    if r["suggestions"]:
        print(f"  Suggestions:")
        for s in r["suggestions"]:
            print(f"    - {s}")
    else:
        print(f"  Suggestions: (none)")
    return r


# Test 1: Optimal LinkedIn post
r1 = test("TEST 1: Optimal post (story + list + CTA + 3 hashtags)", """I spent 3 years building tools nobody used.

Then I changed one thing: I started scoring my own content before posting.

Here is what I learned:

- Your hook decides everything (keep it under 150 chars)
- Short paragraphs get 2x more read-throughs
- A question at the end doubles your comments

The result? 4x more engagement in 2 months.

What is one thing you changed that boosted your reach?

#contentcreation #linkedin #buildinpublic""")

# Test 2: Bad post (short, URL, no hashtags)
r2 = test("TEST 2: Bad post (short, URL, no structure)", "Check out my new tool https://example.com")

# Test 3: Medium post (decent but missing elements)
r3 = test("TEST 3: Medium post (no hashtags, no CTA, no list)", """The biggest mistake I see on LinkedIn is treating it like Twitter.

LinkedIn rewards depth. If you are writing 280-character posts, you are leaving reach on the table.

The algorithm wants you to stay on platform, share real experiences, and start conversations.

Stop posting links. Start posting stories.""")

# Test 4: Spammy post
r4 = test("TEST 4: Spammy (caps, excess emoji, excess hashtags, URL)", """THIS IS THE BEST TOOL EVER!!! YOU NEED THIS NOW!!!

CHECK IT OUT at https://example.com

SO AMAZING WOW \U0001f929\U0001f929\U0001f929\U0001f929\U0001f929\U0001f929\U0001f929\U0001f929

#linkedin #tools #best #amazing #wow #cool #viral #growth #money #success #hustle""")

# Test 5: Real-world ContentForge promo (what you would actually post)
r5 = test("TEST 5: Real-world ContentForge promo for LinkedIn", """I built a free API that scores your content before you post it.

It started as a side project to solve my own problem. I kept writing tweets and LinkedIn posts without knowing if they were actually good.

So I built ContentForge:
- Tweet scorer (0-100 grade with tips)
- LinkedIn post scorer (hook, structure, hashtag analysis)
- Headline analyzer
- Bio generator

All free. 50 API calls per month, no credit card.

The tweet scorer is pure heuristics, no AI. It is instant and deterministic. The generative tools use Gemini under the hood.

If you are a developer who makes content, I would love your feedback.

What would make this more useful to you?

#buildinpublic #contentcreation #api #developers""")

# Test 6: Edge case - just hashtags
r6 = test("TEST 6: Edge case (hashtags only)", "#test #hello #world")

# Test 7: Very long post
r7 = test("TEST 7: Very long post (2500+ chars)", """I have been thinking a lot about what makes content work on LinkedIn.

After 6 months of posting daily, here is everything I have learned about the algorithm, engagement, and what actually drives results on this platform.

1. The hook is everything

Your first 2 lines decide if someone clicks "see more." If you bury the lead, you lose 90 percent of potential readers. Start with something personal, surprising, or specific.

2. Short paragraphs win

Nobody reads walls of text on their phone. Keep each paragraph to 1-2 sentences max. Use line breaks aggressively.

3. Lists get saves

When people see a numbered or bulleted list, they are more likely to save the post for later. Saves signal the algorithm that the content has lasting value.

4. External links kill reach

LinkedIn wants you to stay on LinkedIn. Every time you add an external URL, the algorithm suppresses your post reach by an estimated 50 percent. Put links in the comments instead.

5. Questions drive comments

The algorithm loves comments more than likes. If you end with a genuine question, you will get 3-5x more comments than a statement ending.

6. Hashtags still matter

3-5 relevant hashtags help LinkedIn categorize your post and show it to the right people. More than 5 looks spammy.

7. Post between 8-10am on weekdays

Tuesday through Thursday morning posts get the most initial engagement, which compounds through the day.

8. Engagement in the first hour matters most

Reply to every comment within the first 60 minutes. This signals to the algorithm that your post is generating real conversation.

Here is my framework for every post:
- Hook (under 150 chars)
- Story or insight (3-5 paragraphs)
- List or framework (easy to scan)
- Question or CTA (drives comments)
- 3-5 hashtags at the end

This simple structure has increased my average impressions from 200 to 3000 per post.

What is your best LinkedIn posting tip? Drop it below.

#linkedin #contentcreation #socialmedia #buildinpublic""")

# Summary
print(f"\n{'='*60}")
print("  SUMMARY")
print(f"{'='*60}")
tests = [
    ("Optimal post", r1),
    ("Bad post", r2),
    ("Medium post", r3),
    ("Spammy post", r4),
    ("Real promo", r5),
    ("Hashtags only", r6),
    ("Very long", r7),
]
for label, r in tests:
    print(f"  {label:20s}  Score: {r['score']:3d}  Grade: {r['grade']}")
