"""Regression checks for the calibration harness."""

from scripts.calibrate_content import CalibrationRow, build_report


def assert_true(value, message):
    if not value:
        raise AssertionError(message)


def main():
    rows = [
        CalibrationRow(
            cohort_id="tweet_launch",
            platform="tweet",
            text="Built a scoring API in 48 hours. $500 last month. Here is what changed.",
            actual_outcome=220.0,
            label="tweet_a",
            post_url="",
            notes="",
            raw={"platform": "tweet"},
        ),
        CalibrationRow(
            cohort_id="tweet_launch",
            platform="tweet",
            text="Working on something cool today.",
            actual_outcome=40.0,
            label="tweet_b",
            post_url="",
            notes="",
            raw={"platform": "tweet"},
        ),
        CalibrationRow(
            cohort_id="headline_test",
            platform="headline",
            text="7 landing page headline fixes that lifted demo requests 32%",
            actual_outcome=130.0,
            label="headline_a",
            post_url="",
            notes="",
            raw={"platform": "headline"},
        ),
        CalibrationRow(
            cohort_id="headline_test",
            platform="headline",
            text="Tips for better landing pages",
            actual_outcome=55.0,
            label="headline_b",
            post_url="",
            notes="",
            raw={"platform": "headline"},
        ),
    ]

    report = build_report(rows)

    assert_true(report["summary"]["cohort_count"] == 2, "should produce two cohorts")
    assert_true(report["summary"]["draft_count"] == 4, "should keep all drafts")
    assert_true(report["summary"]["top_pick_accuracy_pct"] == 100.0, "fixture should rank winners correctly")
    assert_true(len(report["examples"]["examples"]) >= 2, "fixture should surface proof examples")
    assert_true(report["cohorts"][0]["rows"][0]["predicted_rank"] >= 1, "rows should include ranks")

    print("calibration harness checks passed")


if __name__ == "__main__":
    main()
