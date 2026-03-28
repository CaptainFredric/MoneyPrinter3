# Getting Started with ContentForge API

**ContentForge** helps you create high-performing content using both instant heuristic scoring and AI generation. This guide walks you through your first API calls in under 5 minutes.

---

## Step 1: Get Your API Key

1. Subscribe to any plan on the [ContentForge RapidAPI page](https://rapidapi.com/captainarmoreddude-default-default/api/contentforge1)
2. After subscribing, your `X-RapidAPI-Key` is shown in the **Code Snippets** panel on the right side of any endpoint page
3. Copy your key — you'll use it in every request

---

## Step 2: Score Your First Headline (Instant, No AI)

This endpoint returns a score in milliseconds — no AI, no wait.

### curl
```bash
curl -X POST "https://contentforge-api-lpp9.onrender.com/v1/analyze_headline" \
  -H "X-RapidAPI-Key: YOUR_KEY_HERE" \
  -H "X-RapidAPI-Host: contentforge1.p.rapidapi.com" \
  -H "Content-Type: application/json" \
  -d '{"text": "5 Proven Ways to Double Your Newsletter Open Rate"}'
```

### Python
```python
import requests

url = "https://contentforge-api-lpp9.onrender.com/v1/analyze_headline"
headers = {
    "X-RapidAPI-Key": "YOUR_KEY_HERE",
    "X-RapidAPI-Host": "contentforge1.p.rapidapi.com",
    "Content-Type": "application/json"
}
payload = {"text": "5 Proven Ways to Double Your Newsletter Open Rate"}

response = requests.post(url, headers=headers, json=payload)
data = response.json()

print(f"Score: {data['score']}/100  Grade: {data['grade']}")
print(f"Power words found: {data['power_words_found']}")
print(f"Suggestions: {data['suggestions']}")
```

### JavaScript (Node.js / fetch)
```javascript
const response = await fetch(
  "https://contentforge-api-lpp9.onrender.com/v1/analyze_headline",
  {
    method: "POST",
    headers: {
      "X-RapidAPI-Key": "YOUR_KEY_HERE",
      "X-RapidAPI-Host": "contentforge1.p.rapidapi.com",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text: "5 Proven Ways to Double Your Newsletter Open Rate" }),
  }
);
const data = await response.json();
console.log(`Score: ${data.score}/100  Grade: ${data.grade}`);
console.log("Suggestions:", data.suggestions);
```

**Example Response:**
```json
{
  "text": "5 Proven Ways to Double Your Newsletter Open Rate",
  "score": 78,
  "grade": "B",
  "length": 49,
  "word_count": 9,
  "has_number": true,
  "power_words_found": ["proven", "double"],
  "suggestions": ["Consider adding urgency or a curiosity gap to push above 80."]
}
```

---

## Step 3: Score a Tweet Draft Before Posting

Check your tweet BEFORE you post it. Only publish A or B grade content.

```python
import requests

url = "https://contentforge-api-lpp9.onrender.com/v1/score_tweet"
headers = {
    "X-RapidAPI-Key": "YOUR_KEY_HERE",
    "X-RapidAPI-Host": "contentforge1.p.rapidapi.com",
    "Content-Type": "application/json"
}

tweets_to_try = [
    "I'm working on a new project.",
    "Built a side project. Got 100 signups in 24 hours 🚀 Here's the exact homepage copy I used: #buildinpublic"
]

for tweet in tweets_to_try:
    r = requests.post(url, headers=headers, json={"text": tweet})
    d = r.json()
    print(f"[{d['grade']}] Score {d['score']} — {tweet[:60]}...")
```

Output:
```
[C] Score 32 — I'm working on a new project...
[A] Score 91 — Built a side project. Got 100 signups in 24 hours 🚀 H...
```

Post the A. Skip the C. It takes 1 second.

---

## Step 4: Improve a Weak Headline with AI

Found your headline scores below 60? Have the AI rewrite it into 3 better versions, each pre-scored.

```python
import requests

url = "https://contentforge-api-lpp9.onrender.com/v1/improve_headline"
headers = {
    "X-RapidAPI-Key": "YOUR_KEY_HERE",
    "X-RapidAPI-Host": "contentforge1.p.rapidapi.com",
    "Content-Type": "application/json"
}

r = requests.post(url, headers=headers, json={
    "text": "How to make money online",
    "count": 3
})
data = r.json()

print(f"Original: {data['original']}  ({data['original_grade']}, score {data['original_score']})\n")
print("Improved versions:")
for v in data["improved_versions"]:
    print(f"  [{v['grade']}] Score {v['score']} — {v['text']}")
```

Output:
```
Original: How to make money online  (C, score 49)

Improved versions:
  [A] Score 100 — Can You Really Earn $5,000 a Month Online? Discover the Secrets
  [B] Score 72  — Proven Blueprint: Make Your First $1,000 Online This Month
  [B] Score 68  — 7 Legitimate Ways to Build Income Online (Without Any Experience)
```

---

## Step 5: Generate a Twitter Thread Outline

Turn any topic into a ready-to-post thread in seconds.

```python
import requests

url = "https://contentforge-api-lpp9.onrender.com/v1/thread_outline"
headers = {
    "X-RapidAPI-Key": "YOUR_KEY_HERE",
    "X-RapidAPI-Host": "contentforge1.p.rapidapi.com",
    "Content-Type": "application/json"
}

r = requests.post(url, headers=headers, json={
    "topic": "why most people fail at building habits",
    "tweet_count": 6,
    "tone": "bold"
})
data = r.json()

print("HOOK:", data["hook"])
print()
for tweet in data["tweets"]:
    print(tweet)
    print()
print("CTA:", data["cta"])
```

---

## Step 6: Generate Your Social Bio

```python
import requests

url = "https://contentforge-api-lpp9.onrender.com/v1/generate_bio"
headers = {
    "X-RapidAPI-Key": "YOUR_KEY_HERE",
    "X-RapidAPI-Host": "contentforge1.p.rapidapi.com",
    "Content-Type": "application/json"
}

r = requests.post(url, headers=headers, json={
    "name": "Jordan Lee",
    "niche": "productivity coach helping remote workers do deep work",
    "platform": "twitter",
    "tone": "casual",
    "keywords": ["deep work", "focus", "no-distraction system"]
})
data = r.json()

print(data["bio"])
print(f"({data['char_count']}/{data['char_limit']} chars — valid: {data['is_valid_length']})")
```

---

## Step 7: Build a 7-Day Content Calendar

```python
import requests

url = "https://contentforge-api-lpp9.onrender.com/v1/content_calendar"
headers = {
    "X-RapidAPI-Key": "YOUR_KEY_HERE",
    "X-RapidAPI-Host": "contentforge1.p.rapidapi.com",
    "Content-Type": "application/json"
}

r = requests.post(url, headers=headers, json={
    "niche": "indie hacking",
    "days": 7,
    "platform": "twitter",
    "tone": "motivational"
})
data = r.json()

for day in data["calendar"]:
    print(f"{day['day']} [{day['theme']}]")
    print(f"  {day['draft']}")
    print()
```

---

## Rate Limits

Every response includes rate limit headers:

| Header | Meaning |
|---|---|
| `X-RateLimit-Limit` | Max requests per minute on your plan |
| `X-RateLimit-Remaining` | Requests left in this window |
| `X-RateLimit-Window` | Window duration |

On the free BASIC plan, the global rate limit is 30 requests/minute. PRO and above have higher limits.

---

## Error Codes

| Code | Meaning | Fix |
|---|---|---|
| 400 | Missing or invalid parameter | Check required parameters in the endpoint docs |
| 403 | Authentication failed | Verify your `X-RapidAPI-Key` header is present |
| 429 | Rate limit exceeded | Wait for the next window or upgrade your plan |
| 503 | LLM generation failed | AI backend is temporarily busy; retry in a few seconds |

---

## Tips for Best Results

1. **Use `score_tweet` before every post.** If score < 60, use `improve_headline` or rewrite manually.  
2. **Batch `analyze_headline` calls** — it's instant and has no AI cost, so you can run 10+ versions in one loop.
3. **Thread outlines need editing.** AI gives you the skeleton; you refine the voice.
4. **`generate_bio` + `analyze_headline` the bio.** Use the headline scorer to check if your bio has strong power words.
5. **Cold start note:** The API runs on Render free tier. First request after 15 min idle may take up to 10 seconds. Subsequent requests are fast.

---

## Support

- **Email:** captainarmoreddude@gmail.com
- **RapidAPI Discussions:** Use the Discussions tab on the listing page
- **GitHub Issues:** https://github.com/CaptainFredric/MoneyPrinter3/issues
