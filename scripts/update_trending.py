"""Rewrite the TRENDING section of README.md with today's GitHub Trending.

Uses the parser from https://github.com/imissshe/gh-trending-digest
(pip install git+https://github.com/imissshe/gh-trending-digest).
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from trending_digest.cli import fetch
from trending_digest.parser import parse_trending

START, END = "<!-- TRENDING:START -->", "<!-- TRENDING:END -->"
CST = timezone(timedelta(hours=8))


def cell(text: str, limit: int = 90) -> str:
    text = " ".join(text.split()).replace("|", "\\|")
    return (text[: limit - 1] + "…") if len(text) > limit else (text or "-")


def build_section(repos, now: datetime) -> str:
    lines = [
        START,
        "",
        "| # | 项目 Repository | 简介 Description | 语言 Lang | ⭐ 今日 Today |",
        "|:-:|:--|:--|:-:|--:|",
    ]
    for i, r in enumerate(repos, 1):
        lines.append(
            f"| {i} | [{r.name}]({r.url}) | {cell(r.description)} | {r.language or '-'} | +{r.stars_gained:,} |"
        )
    lines += [
        "",
        f"<sub>🕒 更新于 Updated: {now.astimezone(CST):%Y-%m-%d %H:%M} (UTC+8) · "
        f"数据来源 Source: [github.com/trending](https://github.com/trending) · "
        f"由 [gh-trending-digest](https://github.com/imissshe/gh-trending-digest) 自动生成</sub>",
        "",
        END,
    ]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--readme", type=Path, default=Path("README.md"))
    ap.add_argument("-n", "--limit", type=int, default=10)
    ap.add_argument("--from-html", type=Path, help="parse a saved page instead of fetching")
    ap.add_argument("--exclude", default="jailbreak",
                    help="comma-separated keywords; repos whose name/description match are skipped")
    args = ap.parse_args(argv)

    page = args.from_html.read_text(encoding="utf-8") if args.from_html else fetch("daily")
    words = [w.strip().lower() for w in args.exclude.split(",") if w.strip()]
    repos = [r for r in parse_trending(page)
             if not any(w in f"{r.name} {r.description}".lower() for w in words)][: args.limit]
    if not repos:
        print("error: no trending repos parsed; leaving README untouched", file=sys.stderr)
        return 1

    readme = args.readme.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if not pattern.search(readme):
        print(f"error: markers {START} / {END} not found in {args.readme}", file=sys.stderr)
        return 1
    section = build_section(repos, datetime.now(timezone.utc))
    args.readme.write_text(pattern.sub(lambda _: section, readme, count=1), encoding="utf-8")
    print(f"updated {args.readme} with {len(repos)} repos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
