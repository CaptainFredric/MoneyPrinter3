#!/usr/bin/env python3
"""Run ContentForge against historical content and measure calibration quality.

Input schema
============

CSV or JSON records must include:

- cohort_id: group of drafts that should be ranked against each other
- platform: ContentForge platform key, such as tweet, linkedin, headline
- text: the content to score
- actual_outcome: numeric ground truth chosen by the operator

Optional fields are preserved in the report:

- label, post_url, notes, impressions, clicks, likes, comments, shares, saves

Typical usage
=============

python scripts/calibrate_content.py \
  --input docs/calibration_dataset_template.csv \
  --report-json docs/calibration_report.json \
  --report-md docs/calibration_report.md \
  --examples-json docs/calibration_examples.json
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from scripts.api_prototype import _PLATFORM_SCORERS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_JSON = ROOT / "docs" / "calibration_report.json"
DEFAULT_REPORT_MD = ROOT / "docs" / "calibration_report.md"
DEFAULT_EXAMPLES_JSON = ROOT / "docs" / "calibration_examples.json"


@dataclass
class CalibrationRow:
    cohort_id: str
    platform: str
    text: str
    actual_outcome: float
    label: str
    post_url: str
    notes: str
    raw: dict


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _coerce_float(value) -> float:
    if value is None:
        raise ValueError("missing numeric value")
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if not text:
        raise ValueError("missing numeric value")
    return float(text)


def _normalize_platform(value: str) -> str:
    platform = str(value or "").strip().lower()
    aliases = {
        "twitter": "tweet",
        "x": "tweet",
        "email_subject": "email",
        "youtube_title": "youtube",
    }
    return aliases.get(platform, platform)


def _load_records(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    if suffix == ".json":
        loaded = json.loads(path.read_text())
        if isinstance(loaded, dict) and isinstance(loaded.get("records"), list):
            return loaded["records"]
        if isinstance(loaded, list):
            return loaded
        raise ValueError("JSON input must be a list or {'records': [...]}")

    if suffix != ".csv":
        raise ValueError("input must be .csv or .json")

    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _build_rows(records: Iterable[dict]) -> list[CalibrationRow]:
    rows: list[CalibrationRow] = []
    for index, record in enumerate(records, start=1):
        platform = _normalize_platform(record.get("platform"))
        if platform not in _PLATFORM_SCORERS:
            raise ValueError(f"row {index}: unsupported platform '{platform}'")

        cohort_id = str(record.get("cohort_id") or "").strip()
        if not cohort_id:
            raise ValueError(f"row {index}: missing cohort_id")

        text = str(record.get("text") or "").strip()
        if not text:
            raise ValueError(f"row {index}: missing text")

        actual_source = (
            record.get("actual_outcome")
            if record.get("actual_outcome") not in (None, "")
            else record.get("engagement_score")
            if record.get("engagement_score") not in (None, "")
            else record.get("actual_score")
        )
        actual_outcome = _coerce_float(actual_source)

        label = str(record.get("label") or f"{cohort_id}-{index}").strip()
        rows.append(
            CalibrationRow(
                cohort_id=cohort_id,
                platform=platform,
                text=text,
                actual_outcome=actual_outcome,
                label=label,
                post_url=str(record.get("post_url") or record.get("url") or "").strip(),
                notes=str(record.get("notes") or "").strip(),
                raw=dict(record),
            )
        )
    return rows


def _rank_desc(items: list[dict], field: str) -> list[dict]:
    ordered = sorted(items, key=lambda item: (item.get(field, 0), item.get("label", "")), reverse=True)
    for rank, item in enumerate(ordered, start=1):
        item[field + "_rank"] = rank
    return ordered


def _spearman(records: list[dict]) -> float | None:
    count = len(records)
    if count < 2:
        return None
    total = sum((row["predicted_rank"] - row["actual_rank"]) ** 2 for row in records)
    return round(1 - ((6 * total) / (count * ((count * count) - 1))), 4)


def _score_row(row: CalibrationRow) -> dict:
    payload = dict(row.raw)
    scored = _PLATFORM_SCORERS[row.platform](row.text, payload)
    return {
        "cohort_id": row.cohort_id,
        "platform": row.platform,
        "label": row.label,
        "text": row.text,
        "text_preview": row.text[:180] + ("..." if len(row.text) > 180 else ""),
        "actual_outcome": round(row.actual_outcome, 4),
        "post_url": row.post_url,
        "notes": row.notes,
        "predicted_score": int(scored.get("score", 0)),
        "grade": scored.get("grade"),
        "quality_gate": scored.get("quality_gate"),
        "operational_risk": scored.get("operational_risk"),
        "suggestions": list(scored.get("suggestions", []))[:5],
        "power_words_found": list(scored.get("power_words_found", []))[:8],
        "signal_breakdown": list(scored.get("signal_breakdown", []))[:6],
    }


def _examples_payload(summary: dict, cohort_results: list[dict], all_rows: list[dict]) -> dict:
    hits: list[dict] = []
    misses: list[dict] = []

    for row in all_rows:
        if row.get("actual_rank") == row.get("predicted_rank") == 1:
            hits.append(
                {
                    "kind": "hit",
                    "platform": row["platform"],
                    "cohort_id": row["cohort_id"],
                    "label": row["label"],
                    "text_preview": row["text_preview"],
                    "predicted_score": row["predicted_score"],
                    "grade": row["grade"],
                    "predicted_rank": row["predicted_rank"],
                    "actual_rank": row["actual_rank"],
                    "actual_outcome": row["actual_outcome"],
                    "power_words_found": row.get("power_words_found", []),
                }
            )
        elif row.get("rank_error", 0) >= 2:
            misses.append(
                {
                    "kind": "miss",
                    "platform": row["platform"],
                    "cohort_id": row["cohort_id"],
                    "label": row["label"],
                    "text_preview": row["text_preview"],
                    "predicted_score": row["predicted_score"],
                    "predicted_rank": row["predicted_rank"],
                    "actual_rank": row["actual_rank"],
                    "actual_outcome": row["actual_outcome"],
                    "rank_error": row["rank_error"],
                }
            )

    strongest_hits = sorted(hits, key=lambda item: (item["predicted_score"], item["actual_outcome"]), reverse=True)[:6]
    biggest_misses = sorted(misses, key=lambda item: (item["rank_error"], item["actual_outcome"]), reverse=True)[:4]

    return {
        "generated_at": _utc_now_iso(),
        "summary": summary,
        "cohorts": [
            {
                "cohort_id": item["cohort_id"],
                "platform": item["platform"],
                "size": item["size"],
                "top_pick_correct": item["top_pick_correct"],
                "spearman": item["spearman"],
            }
            for item in cohort_results
        ],
        "examples": strongest_hits,
        "misses": biggest_misses,
        "empty_state": {
            "title": "Public proof is still being built",
            "body": "Run the calibration harness on your own historical posts to replace this empty state with real examples.",
            "cta_label": "Join the calibration log",
            "cta_href": "docs/blind-taste-test.md",
        },
    }


def _markdown_report(summary: dict, cohort_results: list[dict]) -> str:
    lines = [
        "# ContentForge Calibration Report",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Summary",
        "",
        f"- Cohorts: {summary['cohort_count']}",
        f"- Drafts scored: {summary['draft_count']}",
        f"- Top pick accuracy: {summary['top_pick_accuracy_pct']}%",
        f"- Average Spearman correlation: {summary['avg_spearman'] if summary['avg_spearman'] is not None else 'n/a'}",
        f"- Platforms covered: {', '.join(summary['platforms']) if summary['platforms'] else 'none'}",
        "",
        "## Cohorts",
        "",
        "| Cohort | Platform | Drafts | Top Pick Correct | Spearman | Best Match | Biggest Miss |",
        "|---|---|---|---|---|---|---|",
    ]

    if not cohort_results:
        lines.append("| — | — | — | — | — | — | — |")
    else:
        for item in cohort_results:
            lines.append(
                "| {cohort} | {platform} | {size} | {top_hit} | {spearman} | {best} | {miss} |".format(
                    cohort=item["cohort_id"],
                    platform=item["platform"],
                    size=item["size"],
                    top_hit="yes" if item["top_pick_correct"] else "no",
                    spearman=item["spearman"] if item["spearman"] is not None else "n/a",
                    best=item["best_match_label"] or "—",
                    miss=item["biggest_miss_label"] or "—",
                )
            )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `actual_outcome` is operator defined. Use the same measurement inside a cohort.",
            "- Better cohorts compare alternative drafts for the same campaign, offer, or post window.",
            "- This report is strongest when it ranks sibling drafts, not unrelated posts months apart.",
            "",
        ]
    )
    return "\n".join(lines)


def build_report(rows: list[CalibrationRow]) -> dict:
    scored_rows = [_score_row(row) for row in rows]

    cohorts: dict[tuple[str, str], list[dict]] = {}
    for item in scored_rows:
        cohorts.setdefault((item["cohort_id"], item["platform"]), []).append(item)

    cohort_results: list[dict] = []
    all_ranked_rows: list[dict] = []

    for (cohort_id, platform), items in sorted(cohorts.items()):
        _rank_desc(items, "predicted_score")
        _rank_desc(items, "actual_outcome")
        for row in items:
            row["predicted_rank"] = row.pop("predicted_score_rank")
            row["actual_rank"] = row.pop("actual_outcome_rank")
            row["rank_error"] = abs(row["predicted_rank"] - row["actual_rank"])

        best_match = min(items, key=lambda row: row["rank_error"])
        biggest_miss = max(items, key=lambda row: row["rank_error"])
        top_pick = min(items, key=lambda row: row["predicted_rank"])
        actual_top = min(items, key=lambda row: row["actual_rank"])
        spearman = _spearman(items)

        cohort_results.append(
            {
                "cohort_id": cohort_id,
                "platform": platform,
                "size": len(items),
                "top_pick_correct": top_pick["label"] == actual_top["label"],
                "predicted_top_label": top_pick["label"],
                "actual_top_label": actual_top["label"],
                "best_match_label": best_match["label"] if best_match["rank_error"] == 0 else None,
                "biggest_miss_label": biggest_miss["label"] if biggest_miss["rank_error"] > 0 else None,
                "spearman": spearman,
                "rows": items,
            }
        )
        all_ranked_rows.extend(items)

    top_pick_hits = sum(1 for item in cohort_results if item["top_pick_correct"])
    spearman_values = [item["spearman"] for item in cohort_results if item["spearman"] is not None]
    platforms = sorted({row.platform for row in rows})

    summary = {
        "generated_at": _utc_now_iso(),
        "cohort_count": len(cohort_results),
        "draft_count": len(rows),
        "platforms": platforms,
        "top_pick_hits": top_pick_hits,
        "top_pick_accuracy_pct": round((top_pick_hits / len(cohort_results)) * 100, 2) if cohort_results else 0.0,
        "avg_spearman": round(sum(spearman_values) / len(spearman_values), 4) if spearman_values else None,
    }

    return {
        "summary": summary,
        "cohorts": cohort_results,
        "rows": all_ranked_rows,
        "examples": _examples_payload(summary, cohort_results, all_ranked_rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Calibrate ContentForge against historical outcomes.")
    parser.add_argument("--input", required=True, help="CSV or JSON dataset path")
    parser.add_argument("--report-json", default=str(DEFAULT_REPORT_JSON))
    parser.add_argument("--report-md", default=str(DEFAULT_REPORT_MD))
    parser.add_argument("--examples-json", default=str(DEFAULT_EXAMPLES_JSON))
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    rows = _build_rows(_load_records(input_path))
    report = build_report(rows)

    report_json_path = Path(args.report_json).resolve()
    report_md_path = Path(args.report_md).resolve()
    examples_json_path = Path(args.examples_json).resolve()

    report_json_path.parent.mkdir(parents=True, exist_ok=True)
    report_md_path.parent.mkdir(parents=True, exist_ok=True)
    examples_json_path.parent.mkdir(parents=True, exist_ok=True)

    report_json_path.write_text(json.dumps(report, indent=2))
    report_md_path.write_text(_markdown_report(report["summary"], report["cohorts"]))
    examples_json_path.write_text(json.dumps(report["examples"], indent=2))

    print(
        json.dumps(
            {
                "status": "ok",
                "cohorts": report["summary"]["cohort_count"],
                "drafts": report["summary"]["draft_count"],
                "top_pick_accuracy_pct": report["summary"]["top_pick_accuracy_pct"],
                "report_json": str(report_json_path),
                "report_md": str(report_md_path),
                "examples_json": str(examples_json_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
