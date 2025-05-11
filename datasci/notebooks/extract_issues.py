#!/usr/bin/env python3
"""
extract_issues.py

Extrage toate issue-urile (open + closed) GitHub pentru fiecare repo listat
într-un CSV și salvează rezultatele în
data/repos/<owner>_<repo>/issues.csv.

Usage:
    python extract_issues.py [--csv PATH_TO_CSV] [--max-issues N]

Exemplu:
    python extract_issues.py --csv shallow_data.csv --max-issues 100
"""

import os
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from github import Github


def load_token() -> str:
    """Încarcă GH_TOKEN din .env sau din mediul de sistem."""
    load_dotenv()
    # token = os.getenv("GH_TOKEN")
    token = "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"
    if not token:
        raise ValueError("Environment variable GH_TOKEN is not set")
    return token


def read_repo_list(csv_path: str) -> list[str]:
    """
    Încarcă CSV-ul cu lista de repo-uri și returnează full_name-urile unice.
    Așteaptă o coloană 'full_name' cu format 'owner/repo'.
    """
    df = pd.read_csv(csv_path)
    if "full_name" not in df.columns:
        raise ValueError(f"CSV '{csv_path}' must contain a 'full_name' column")
    return df["full_name"].dropna().unique().tolist()


def ensure_repo_folder(full_name: str, base_dir: str = "data/repos") -> Path:
    """
    Creează folderul data/repos/owner_repo dacă nu există și îl returnează.
    """
    owner, repo = full_name.split("/")
    folder = Path(base_dir) / f"{owner}_{repo}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def log(msg: str):
    """Afișează un mesaj cu timestamp UTC."""
    print(f"[{datetime.utcnow().isoformat()}] {msg}")


def extract_issues(
    repo_full_name: str,
    gh: Github,
    dest_folder: Path,
    max_issues: int | None = None
) -> pd.DataFrame:
    """
    Extrage issue-urile dintr-un repo:
      - toate state-urile (open și closed)
      - max_issues: dacă nu None, limitează numărul de issue-uri
    """
    repo = gh.get_repo(repo_full_name)
    rows = []

    for i, issue in enumerate(repo.get_issues(state="all")):
        if max_issues and i >= max_issues:
            break
        r = issue.raw_data.get("reactions", {})
        labels = ";".join(lbl["name"] for lbl in issue.raw_data.get("labels", []))
        rows.append({
            "repo_full_name":    repo_full_name,
            "issue_id":          issue.id,
            "number":            issue.number,
            "title":             issue.title,
            "body":              issue.body,
            "user_login":        issue.user.login,
            "user_id":           issue.user.id,
            "state":             issue.state,
            "locked":            issue.locked,
            "comments_count":    issue.comments,
            "created_at":        issue.created_at.isoformat(),
            "updated_at":        issue.updated_at.isoformat(),
            "closed_at":         issue.closed_at.isoformat() if issue.closed_at else None,
            "labels":            labels,
            "reactions_total":   r.get("total_count", 0),
            "reactions_plus1":   r.get("+1", 0),
            "reactions_minus1":  r.get("-1", 0),
            "reactions_laugh":   r.get("laugh", 0),
            "reactions_hooray":  r.get("hooray", 0),
            "reactions_confused":r.get("confused", 0),
            "reactions_heart":   r.get("heart", 0)
        })

    df = pd.DataFrame(rows)
    outfile = dest_folder / "issues.csv"
    df.to_csv(outfile, index=False)
    log(f"Saved {len(df)} issues to {outfile}")
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Extrage issue-urile pentru lista de repo-uri."
    )
    parser.add_argument(
        "--csv",
        default="shallow_data.csv",
        help="Path to CSV file with 'full_name' column"
    )
    parser.add_argument(
        "--max-issues",
        type=int,
        default=None,
        help="Max number of issues to extract per repo"
    )
    args = parser.parse_args()

    token = load_token()
    gh = Github(token)

    repos = read_repo_list(args.csv)
    log(f"Starting issues extraction for {len(repos)} repos")

    for full_name in repos:
        log(f"Processing issues → {full_name}")
        folder = ensure_repo_folder(full_name)
        extract_issues(full_name, gh, folder, max_issues=args.max_issues)


if __name__ == "__main__":
    main()