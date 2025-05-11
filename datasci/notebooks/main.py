#!/usr/bin/env python3
"""
main.py

Orchestrator care rulează toate scripturile de extracție în paralel,
fiecare pe un thread separat.

Usage:
    python main.py [--csv PATH_TO_CSV]
                   [--max-stars N]
                   [--max-prs N]
                   [--max-pr-comments N]
                   [--max-issue-comments N]
                   [--max-issues N]
                   [--max-commits N]

Exemplu:
    python main.py --csv shallow_data.csv \
                   --max-stars 50 \
                   --max-prs 100 \
                   --max-pr-comments 200 \
                   --max-issue-comments 200 \
                   --max-issues 150 \
                   --max-commits 75
"""

import sys
import argparse
import threading
import subprocess


def run_script(script: str, args: list[str]) -> None:
    cmd = [sys.executable, script] + args
    print(f">>> Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"!!! {script} exited with code {result.returncode}")


def main():
    parser = argparse.ArgumentParser(
        description="Orchestrator pentru toate scripturile de extracție GitHub"
    )
    parser.add_argument(
        "--csv", default="shallow_data.csv",
        help="CSV cu coloana 'full_name' (owner/repo)"
    )
    parser.add_argument("--max-stars",        type=int, default=None,
                        help="Max stars per repo")
    parser.add_argument("--max-prs",          type=int, default=None,
                        help="Max PRs per repo")
    parser.add_argument("--max-pr-comments",  type=int, default=None,
                        help="Max PR comments per repo")
    parser.add_argument("--max-issue-comments", type=int, default=None,
                        help="Max issue comments per repo")
    parser.add_argument("--max-issues",       type=int, default=None,
                        help="Max issues per repo")
    parser.add_argument("--max-commits",      type=int, default=None,
                        help="Max commits per repo")
    args = parser.parse_args()

    # Define lista de scripturi + flag-ul pentru parametrul maxim
    jobs = [
        ("extract_stars.py",         "--max-stars",        args.max_stars),
        ("extract_prs.py",           "--max-prs",          args.max_prs),
        ("extract_pr_comments.py",   "--max-comments",     args.max_pr_comments),
        ("extract_issue_comments.py","--max-comments",     args.max_issue_comments),
        ("extract_issues.py",        "--max-issues",       args.max_issues),
        ("extract_commits.py",       "--max-commits",      args.max_commits),
    ]

    threads = []
    for script, max_flag, max_val in jobs:
        cmd_args = ["--csv", args.csv]
        if max_val is not None:
            cmd_args += [max_flag, str(max_val)]
        t = threading.Thread(target=run_script, args=(script, cmd_args), daemon=True)
        threads.append(t)

    # Pornește toate thread-urile
    for t in threads:
        t.start()

    # Așteaptă terminarea tuturor
    for t in threads:
        t.join()

    print(">>> All extraction jobs completed.")


if __name__ == "__main__":
    main()