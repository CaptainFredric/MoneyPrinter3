#!/usr/bin/env python3
"""
scripts/system_dashboard.py

Single-pane system dashboard for ContentForge + Twitter bots.

Shows at a glance:
  - ContentForge API health (production + local if running)
  - Twitter bot account states and recent post history
  - API usage stats from local log
  - Render deployment status
  - Gemini quota indicators

Usage:
  python scripts/system_dashboard.py
  python scripts/system_dashboard.py --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Paths
TWITTER_CACHE = ROOT / ".mp" / "twitter.json"
STATES_FILE = ROOT / ".mp" / "runtime" / "account_states.json"
API_USAGE_LOG = ROOT / ".mp" / "api_usage.json"
CONTENTFORGE_URL = "https://contentforge-api-lpp9.onrender.com"
LOCAL_API_URL = "http://127.0.0.1:8081"

# Colors for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"
DIM = "\033[2m"


def _check_url(url: str, timeout: int = 8) -> tuple[bool, dict | None, float]:
    """Returns (reachable, response_json_or_none, latency_ms)."""
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MPV2-Dashboard/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            latency = (time.time() - t0) * 1000
            try:
                data = json.loads(resp.read().decode())
            except Exception:
                data = None
            return True, data, latency
    except Exception:
        latency = (time.time() - t0) * 1000
        return False, None, latency


def _status_icon(ok: bool) -> str:
    return f"{GREEN}✅{RESET}" if ok else f"{RED}❌{RESET}"


def _grade_color(grade: str) -> str:
    return {
        "A": GREEN,
        "B": CYAN,
        "C": YELLOW,
        "D": RED,
    }.get(grade.upper(), RESET)


def _load_json(path: Path) -> dict | list | None:
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _time_ago(dt_str: str) -> str:
    """Convert ISO timestamp to human-readable 'X ago' string."""
    if not dt_str:
        return "never"
    try:
        # Handle both formats: "2026-03-28T12:00:00" and "03/28/2026, 12:00:00"
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%m/%d/%Y, %H:%M:%S"):
            try:
                dt = datetime.strptime(dt_str[:len(fmt)], fmt)
                break
            except ValueError:
                continue
        else:
            return dt_str[:16]

        now = datetime.now()
        diff = now - dt
        secs = int(diff.total_seconds())
        if secs < 60:
            return f"{secs}s ago"
        if secs < 3600:
            return f"{secs // 60}m ago"
        if secs < 86400:
            return f"{secs // 3600}h ago"
        return f"{secs // 86400}d ago"
    except Exception:
        return dt_str[:16]


def section(title: str) -> None:
    width = 62
    print(f"\n{BOLD}{CYAN}{'─' * width}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─' * width}{RESET}")


def build_report(as_json: bool = False) -> dict:
    report: dict = {
        "generated_at": datetime.now().isoformat(),
        "api": {},
        "twitter": {},
        "usage": {},
    }

    # ── ContentForge API ──────────────────────────────────────────
    prod_ok, prod_data, prod_ms = _check_url(CONTENTFORGE_URL + "/health")
    local_ok, local_data, local_ms = _check_url(LOCAL_API_URL + "/health")

    report["api"]["production"] = {
        "reachable": prod_ok,
        "latency_ms": round(prod_ms),
        "data": prod_data,
    }
    report["api"]["local"] = {
        "reachable": local_ok,
        "latency_ms": round(local_ms),
        "data": local_data,
    }

    # ── Twitter accounts ──────────────────────────────────────────
    twitter_data = _load_json(TWITTER_CACHE) or {}
    states_data = _load_json(STATES_FILE) or {}
    account_states = states_data.get("accounts", {})

    accounts_report = []
    for acc in twitter_data.get("accounts", []):
        nickname = acc.get("nickname", "?")
        posts = acc.get("posts", [])
        state = account_states.get(nickname, {})
        health = state.get("health_score", 0)
        acc_state = state.get("state", "unknown")
        last_post_at = state.get("last_post_at", "")
        # Prefer the actual post date from the posts array (more accurate)
        if posts:
            last_post_at = posts[-1].get("date", last_post_at)
        last_post_status = state.get("last_post_status", "")

        # Count verified posts
        verified = sum(
            1 for p in posts
            if p.get("confidence_score", 0) >= 80 or "verified" in p.get("status", "")
        )

        accounts_report.append({
            "nickname": nickname,
            "state": acc_state,
            "health_score": health,
            "total_posts": len(posts),
            "verified_posts": verified,
            "last_post_at": last_post_at,
            "last_post_status": last_post_status,
        })
    report["twitter"]["accounts"] = accounts_report

    # ── API Usage Stats ───────────────────────────────────────────
    usage_data = _load_json(API_USAGE_LOG) or []
    if isinstance(usage_data, list):
        endpoint_counts: dict[str, int] = {}
        total_latency_by_ep: dict[str, list[int]] = {}
        for entry in usage_data:
            ep = entry.get("endpoint", "unknown")
            endpoint_counts[ep] = endpoint_counts.get(ep, 0) + 1
            total_latency_by_ep.setdefault(ep, []).append(entry.get("latency_ms", 0))

        avg_latencies = {
            ep: round(sum(lats) / len(lats))
            for ep, lats in total_latency_by_ep.items()
        }
        report["usage"] = {
            "total_requests": len(usage_data),
            "by_endpoint": endpoint_counts,
            "avg_latency_ms": avg_latencies,
        }

    return report


def print_dashboard(report: dict) -> None:
    print(f"\n{BOLD}{'═' * 62}")
    print(f"  ContentForge + Twitter Bot Dashboard")
    print(f"  Generated: {report['generated_at'][:19]}")
    print(f"{'═' * 62}{RESET}")

    # ── API Section ────────────────────────────────────────────────
    section("ContentForge API")

    prod = report["api"]["production"]
    prod_data = prod.get("data") or {}
    prod_ok = prod["reachable"]
    llm = prod_data.get("llm_backend", "?")
    ai_ready = prod_data.get("ai_endpoints_ready", False)

    print(f"  Production : {_status_icon(prod_ok)}  {CONTENTFORGE_URL}")
    if prod_ok:
        print(f"  LLM backend: {CYAN}{llm}{RESET}  |  AI ready: {_status_icon(ai_ready)}  |  Latency: {prod['latency_ms']}ms")
        total = prod_data.get("total_requests_served", "?")
        print(f"  Total reqs : {CYAN}{total}{RESET}")
    else:
        print(f"  {RED}  → Cannot reach production API{RESET}")

    local = report["api"]["local"]
    local_ok = local["reachable"]
    print(f"\n  Local dev  : {_status_icon(local_ok)}  {LOCAL_API_URL}", end="")
    if local_ok:
        local_data = local.get("data") or {}
        print(f"  (LLM: {local_data.get('llm_backend', '?')}, {local['latency_ms']}ms)")
    else:
        print(f"  {DIM}(not running){RESET}")

    # ── Twitter Section ────────────────────────────────────────────
    section("Twitter Bot Accounts")

    for acc in report["twitter"].get("accounts", []):
        name = acc["nickname"]
        state = acc["state"]
        health = acc["health_score"]
        posts = acc["total_posts"]
        verified = acc["verified_posts"]
        last_at = _time_ago(acc["last_post_at"])
        last_status = acc["last_post_status"][:40] if acc["last_post_status"] else "—"

        # State coloring
        state_color = {
            "active": GREEN,
            "cooldown": YELLOW,
            "degraded": YELLOW,
            "blocked": RED,
            "paused": RED,
        }.get(state, RESET)

        health_color = GREEN if health >= 80 else YELLOW if health >= 50 else RED

        print(f"\n  {BOLD}{name}{RESET}")
        print(f"    State   : {state_color}{state}{RESET}  |  Health: {health_color}{health}/100{RESET}")
        print(f"    Posts   : {posts} total, {verified} verified")
        print(f"    Last    : {last_at}  ({DIM}{last_status}{RESET})")

    # ── Usage Stats Section ────────────────────────────────────────
    section("API Usage (Local Log)")

    usage = report.get("usage", {})
    total = usage.get("total_requests", 0)
    by_ep = usage.get("by_endpoint", {})
    avg_lat = usage.get("avg_latency_ms", {})

    print(f"  Total requests logged: {CYAN}{total}{RESET}")
    if by_ep:
        print()
        print(f"  {'Endpoint':<25} {'Calls':>6}  {'Avg Latency':>12}")
        print(f"  {'─' * 25}  {'─' * 6}  {'─' * 12}")
        for ep, count in sorted(by_ep.items(), key=lambda x: -x[1]):
            lat = avg_lat.get(ep, "?")
            lat_str = f"{lat}ms" if isinstance(lat, int) else "?"
            print(f"  {ep:<25} {count:>6}  {lat_str:>12}")

    # ── Quick Actions ──────────────────────────────────────────────
    section("Quick Actions")
    print(f"  {DIM}Post tweet    : python scripts/smart_post_twitter.py --headless{RESET}")
    print(f"  {DIM}Promo post    : python scripts/promo_contentforge.py --headless{RESET}")
    print(f"  {DIM}Readiness     : python scripts/twitter_readiness_report.py{RESET}")
    print(f"  {DIM}Performance   : python scripts/performance_report.py{RESET}")
    print(f"  {DIM}API test      : .runtime-venv/bin/python scripts/api_prototype.py --test{RESET}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="ContentForge system dashboard")
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of formatted")
    args = parser.parse_args()

    report = build_report()

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_dashboard(report)


if __name__ == "__main__":
    main()
