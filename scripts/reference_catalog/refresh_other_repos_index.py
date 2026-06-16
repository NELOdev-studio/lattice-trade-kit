#!/usr/bin/env python3
"""Refresh the structured reference snapshot for `other_repos/`.

The script searches GitHub for trading bot, strategy, broker, backtest, and
market-data projects, merges those discoveries with any existing local
reference entries already captured in
`reference_catalog_repo/sources/other_repos/raw_index.json`, and writes a
single consolidated raw snapshot.

The generated catalog is designed to be easy for AI agents to consume:

- compact but structured metadata
- a small set of canonical capability tags
- explicit notes about how each project may help TradeCore
- optional local-clone awareness, so deep inspection stays cheap

The script uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
from urllib.request import Request, urlopen


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
OTHER_REPOS_DIR = WORKSPACE_ROOT / "other_repos"
CATALOG_REPO_DIR = WORKSPACE_ROOT / "reference_catalog_repo"
OTHER_REPOS_SOURCE_DIR = CATALOG_REPO_DIR / "sources" / "other_repos"
INDEX_PATH = OTHER_REPOS_SOURCE_DIR / "raw_index.json"
DEFAULT_MAX_PROJECTS = 100
DEFAULT_SEARCH_LIMIT = 100
DEFAULT_README_LIMIT = 12
GITHUB_API = "https://api.github.com"


SEARCH_QUERIES: list[dict[str, str]] = [
    {"query": "oanda", "bucket": "oanda"},
    {"query": "oanda api", "bucket": "oanda"},
    {"query": "oanda api python", "bucket": "oanda"},
    {"query": "oanda trading bot", "bucket": "oanda"},
    {"query": "oanda python", "bucket": "oanda"},
    {"query": "oanda v20", "bucket": "oanda"},
    {"query": "oanda v20 python", "bucket": "oanda"},
    {"query": "oanda backtest", "bucket": "oanda"},
    {"query": "oanda data", "bucket": "oanda"},
    {"query": "oanda wrapper", "bucket": "oanda"},
    {"query": "oanda adapter", "bucket": "oanda"},
    {"query": "oandapy", "bucket": "oanda"},
    {"query": "oanda strategy", "bucket": "oanda"},
    {"query": "oanda dashboard", "bucket": "oanda"},
    {"query": "forex trading bot", "bucket": "forex"},
    {"query": "forex strategy", "bucket": "forex"},
    {"query": "forex trading system", "bucket": "forex"},
    {"query": "fx trading bot python", "bucket": "forex"},
    {"query": "forex backtesting python", "bucket": "forex"},
    {"query": "forex risk management", "bucket": "forex"},
    {"query": "algorithmic trading bot", "bucket": "general_trading"},
    {"query": "algorithmic trading framework", "bucket": "framework"},
    {"query": "trading strategy backtest", "bucket": "framework"},
    {"query": "backtrader strategy", "bucket": "framework"},
    {"query": "vectorbt trading", "bucket": "framework"},
    {"query": "trade execution engine", "bucket": "framework"},
    {"query": "paper trading bot", "bucket": "ops"},
    {"query": "trading dashboard", "bucket": "ops"},
    {"query": "market data collector trading", "bucket": "data"},
    {"query": "mcp trading agent", "bucket": "agent"},
    {"query": "ai trading agent", "bucket": "agent"},
    {"query": "risk management trading", "bucket": "framework"},
    {"query": "market making bot", "bucket": "framework"},
]


KEYWORD_CAPABILITIES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\boanda\b", re.I), "OANDA integration"),
    (re.compile(r"\bforex\b|\bfx\b", re.I), "forex trading"),
    (re.compile(r"\bcrypto\b|\bbitcoin\b|\bethereum\b", re.I), "crypto trading"),
    (re.compile(r"\bbacktest|\bbacktesting\b", re.I), "backtesting"),
    (re.compile(r"\bstrategy\b", re.I), "strategy layer"),
    (re.compile(r"\brisk\b", re.I), "risk management"),
    (re.compile(r"\bdashboard\b|\bmonitor\b|\bcontrol room\b", re.I), "monitoring UI"),
    (re.compile(r"\bmcp\b", re.I), "agent tool server"),
    (re.compile(r"\btelegram\b|\bslack\b|\bdiscord\b", re.I), "operator alerts"),
    (re.compile(r"\bdata collector\b|\bingest|\bfeed\b|\bstream\b", re.I), "market data ingestion"),
    (re.compile(r"\bpaper\b|\bsimulation\b", re.I), "paper-trading mode"),
    (re.compile(r"\bexecution\b|\border\b|\bbroker\b", re.I), "execution layer"),
]


TRADECORE_NOTE_MAP: dict[str, list[str]] = {
    "oanda": [
        "Use as an OANDA adapter or request/response naming reference for `src/tradecore/adapters/oanda/`.",
        "Good for checking broker-domain boundaries around accounts, prices, orders, trades, and transactions.",
    ],
    "forex": [
        "Useful for forex-specific strategy, session, and pair-selection ideas.",
        "Can inform risk gates, indicator tuning, or multi-pair orchestration in `tradecore/strategies/`.",
    ],
    "crypto": [
        "Useful for execution, signals, and lifecycle patterns even if the broker differs from OANDA.",
        "Can inspire live monitoring or automation patterns for `tradecore-private/` experiments.",
    ],
    "framework": [
        "Useful for architecture ideas around backtesting, execution, and pluggable strategy boundaries.",
        "Can help shape `core/`, `strategies/`, `risk/`, and `execution/` seams in TradeCore.",
    ],
    "ops": [
        "Useful for operator control, paper-trading, alerting, or execution supervision patterns.",
        "Can inform `apps/dashboard/` and runtime monitoring flows.",
    ],
    "data": [
        "Useful for market-data ingestion, caching, persistence, and provenance logging patterns.",
        "Can inform `market_data/` and research-note workflows.",
    ],
    "agent": [
        "Useful for agent tooling, tool-server boundaries, or model-facing API surfaces.",
        "Can inform private experiments around AI-mediated decision support.",
    ],
    "research": [
        "Useful for report layouts, experiment summaries, and parameter-sweep presentation.",
        "Can support research-note templates and publishable analysis artifacts.",
    ],
    "general": [
        "Useful as a broad algorithmic-trading reference.",
        "Worth mining for small architectural or operational patterns that fit TradeCore.",
    ],
}


BUCKET_TO_KIND: dict[str, str] = {
    "oanda": "oanda_reference",
    "forex": "forex_bot_or_strategy",
    "crypto": "crypto_bot_or_strategy",
    "framework": "trading_framework",
    "ops": "ops_and_control",
    "data": "data_pipeline",
    "agent": "agent_tooling",
    "research": "research_artifact",
    "general_trading": "general_trading",
    "general": "general_trading",
}


@dataclass(slots=True)
class RepoCandidate:
    """Normalized GitHub repository candidate."""

    full_name: str
    name: str
    owner: str
    html_url: str
    description: str
    language: str | None
    stars: int
    forks: int
    score: float
    fork: bool
    archived: bool
    default_branch: str | None
    local_path: str | None = None
    query_hits: list[str] = field(default_factory=list)
    bucket_hits: list[str] = field(default_factory=list)

    @property
    def repo_id(self) -> str:
        return self.full_name.replace("/", "__")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search GitHub and refresh the structured reference index."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=INDEX_PATH,
        help="Path to the raw snapshot JSON to write.",
    )
    parser.add_argument(
        "--max-projects",
        type=int,
        default=DEFAULT_MAX_PROJECTS,
        help="Maximum number of projects to keep in the final catalog.",
    )
    parser.add_argument(
        "--search-limit",
        type=int,
        default=DEFAULT_SEARCH_LIMIT,
        help="Max results to request per GitHub search query.",
    )
    parser.add_argument(
        "--readme-limit",
        type=int,
        default=DEFAULT_README_LIMIT,
        help="Reserved for future README enrichment. Currently used as a note in the catalog.",
    )
    parser.add_argument(
        "--clone-top",
        type=int,
        default=0,
        help="Optionally clone the top N remote repos into other_repos/.",
    )
    parser.add_argument(
        "--github-token",
        default=os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN"),
        help="Optional GitHub token for higher API limits.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip GitHub search and rebuild the raw snapshot from the existing raw index only.",
    )
    return parser.parse_args(argv)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
        handle.write("\n")


def http_get_json(url: str, token: str | None = None) -> dict[str, Any]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "tradecore-reference-catalog/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, headers=headers)
    with urlopen(request, timeout=45) as response:
        data = response.read().decode("utf-8")
    return json.loads(data)


def search_repositories(query: str, limit: int, token: str | None) -> list[dict[str, Any]]:
    url = (
        f"{GITHUB_API}/search/repositories?"
        f"q={quote_plus(query)}&sort=stars&order=desc&per_page={limit}&page=1"
    )
    payload = http_get_json(url, token=token)
    items = payload.get("items", [])
    if not isinstance(items, list):
        return []
    return items


def read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def local_clone_path(repo_name: str) -> str | None:
    direct = OTHER_REPOS_DIR / repo_name
    if direct.exists():
        return str(direct.relative_to(WORKSPACE_ROOT))

    for child in OTHER_REPOS_DIR.iterdir():
        if child.is_dir() and child.name == repo_name:
            return str(child.relative_to(WORKSPACE_ROOT))
    return None


def build_text_blob(candidate: RepoCandidate) -> str:
    parts = [
        candidate.full_name,
        candidate.name,
        candidate.description,
        candidate.language or "",
    ]
    return " ".join(part for part in parts if part).lower()


def contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def has_forex_context(text: str) -> bool:
    return contains_any(text, ["forex", "fx", "eurusd", "gbpusd", "usdjpy"])


def has_generic_crypto_context(text: str) -> bool:
    return contains_any(
        text,
        [
            "crypto",
            "cryptocurrency",
            "bitcoin",
            "ethereum",
            "binance",
            "ccxt",
            "freqtrade",
            "hummingbot",
            "solana",
            "coinbase",
        ],
    )


def keyword_capabilities(text: str) -> list[str]:
    caps: list[str] = []
    for pattern, label in KEYWORD_CAPABILITIES:
        if pattern.search(text) and label not in caps:
            caps.append(label)
    return caps[:5]


def classify_bucket(text: str) -> str:
    if "oanda" in text:
        return "oanda"
    if any(term in text for term in ["forex", "fx", "eurusd", "gbpusd", "usdjpy"]):
        return "forex"
    if any(term in text for term in ["crypto", "bitcoin", "ethereum", "binance", "ccxt"]):
        return "crypto"
    if any(term in text for term in ["backtest", "backtesting", "framework", "engine", "lean", "vectorbt", "backtrader", "freqtrade"]):
        return "framework"
    if any(term in text for term in ["dashboard", "monitor", "telegram", "discord", "paper", "simulation", "ops", "control"]):
        return "ops"
    if any(term in text for term in ["collector", "ingest", "pipeline", "feed", "stream", "data"]):
        return "data"
    if "mcp" in text or "agent" in text:
        return "agent"
    if any(term in text for term in ["report", "research", "analysis", "experiment", "journal"]):
        return "research"
    return "general"


def score_candidate(candidate: RepoCandidate, is_local: bool, existing_bonus: float = 0.0) -> float:
    text = build_text_blob(candidate)
    is_oanda = "oanda" in text
    is_forex = has_forex_context(text)
    is_crypto = has_generic_crypto_context(text)
    score = float(candidate.score) * 10.0
    score += math.log10(candidate.stars + 1.0) * 18.0
    score += math.log10(candidate.forks + 1.0) * 5.0
    score += existing_bonus

    for pattern, _label in KEYWORD_CAPABILITIES:
        if pattern.search(text):
            score += 10.0

    if "oanda" in candidate.name.lower() or "oanda" in candidate.full_name.lower():
        score += 45.0
    if "oanda" in candidate.description.lower():
        score += 30.0
    if "oanda" in candidate.bucket_hits:
        score += 25.0
    if is_oanda:
        score += 85.0
        if contains_any(text, ["api", "sdk", "v20", "rest", "client", "wrapper", "adapter", "library"]):
            score += 32.0
        if contains_any(text, ["account", "instrument", "order", "pricing", "trade", "transaction", "position", "candle", "candles"]):
            score += 24.0
        if contains_any(text, ["dashboard", "monitor", "backtest", "data", "strategy", "bot"]):
            score += 18.0
    if is_forex:
        score += 34.0
    if "trading" in text:
        score += 16.0
    if "bot" in text:
        score += 14.0
    if "strategy" in text:
        score += 12.0
    if "backtest" in text:
        score += 16.0
    if contains_any(text, ["execution", "broker", "adapter"]):
        score += 14.0
    if "risk" in text:
        score += 12.0
    if contains_any(text, ["dashboard", "monitor", "control room"]):
        score += 12.0
    if contains_any(text, ["collector", "ingest", "feed", "stream", "pipeline"]):
        score += 14.0
    if "mcp" in text:
        score += 20.0
    if "agent" in text:
        score += 14.0
    if contains_any(text, ["paper", "simulation"]):
        score += 10.0
    if contains_any(text, ["report", "research", "analysis", "experiment", "journal"]):
        score += 10.0
    if is_crypto and not is_oanda and not is_forex:
        score -= 85.0
    elif is_crypto and not is_oanda:
        score -= 35.0
    if "crypto" in candidate.bucket_hits and not is_oanda and not is_forex:
        score -= 45.0
    if is_local:
        score += 40.0
    if candidate.fork:
        score -= 15.0
    if candidate.archived:
        score -= 6.0
    return score


def clean_description(description: str) -> str:
    desc = " ".join(description.split())
    if not desc:
        return "No repository description was provided."
    return desc.rstrip(".")


def build_summary(description: str, bucket: str, capabilities: list[str]) -> str:
    base = clean_description(description)
    suffix_map = {
        "oanda": "Best used as an OANDA-specific integration or adapter reference.",
        "forex": "Useful for forex strategy, session, or pair-management ideas.",
        "crypto": "Useful for exchange-agnostic execution and trading-loop patterns.",
        "framework": "Useful for backtesting, execution, and strategy-boundary ideas.",
        "ops": "Useful for dashboards, alerts, and operator-control patterns.",
        "data": "Useful for market-data ingestion and provenance patterns.",
        "agent": "Useful for agent-tool surface and decision-guardrail patterns.",
        "research": "Useful for research-report and experiment-layout patterns.",
        "general": "Useful as a broad algorithmic-trading reference.",
    }
    suffix = suffix_map.get(bucket, suffix_map["general"])
    capability_tail = ""
    if capabilities:
        capability_tail = f" Key signals: {', '.join(capabilities[:3])}."
    return f"{base} {suffix}{capability_tail}".strip()


def build_tradecore_notes(bucket: str, capabilities: list[str], is_local: bool) -> list[str]:
    notes = list(TRADECORE_NOTE_MAP.get(bucket, TRADECORE_NOTE_MAP["general"]))
    if is_local:
        notes.insert(0, "Already cloned in the workspace, so it is cheap to inspect in detail.")
    if capabilities:
        notes.append(f"High-signal tags: {', '.join(capabilities[:3])}.")
    return notes[:3]


def infer_existing_bucket(entry: dict[str, Any]) -> str:
    kind = entry.get("kind")
    if isinstance(kind, str):
        kind_lower = kind.lower()
        if any(term in kind_lower for term in ["report", "research"]):
            return "research"
        if any(term in kind_lower for term in ["dashboard", "ops", "control", "monitor"]):
            return "ops"
        if "data" in kind_lower:
            return "data"
        if any(term in kind_lower for term in ["agent", "tool", "mcp"]):
            return "agent"
        if "forex" in kind_lower:
            return "forex"
        if "crypto" in kind_lower:
            return "crypto"

    signals = entry.get("signals") if isinstance(entry.get("signals"), dict) else {}
    bucket = signals.get("bucket") if isinstance(signals, dict) else None
    if isinstance(bucket, str) and bucket in BUCKET_TO_KIND and bucket not in {"general", "general_trading"}:
        return bucket

    parts: list[str] = []
    for key in ("id", "name", "kind", "summary", "description"):
        value = entry.get(key)
        if isinstance(value, str):
            parts.append(value)
    capabilities = entry.get("capabilities")
    if isinstance(capabilities, list):
        parts.extend(str(item) for item in capabilities if isinstance(item, str))
    return classify_bucket(" ".join(parts).lower())


def candidate_from_existing_entry(entry: dict[str, Any]) -> tuple[RepoCandidate, str, str | None]:
    entry_id = str(entry.get("id") or "").strip()
    path = entry.get("path")
    repo_name = ""
    if isinstance(path, str) and path.strip():
        repo_name = Path(path).name
    if not repo_name:
        name_value = entry.get("name")
        if isinstance(name_value, str) and name_value.strip():
            repo_name = name_value.strip()
    if not repo_name:
        repo_name = entry_id or "unknown"

    local_path = local_clone_path(repo_name)
    bucket = infer_existing_bucket(entry)
    signals = entry.get("signals") if isinstance(entry.get("signals"), dict) else {}
    metrics = entry.get("metrics") if isinstance(entry.get("metrics"), dict) else {}

    candidate = RepoCandidate(
        full_name=str(entry.get("github_full_name") or entry_id or repo_name),
        name=repo_name,
        owner=str(entry.get("owner") or "local"),
        html_url=str(entry.get("github_url") or f"https://example.invalid/{repo_name}"),
        description=str(entry.get("description") or entry.get("summary") or repo_name),
        language=str(entry.get("language")) if isinstance(entry.get("language"), str) else None,
        stars=int(metrics.get("stars", 0)),
        forks=int(metrics.get("forks", 0)),
        score=float(metrics.get("github_score", 0.0)),
        fork=bool(signals.get("fork", False)),
        archived=bool(signals.get("archived", False)),
        default_branch=str(entry.get("default_branch")) if isinstance(entry.get("default_branch"), str) else None,
        local_path=local_path,
        query_hits=["existing_index"],
        bucket_hits=[bucket],
    )
    return candidate, bucket, local_path


def existing_project_map(existing_index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for entry in existing_index.get("projects", []):
        if not isinstance(entry, dict):
            continue
        entry_id = entry.get("id")
        if isinstance(entry_id, str):
            mapping[entry_id] = entry
        path = entry.get("path")
        if isinstance(path, str):
            mapping.setdefault(Path(path).name, entry)
    return mapping


def build_catalog_from_existing(existing_index: dict[str, Any], args: argparse.Namespace, source_label: str) -> dict[str, Any]:
    existing_projects = existing_index.get("projects", [])
    curated_entries: list[dict[str, Any]] = []
    bucket_index: dict[str, list[str]] = {}

    if isinstance(existing_projects, list):
        for entry in existing_projects:
            if not isinstance(entry, dict):
                continue
            candidate, bucket, local_path = candidate_from_existing_entry(entry)
            built_entry = build_entry(
                candidate=candidate,
                bucket=bucket,
                rank=len(curated_entries) + 1,
                local_local_path=local_path,
                existing_entry=entry,
                source_queries=[source_label],
            )
            curated_entries.append(built_entry)
            bucket_index.setdefault(bucket, []).append(str(built_entry.get("id")))
            if len(curated_entries) >= args.max_projects:
                break

    stats = {
        "selected_projects": len(curated_entries),
        "local_clones": sum(1 for entry in curated_entries if entry.get("path")),
        "remote_only": sum(1 for entry in curated_entries if not entry.get("path")),
        "oanda_related": len(bucket_index.get("oanda", [])),
        "forex_related": len(bucket_index.get("forex", [])),
        "crypto_related": len(bucket_index.get("crypto", [])),
        "framework_related": len(bucket_index.get("framework", [])),
        "ops_related": len(bucket_index.get("ops", [])),
        "data_related": len(bucket_index.get("data", [])),
        "agent_related": len(bucket_index.get("agent", [])),
        "research_related": len(bucket_index.get("research", [])),
        "general_trading_related": len(bucket_index.get("general_trading", bucket_index.get("general", []))),
        "existing_local_entries": len(existing_projects) if isinstance(existing_projects, list) else 0,
        "search_queries": 0,
        "search_limit": 0,
        "readme_limit": args.readme_limit,
    }

    topic_index = {
        "oanda_reference": bucket_index.get("oanda", []),
        "forex_bot_or_strategy": bucket_index.get("forex", []),
        "crypto_bot_or_strategy": bucket_index.get("crypto", []),
        "trading_framework": bucket_index.get("framework", []),
        "ops_and_control": bucket_index.get("ops", []),
        "data_pipeline": bucket_index.get("data", []),
        "agent_tooling": bucket_index.get("agent", []),
        "research_artifact": bucket_index.get("research", []),
        "general_trading": bucket_index.get("general_trading", bucket_index.get("general", [])),
    }

    return {
        "generated_at": time.strftime("%Y-%m-%d"),
        "workspace_root": str(WORKSPACE_ROOT),
        "purpose": "High-signal summary of trading, bot, framework, and OANDA-related reference repositories for AI agents.",
        "scope": "Raw snapshot under reference_catalog_repo/sources/other_repos/",
        "source": {
            "type": source_label,
            "queries": [],
            "max_projects": args.max_projects,
            "search_limit_per_query": 0,
            "readme_limit": args.readme_limit,
        },
        "stats": stats,
        "topic_index": topic_index,
        "projects": curated_entries,
        "notes": [
            "This offline refresh preserves the current catalog and reclassifies entries using the latest local heuristics.",
            "Run without --offline to rebuild the catalog from GitHub search results.",
        ],
        "query_log": [],
    }


def normalize_search_item(item: dict[str, Any], query: str, bucket: str) -> RepoCandidate | None:
    full_name = str(item.get("full_name") or "").strip()
    name = str(item.get("name") or "").strip()
    owner_data = item.get("owner") if isinstance(item.get("owner"), dict) else {}
    owner = str(owner_data.get("login") or "").strip()
    html_url = str(item.get("html_url") or "").strip()
    description = str(item.get("description") or "").strip()
    language = item.get("language")
    if isinstance(language, str) and not language.strip():
        language = None
    stars = int(item.get("stargazers_count") or 0)
    forks = int(item.get("forks_count") or 0)
    score = float(item.get("score") or 0.0)
    fork = bool(item.get("fork") or False)
    archived = bool(item.get("archived") or False)
    default_branch = item.get("default_branch")
    if isinstance(default_branch, str) and not default_branch.strip():
        default_branch = None
    local_path = local_clone_path(name)
    if not full_name or not name or not owner or not html_url:
        return None
    return RepoCandidate(
        full_name=full_name,
        name=name,
        owner=owner,
        html_url=html_url,
        description=description,
        language=language if isinstance(language, str) else None,
        stars=stars,
        forks=forks,
        score=score,
        fork=fork,
        archived=archived,
        default_branch=default_branch if isinstance(default_branch, str) else None,
        local_path=local_path,
        query_hits=[query],
        bucket_hits=[bucket],
    )


def merge_candidate(existing: RepoCandidate, incoming: RepoCandidate) -> RepoCandidate:
    merged = RepoCandidate(
        full_name=existing.full_name or incoming.full_name,
        name=existing.name or incoming.name,
        owner=existing.owner or incoming.owner,
        html_url=existing.html_url or incoming.html_url,
        description=existing.description or incoming.description,
        language=existing.language or incoming.language,
        stars=max(existing.stars, incoming.stars),
        forks=max(existing.forks, incoming.forks),
        score=max(existing.score, incoming.score),
        fork=existing.fork or incoming.fork,
        archived=existing.archived or incoming.archived,
        default_branch=existing.default_branch or incoming.default_branch,
        local_path=existing.local_path or incoming.local_path,
        query_hits=sorted(set(existing.query_hits + incoming.query_hits)),
        bucket_hits=sorted(set(existing.bucket_hits + incoming.bucket_hits)),
    )
    return merged


def repo_identifier(candidate: RepoCandidate) -> str:
    if candidate.local_path:
        return candidate.name
    return candidate.repo_id


def build_entry(
    candidate: RepoCandidate,
    bucket: str,
    rank: int,
    local_local_path: str | None,
    existing_entry: dict[str, Any] | None,
    source_queries: list[str],
) -> dict[str, Any]:
    text = build_text_blob(candidate)
    capabilities = keyword_capabilities(text)
    if existing_entry and isinstance(existing_entry.get("capabilities"), list):
        preserved_caps = [str(item) for item in existing_entry["capabilities"] if isinstance(item, str)]
        for cap in preserved_caps:
            if cap not in capabilities:
                capabilities.append(cap)
    summary = existing_entry.get("summary") if isinstance(existing_entry, dict) else None
    if not isinstance(summary, str) or not summary.strip():
        summary = build_summary(candidate.description, bucket, capabilities)

    tradecore_notes = existing_entry.get("tradecore_usefulness") if isinstance(existing_entry, dict) else None
    if not isinstance(tradecore_notes, list) or not tradecore_notes:
        tradecore_notes = build_tradecore_notes(bucket, capabilities, bool(local_local_path))
    else:
        tradecore_notes = [str(item) for item in tradecore_notes if isinstance(item, str)]

    caveats = existing_entry.get("caveats") if isinstance(existing_entry, dict) else None
    if not isinstance(caveats, list) or not caveats:
        caveats = []
        if candidate.archived:
            caveats.append("Archived upstream; treat as a historical reference.")
        if candidate.fork:
            caveats.append("Forked repository; verify original upstream context before reuse.")
        if not local_local_path:
            caveats.append("Remote-only entry; clone locally if deeper inspection is needed.")
    else:
        caveats = [str(item) for item in caveats if isinstance(item, str)]

    source_url = candidate.html_url
    project_entry = {
        "id": repo_identifier(candidate),
        "github_full_name": candidate.full_name,
        "github_url": candidate.html_url,
        "name": candidate.name,
        "owner": candidate.owner,
        "path": local_local_path,
        "kind": existing_entry.get("kind") if isinstance(existing_entry, dict) and existing_entry.get("kind") else BUCKET_TO_KIND[bucket],
        "status": existing_entry.get("status") if isinstance(existing_entry, dict) and existing_entry.get("status") else (
            "local_reference" if local_local_path else ("archived_reference" if candidate.archived else "github_reference")
        ),
        "summary": summary,
        "capabilities": capabilities[:6],
        "tradecore_usefulness": tradecore_notes[:3],
        "caveats": caveats[:3],
        "stack": [candidate.language] if candidate.language else [],
        "language": candidate.language,
        "description": clean_description(candidate.description),
        "metrics": {
            "stars": candidate.stars,
            "forks": candidate.forks,
            "github_score": round(candidate.score, 3),
            "relevance_score": round(score_candidate(candidate, bool(local_local_path)), 3),
            "rank": rank,
        },
        "signals": {
            "bucket": bucket,
            "queries": source_queries,
            "local_clone": bool(local_local_path),
            "archived": candidate.archived,
            "fork": candidate.fork,
        },
        "evidence_files": existing_entry.get("evidence_files") if isinstance(existing_entry, dict) and isinstance(existing_entry.get("evidence_files"), list) else [],
        "source": {
            "type": "local_clone" if local_local_path else "github_search",
            "url": source_url,
            "readme_limit": DEFAULT_README_LIMIT,
        },
    }
    if candidate.default_branch:
        project_entry["default_branch"] = candidate.default_branch
    if candidate.local_path:
        project_entry["local_path"] = candidate.local_path
    return project_entry


def maybe_clone_repo(candidate: RepoCandidate, target_root: Path) -> None:
    target = target_root / candidate.name
    if target.exists():
        return
    target_root.mkdir(parents=True, exist_ok=True)
    cmd = ["git", "clone", "--depth", "1", candidate.html_url, str(target)]
    subprocess.run(cmd, check=False)


def build_catalog(args: argparse.Namespace) -> dict[str, Any]:
    existing_index = load_json(INDEX_PATH)
    existing_map = existing_project_map(existing_index)
    existing_projects = existing_index.get("projects", [])
    existing_count = len(existing_projects) if isinstance(existing_projects, list) else 0

    if args.offline:
        return build_catalog_from_existing(existing_index, args, source_label="existing_index_offline")

    candidates_by_id: dict[str, RepoCandidate] = {}
    query_log: list[dict[str, Any]] = []

    for query_cfg in SEARCH_QUERIES:
        query = query_cfg["query"]
        bucket = query_cfg["bucket"]
        query_log.append({"query": query, "bucket": bucket})
        try:
            results = search_repositories(query, args.search_limit, args.github_token)
        except Exception as exc:  # pragma: no cover - network-dependent path
            query_log[-1]["error"] = str(exc)
            continue

        for item in results:
            candidate = normalize_search_item(item, query=query, bucket=bucket)
            if candidate is None:
                continue
            candidate_id = candidate.repo_id
            if candidate_id in candidates_by_id:
                candidates_by_id[candidate_id] = merge_candidate(candidates_by_id[candidate_id], candidate)
            else:
                candidates_by_id[candidate_id] = candidate

        time.sleep(0.7)

    if not candidates_by_id:
        return build_catalog_from_existing(existing_index, args, source_label="existing_index_fallback")

    # Add local reference entries even if the search query did not surface them.
    for entry in existing_projects if isinstance(existing_projects, list) else []:
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        repo_name = None
        if isinstance(path, str) and path:
            repo_name = Path(path).name
        if not repo_name:
            entry_id = entry.get("id")
            if isinstance(entry_id, str):
                repo_name = entry_id
        if not repo_name:
            continue
        local_path = local_clone_path(repo_name)
        if not local_path:
            continue
        existing_candidate = RepoCandidate(
            full_name=str(entry.get("github_full_name") or repo_name),
            name=repo_name,
            owner=str(entry.get("owner") or "local"),
            html_url=str(entry.get("github_url") or f"https://example.invalid/{repo_name}"),
            description=str(entry.get("description") or entry.get("summary") or repo_name),
            language=str(entry.get("language")) if isinstance(entry.get("language"), str) else None,
            stars=int(entry.get("metrics", {}).get("stars", 0)) if isinstance(entry.get("metrics"), dict) else 0,
            forks=int(entry.get("metrics", {}).get("forks", 0)) if isinstance(entry.get("metrics"), dict) else 0,
            score=float(entry.get("metrics", {}).get("github_score", 0.0)) if isinstance(entry.get("metrics"), dict) else 0.0,
            fork=bool(entry.get("signals", {}).get("fork", False)) if isinstance(entry.get("signals"), dict) else False,
            archived=bool(entry.get("signals", {}).get("archived", False)) if isinstance(entry.get("signals"), dict) else False,
            default_branch=str(entry.get("default_branch")) if isinstance(entry.get("default_branch"), str) else None,
            local_path=local_path,
            query_hits=["existing_index"],
            bucket_hits=[infer_existing_bucket(entry)],
        )
        candidates_by_id.setdefault(existing_candidate.repo_id, existing_candidate)

    # Always preserve the existing curated local entries first, then fill the rest with new finds.
    curated_entries: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for entry in existing_projects if isinstance(existing_projects, list) else []:
        if not isinstance(entry, dict):
            continue
        entry_id = str(entry.get("id") or "").strip()
        if not entry_id or entry_id in seen_ids:
            continue
        path = entry.get("path")
        repo_name = Path(path).name if isinstance(path, str) and path else entry_id
        local_path = local_clone_path(repo_name)
        if not local_path:
            # Keep remote-only entries only if they were already curated and we still have room.
            continue
        candidate = candidates_by_id.get(entry_id) or candidates_by_id.get(repo_name.replace("/", "__"))
        if not candidate:
            bucket = infer_existing_bucket(entry)
            candidate = RepoCandidate(
                full_name=str(entry.get("github_full_name") or entry_id),
                name=repo_name,
                owner=str(entry.get("owner") or "local"),
                html_url=str(entry.get("github_url") or f"https://example.invalid/{repo_name}"),
                description=str(entry.get("description") or entry.get("summary") or repo_name),
                language=str(entry.get("language")) if isinstance(entry.get("language"), str) else None,
                stars=int(entry.get("metrics", {}).get("stars", 0)) if isinstance(entry.get("metrics"), dict) else 0,
                forks=int(entry.get("metrics", {}).get("forks", 0)) if isinstance(entry.get("metrics"), dict) else 0,
                score=float(entry.get("metrics", {}).get("github_score", 0.0)) if isinstance(entry.get("metrics"), dict) else 0.0,
                fork=bool(entry.get("signals", {}).get("fork", False)) if isinstance(entry.get("signals"), dict) else False,
                archived=bool(entry.get("signals", {}).get("archived", False)) if isinstance(entry.get("signals"), dict) else False,
                default_branch=str(entry.get("default_branch")) if isinstance(entry.get("default_branch"), str) else None,
                local_path=local_path,
                query_hits=["existing_index"],
                bucket_hits=[bucket],
            )
        else:
            bucket = infer_existing_bucket(entry)
        built_entry = build_entry(
            candidate=candidate,
            bucket=bucket,
            rank=len(curated_entries) + 1,
            local_local_path=local_path,
            existing_entry=entry,
            source_queries=["existing_index"],
        )
        curated_entries.append(built_entry)
        seen_ids.add(entry_id)

    # Now add new candidates sorted by score.
    sorted_candidates = sorted(
        candidates_by_id.values(),
        key=lambda cand: score_candidate(cand, bool(cand.local_path)),
        reverse=True,
    )

    for candidate in sorted_candidates:
        if len(curated_entries) >= args.max_projects:
            break
        candidate_id = candidate.repo_id
        if candidate_id in seen_ids:
            continue
        local_path = candidate.local_path
        existing_entry = existing_map.get(candidate_id)
        bucket = candidate.bucket_hits[0] if candidate.bucket_hits else classify_bucket(build_text_blob(candidate))
        built_entry = build_entry(
            candidate=candidate,
            bucket=bucket,
            rank=len(curated_entries) + 1,
            local_local_path=local_path,
            existing_entry=existing_entry,
            source_queries=sorted(set(candidate.query_hits)),
        )
        curated_entries.append(built_entry)
        seen_ids.add(candidate_id)

    # Optional cloning for the top remote-only entries.
    if args.clone_top > 0:
        remote_candidates = [
            cand for cand in sorted_candidates if not cand.local_path and cand.repo_id not in seen_ids
        ][: args.clone_top]
        for candidate in remote_candidates:
            maybe_clone_repo(candidate, OTHER_REPOS_DIR)

    for index, entry in enumerate(curated_entries, start=1):
        entry.setdefault("metrics", {})["rank"] = index

    bucket_index: dict[str, list[str]] = {}
    for entry in curated_entries:
        bucket = str(entry.get("signals", {}).get("bucket", "general")) if isinstance(entry.get("signals"), dict) else "general"
        bucket_index.setdefault(bucket, []).append(str(entry.get("id")))

    stats = {
        "selected_projects": len(curated_entries),
        "local_clones": sum(1 for entry in curated_entries if entry.get("path")),
        "remote_only": sum(1 for entry in curated_entries if not entry.get("path")),
        "oanda_related": len(bucket_index.get("oanda", [])),
        "forex_related": len(bucket_index.get("forex", [])),
        "crypto_related": len(bucket_index.get("crypto", [])),
        "framework_related": len(bucket_index.get("framework", [])),
        "ops_related": len(bucket_index.get("ops", [])),
        "data_related": len(bucket_index.get("data", [])),
        "agent_related": len(bucket_index.get("agent", [])),
        "research_related": len(bucket_index.get("research", [])),
        "general_trading_related": len(bucket_index.get("general_trading", bucket_index.get("general", []))),
        "existing_local_entries": existing_count,
        "search_queries": len(SEARCH_QUERIES),
        "search_limit": args.search_limit,
        "readme_limit": args.readme_limit,
    }

    topic_index = {
        "oanda_reference": bucket_index.get("oanda", []),
        "forex_bot_or_strategy": bucket_index.get("forex", []),
        "crypto_bot_or_strategy": bucket_index.get("crypto", []),
        "trading_framework": bucket_index.get("framework", []),
        "ops_and_control": bucket_index.get("ops", []),
        "data_pipeline": bucket_index.get("data", []),
        "agent_tooling": bucket_index.get("agent", []),
        "research_artifact": bucket_index.get("research", []),
        "general_trading": bucket_index.get("general_trading", bucket_index.get("general", [])),
    }

    generated = {
        "generated_at": time.strftime("%Y-%m-%d"),
        "workspace_root": str(WORKSPACE_ROOT),
        "purpose": "High-signal summary of trading, bot, framework, and OANDA-related reference repositories for AI agents.",
        "scope": "Raw snapshot under reference_catalog_repo/sources/other_repos/",
        "source": {
            "type": "github_search_api",
            "queries": SEARCH_QUERIES,
            "max_projects": args.max_projects,
            "search_limit_per_query": args.search_limit,
            "readme_limit": args.readme_limit,
        },
        "stats": stats,
        "topic_index": topic_index,
        "projects": curated_entries,
        "notes": [
            "Remote-only entries are intentionally kept as metadata-rich references so the catalog stays compact.",
            "Clone selected repos with --clone-top if you need deeper local inspection.",
            "Existing local reference entries from the previous catalog are preserved when the local path is still present.",
        ],
        "query_log": query_log,
    }
    return generated


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    catalog = build_catalog(args)
    write_json(args.output, catalog)
    print(f"Wrote {args.output} with {len(catalog.get('projects', []))} projects")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
