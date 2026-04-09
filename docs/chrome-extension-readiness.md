# ContentForge Chrome Extension Readiness

Updated: 2026-04-09

## Audit Read

The extension is close enough to submit and defend, but the store story needs to stay narrow and precise:

1. Single purpose must stay obvious: score draft copy before publishing.
2. Permission scope must stay minimal and justified.
3. Store text must avoid claims that sound broader than the shipped product.
4. Privacy story must be one click away from the listing and the popup.

## What Was Tightened

- Removed the extra `tabs` permission from the manifest.
- Added direct Privacy, Support, and Report links in the popup footer.
- Rewrote the store listing copy around one job: score drafts before publish.
- Added a calibration harness so proof claims can be backed with public examples.

## Reviewer Talking Points

Single purpose:
- ContentForge scores user written draft copy before the user publishes it.
- The extension shows a live score on supported composer surfaces and a popup scorer on any page.
- The rewrite action is attached to that same purpose. It improves weak drafts after scoring.

Permissions:
- `storage`: stores rewrite history locally and caches extension settings.
- Host access to `https://contentforge-api-lpp9.onrender.com/*`: sends only the text the user chooses to score.
- Content scripts run only on supported compose surfaces: X, LinkedIn, Instagram, Threads, Facebook.

Data handling:
- No account required.
- No analytics or ad trackers.
- Local rewrite history stays in `chrome.storage.local`.
- The API should discard scored text after processing, as stated in `privacy.html`.

## Remaining Human Tasks

1. Upload clean store screenshots that show:
   - live badge on a supported composer
   - popup score breakdown
   - rewrite flow
2. Keep the short description literal and modest.
3. Keep privacy and support URLs working during review.
4. If review asks why scoring happens on multiple sites, answer with the same single purpose: before publish quality scoring on supported composer surfaces.

## Useful Official References

- Permission warning guidance: [developer.chrome.com/docs/extensions/develop/concepts/permission-warnings](https://developer.chrome.com/docs/extensions/develop/concepts/permission-warnings)
- Store troubleshooting and excessive permissions notes: [developer.chrome.com/docs/webstore/troubleshooting](https://developer.chrome.com/docs/webstore/troubleshooting)
