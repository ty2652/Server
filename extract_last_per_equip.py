#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
remote_Hlog.csv (원본)에서 IoT 설비명(B열)별 최신 행 1줄만 추출합니다.
입력은 항상 이 스크립트와 같은 폴더의 remote_Hlog.csv 입니다.

사용:
  python extract_last_per_equip.py
  python extract_last_per_equip.py --output equip_latest.csv
  python extract_last_per_equip.py --sort time
"""

from __future__ import annotations

import argparse
import csv
import sys
from io import StringIO
from pathlib import Path

DEFAULT_INPUT = "remote_Hlog.csv"
DEFAULT_OUTPUT = "remote_Hlog_latest_per_equip.csv"


def parse_equip_name(line: str) -> str | None:
    line = line.rstrip("\r\n")
    if not line:
        return None
    try:
        row = next(csv.reader(StringIO(line)))
    except csv.Error:
        return None
    if len(row) < 2:
        return None
    name = row[1].strip()
    return name or None


def collect_last_per_equip(
    src: Path,
    show_progress: bool,
) -> tuple[dict[str, str], int]:
    latest: dict[str, str] = {}
    read_n = 0
    report_every = 500_000

    with src.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            read_n += 1
            equip = parse_equip_name(line)
            if equip is None:
                continue
            latest[equip] = line if line.endswith("\n") else line + "\n"
            if show_progress and read_n % report_every == 0:
                print(
                    f"  … {read_n:,}줄 읽음, {len(latest):,}개 설비",
                    file=sys.stderr,
                )

    return latest, read_n


def resolve_in_script_dir(here: Path, path: Path) -> Path:
    """상대 경로는 스크립트 폴더 기준."""
    return path if path.is_absolute() else here / path


def main() -> int:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="remote_Hlog 원본 CSV — 설비명(B열)별 최신 행 1줄 추출 "
        f"(입력: {DEFAULT_INPUT}, 스크립트와 같은 폴더)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(DEFAULT_OUTPUT),
        help=f"출력 CSV (기본: {DEFAULT_OUTPUT}, 상대 경로는 스크립트 폴더 기준)",
    )
    parser.add_argument(
        "--sort",
        choices=("equip", "time"),
        default="equip",
        help="출력 정렬: equip=설비명, time=최신 시각 (기본: equip)",
    )
    parser.add_argument("--quiet", action="store_true", help="진행 메시지 숨김")
    args = parser.parse_args()

    src = here / DEFAULT_INPUT
    dst = resolve_in_script_dir(here, args.output)
    if not src.is_file():
        print(f"입력 파일 없음 (스크립트 폴더): {src}", file=sys.stderr)
        return 1

    print(f"입력: {src}")
    print(f"출력: {dst}")
    print()

    latest, read_n = collect_last_per_equip(src, show_progress=not args.quiet)

    if args.sort == "time":
        lines = sorted(latest.values(), key=lambda s: s[:16], reverse=True)
    else:
        lines = [latest[k] for k in sorted(latest.keys())]

    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("w", encoding="utf-8", newline="") as f:
        for line in lines:
            f.write(line)

    print(f"완료: {read_n:,}줄 읽음 → {len(lines):,}개 설비 (설비당 1줄)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
