#!/usr/bin/env python3
"""Sync GitHub issues and milestones into local Markdown mirrors."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = REPO_ROOT.parent
PLAN_PATH = WORKSPACE_ROOT / "docs" / "project_organisation_migration_plan.json"
SYNC_ROOT = REPO_ROOT / "docs" / "dev" / "issues"
SOURCE_DIR = SYNC_ROOT / "_source"
OPEN_DIR = SYNC_ROOT / "mirrored_from_github" / "open"
CLOSED_DIR = SYNC_ROOT / "mirrored_from_github" / "closed"
MILESTONE_DIR = SYNC_ROOT / "mirrored_from_github" / "milestones"
SUMMARY_PATH = SYNC_ROOT / "mirrored_from_github" / "issue_summary_status.md"
CONFIG_CANDIDATES = [
    REPO_ROOT / "configs" / "local" / "github_issue_sync.json",
    REPO_ROOT / ".codex" / "github_issue_sync.json",
]

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print planned writes without writing.")
    return parser.parse_args()

def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

def load_target() -> tuple[str, str] | None:
    owner = os.getenv("GITHUB_OWNER")
    repo = os.getenv("GITHUB_REPO")
    if owner and repo:
        return owner, repo
    for path in CONFIG_CANDIDATES:
        if path.exists():
            data = load_json(path)
            owner = owner or data.get("owner")
            repo = repo or data.get("repo")
            if owner and repo:
                return str(owner), str(repo)
    return None

def run_gh(args: list[str]) -> object:
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "gh command failed")
    return json.loads(proc.stdout or "null")

def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "item"

def priority_label(labels: list[dict]) -> str:
    for label in labels:
        name = str(label.get("name", ""))
        if name.startswith("priority/"):
            return name.split("/", 1)[1]
    return "p3"

def first_paragraph(body: str) -> str:
    for chunk in re.split(r"\n\s*\n", body.strip()):
        text = chunk.strip()
        if text and not text.startswith("##"):
            return text
    return ""

def section(body: str, heading: str) -> str:
    lines = body.splitlines()
    start = None
    for idx, line in enumerate(lines):
        if line.strip().lower() in {f"## {heading}".lower(), f"### {heading}".lower()}:
            start = idx + 1
            break
    if start is None:
        return ""
    end = len(lines)
    for idx in range(start, len(lines)):
        if lines[idx].startswith("## "):
            end = idx
            break
    return "\n".join(lines[start:end]).strip()

def extract_links(body: str) -> str:
    links = []
    for url in re.findall(r"https://[^\s)]+", body):
        if ("github.com" in url and ("/pull/" in url or "/commit/" in url)) or "github.com" not in url:
            if url not in links:
                links.append(url)
    return "\n".join(f"- {url}" for url in links)

def issue_markdown(issue: dict, mirror_fields: list[str]) -> str:
    labels = [str(label.get("name")) for label in issue.get("labels", []) if isinstance(label, dict)]
    milestone = issue.get("milestone") or {}
    body = str(issue.get("body") or "")
    values = {
        "GitHub URL": str(issue.get("url") or ""),
        "issue or milestone number": str(issue.get("number") or ""),
        "title": str(issue.get("title") or ""),
        "labels": ", ".join(labels) or "n/a",
        "milestone": str(milestone.get("title") or "n/a"),
        "status": str(issue.get("state") or "n/a"),
        "summary": first_paragraph(body) or body[:400].strip() or "n/a",
        "acceptance criteria": section(body, "acceptance criteria") or "n/a",
        "implementation notes": section(body, "implementation notes") or "n/a",
        "links to PRs and commits": extract_links(body) or "n/a",
        "closure summary": section(body, "closure summary") or ("Closed on " + str(issue.get("closedAt")) if issue.get("closedAt") else "n/a"),
    }
    header = f"# {issue.get('number')} {issue.get('title')}\n\n"
    return header + "".join(
        f"## {field}\n\n{(values.get(field, 'n/a').strip() or 'n/a')}\n" for field in mirror_fields
    )
def milestone_markdown(milestone: dict, mirror_fields: list[str]) -> str:
    body = str(milestone.get("description") or "")
    values = {
        "GitHub URL": str(milestone.get("html_url") or milestone.get("url") or ""),
        "issue or milestone number": str(milestone.get("number") or ""),
        "title": str(milestone.get("title") or ""),
        "labels": "n/a",
        "milestone": str(milestone.get("title") or "n/a"),
        "status": str(milestone.get("state") or "n/a"),
        "summary": first_paragraph(body) or body[:400].strip() or "n/a",
        "acceptance criteria": "n/a",
        "implementation notes": body or "n/a",
        "links to PRs and commits": "n/a",
        "closure summary": body if milestone.get("state") == "closed" else "n/a",
    }
    header = f"# Milestone {milestone.get('number')}: {milestone.get('title')}\n\n"
    return header + "".join(
        f"## {field}\n\n{(values.get(field, 'n/a').strip() or 'n/a')}\n" for field in mirror_fields
    )
def main() -> int:
    args = parse_args()
    target = load_target()
    if not target:
        print("Set GITHUB_OWNER/GITHUB_REPO or create configs/local/github_issue_sync.json.", file=sys.stderr)
        return 1
    owner, repo = target
    try:
        mirror_fields = load_json(PLAN_PATH)["issue_and_milestone_system"]["mirror_fields"]
        issues = run_gh(["issue", "list", "--repo", f"{owner}/{repo}", "--state", "all", "--limit", "1000", "--json", "number,title,state,url,labels,milestone,body,closedAt"])
        milestones = run_gh(["api", f"repos/{owner}/{repo}/milestones?state=all&per_page=100"])
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    writes: dict[Path, str] = {}
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    OPEN_DIR.mkdir(parents=True, exist_ok=True)
    CLOSED_DIR.mkdir(parents=True, exist_ok=True)
    MILESTONE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    writes[SOURCE_DIR / "github_issues.json"] = json.dumps(issues, indent=2) + "\n"
    writes[SOURCE_DIR / "github_milestones.json"] = json.dumps(milestones, indent=2) + "\n"
    writes[SOURCE_DIR / "sync_state.json"] = json.dumps({"owner": owner, "repo": repo, "last_sync": timestamp}, indent=2) + "\n"
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        dest = CLOSED_DIR if issue.get("state") == "closed" else OPEN_DIR
        file_name = f"{int(issue.get('number', 0)):04d}_{priority_label(issue.get('labels', []))}_{slugify(str(issue.get('title') or 'issue'))}.md"
        writes[dest / file_name] = issue_markdown(issue, mirror_fields)
    for milestone in milestones:
        if not isinstance(milestone, dict):
            continue
        file_name = f"{int(milestone.get('number', 0)):02d}_Milestone_{slugify(str(milestone.get('title') or 'milestone')).title().replace('-', '')}.md"
        writes[MILESTONE_DIR / file_name] = milestone_markdown(milestone, mirror_fields)
    writes[SUMMARY_PATH] = (
        f"# {repo} Issue Summary Status\n\n"
        f"Status date: {timestamp[:10]}\n\n"
        f"## Open Issues\n{len([i for i in issues if isinstance(i, dict) and i.get('state') == 'open'])} issues mirrored.\n\n"
        f"## Milestones\n{len([m for m in milestones if isinstance(m, dict)])} milestones mirrored.\n\n"
        f"## Notes\nUpdated from GitHub on demand.\n"
    )
    if args.dry_run:
        print(f"dry-run: {len(writes)} files would be written for {owner}/{repo}")
        for path in sorted(writes):
            print(path.relative_to(REPO_ROOT))
        return 0
    for path, content in writes.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    print(f"synced {len(issues)} issues and {len(milestones)} milestones for {owner}/{repo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
