#!/usr/bin/env python3
"""
extract_commits.py

Extrage commit-urile GitHub pentru fiecare repo listat într-un CSV și salvează
datele în data/repos/<owner>_<repo>/commits.csv.

Usage:
    python extract_commits.py [--csv PATH_TO_CSV] [--max-commits N]

Exemplu:
    python extract_commits.py --csv shallow_data.csv --max-commits 50
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
    token = os.getenv("GH_TOKEN")
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


def ensure_repo_folder(full_name: str, base_dir: Path) -> Path:
    """
    Creează folderul data/repos/owner_repo dacă nu există și îl returnează.
    """
    owner, repo = full_name.split("/")
    folder = base_dir / f"{owner}_{repo}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def log(msg: str):
    """Afișează un mesaj cu timestamp UTC."""
    print(f"[{datetime.utcnow().isoformat()}] {msg}")


def extract_commits(
    repo_full_name: str,
    gh: Github,
    dest_folder: Path,
    max_commits: int | None = None
) -> pd.DataFrame:
    """
    Extrage commit-urile dintr-un repo:
      - sha, url, autor, committer, date, mesaj, LoC și număr de fișiere
      - max_commits: dacă nu None, limitează numărul de commit-uri
    """
    repo = gh.get_repo(repo_full_name)
    rows = []

    for i, commit in enumerate(repo.get_commits()):
        if max_commits and i >= max_commits:
            break
        stats     = commit.stats
        author    = commit.author
        committer = commit.committer
        rows.append({
            "repo_full_name":      repo_full_name,
            "sha":                 commit.sha,
            "html_url":            commit.html_url,
            "author_login":        author.login    if author    else None,
            "author_id":           author.id       if author    else None,
            "author_type":         author.type     if author    else None,
            "authored_date":       commit.commit.author.date.isoformat(),
            "committer_login":     committer.login if committer else None,
            "committed_date":      commit.commit.committer.date.isoformat(),
            "message":             commit.commit.message,
            "additions":           stats.additions,
            "deletions":           stats.deletions,
            "total_changes":       stats.total,
            "files_changed_count": len(commit.files),
            "parent_shas":         ",".join(p.sha for p in commit.parents)
        })

    df = pd.DataFrame(rows)
    outfile = dest_folder / "commits.csv"
    df.to_csv(outfile, index=False)
    log(f"Saved {len(df)} commits to {outfile}")
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Extrage commit-urile pentru lista de repo-uri."
    )
    parser.add_argument(
        "--csv",
        default="shallow_data.csv",
        help="Path to CSV file with 'full_name' column"
    )
    parser.add_argument(
        "--max-commits",
        type=int,
        default=None,
        help="Max number of commits to extract per repo"
    )
    args = parser.parse_args()

    token = load_token()
    gh = Github(token)

    base_dir = Path("data/repos")

    # ——— ȘTERGERE GLOBALĂ (toate commits.csv) ———
    if base_dir.exists():
        for old in base_dir.rglob("commits.csv"):
            old.unlink()
            log(f"Removed old file → {old.resolve()}")
    # ——————————————————————————————————————————

    repos = read_repo_list(args.csv)
    log(f"Starting commits extraction for {len(repos)} repos")

    for full_name in repos:
        log(f"Processing commits → {full_name}")
        folder = ensure_repo_folder(full_name, base_dir)
        extract_commits(full_name, gh, folder, max_commits=args.max_commits)


if __name__ == "__main__":
    main()