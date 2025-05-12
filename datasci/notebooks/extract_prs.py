#!/usr/bin/env python3
"""
extract_prs.py

Extrage pull requests GitHub pentru fiecare repo listat în CSV și salvează
datele în data/repos/<owner>_<repo>/prs.csv.

Usage:
    python extract_prs.py [--csv PATH_TO_CSV] [--max-prs N]

Exemplu:
    python extract_prs.py --csv shallow_data.csv --max-prs 100
"""

import os
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from github import Github


def load_token() -> str:
    load_dotenv()
    token = os.getenv("GH_TOKEN")
    if not token:
        raise ValueError("Environment variable GH_TOKEN is not set")
    return token


def read_repo_list(csv_path: str) -> list[str]:
    df = pd.read_csv(csv_path)
    if "full_name" not in df.columns:
        raise ValueError(f"CSV {csv_path} must contain 'full_name' column")
    return df["full_name"].dropna().unique().tolist()


def ensure_repo_folder(full_name: str, base_dir: Path) -> Path:
    owner, repo = full_name.split("/")
    folder = base_dir / f"{owner}_{repo}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def log(msg: str):
    print(f"[{datetime.utcnow().isoformat()}] {msg}")


def extract_prs(
    repo_full_name: str,
    gh: Github,
    dest_folder: Path,
    max_prs: int | None = None
) -> pd.DataFrame:
    repo = gh.get_repo(repo_full_name)
    rows = []
    for i, pr in enumerate(repo.get_pulls(state="all", sort="created", direction="asc")):
        if max_prs and i >= max_prs:
            break
        users, teams = pr.get_review_requests()
        rows.append({
            "repo_full_name":      repo_full_name,
            "pr_id":               pr.id,
            "number":              pr.number,
            "title":               pr.title,
            "body":                pr.body,
            "user_login":          pr.user.login,
            "user_id":             pr.user.id,
            "state":               pr.state,
            "draft":               pr.draft,
            "created_at":          pr.created_at.isoformat(),
            "updated_at":          pr.updated_at.isoformat(),
            "closed_at":           pr.closed_at.isoformat() if pr.closed_at else None,
            "merged_at":           pr.merged_at.isoformat() if pr.merged_at else None,
            "merge_commit_sha":    pr.merge_commit_sha,
            "mergeable_state":     pr.mergeable_state,
            "additions":           pr.additions,
            "deletions":           pr.deletions,
            "changed_files":       pr.changed_files,
            "commits_count":       pr.commits,
            "review_comments_count": pr.review_comments,
            "comments_count":      pr.comments,
            "requested_reviewers": ";".join(u.login for u in users),
            "requested_teams":     ";".join(t.slug for t in teams),
            "labels":              ";".join(lbl["name"] for lbl in pr.raw_data.get("labels", []))
        })
    df = pd.DataFrame(rows)
    outfile = dest_folder / "prs.csv"
    df.to_csv(outfile, index=False)
    log(f"Saved {len(df)} PRs to {outfile}")
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Extrage pull requests pentru lista de repo-uri."
    )
    parser.add_argument(
        "--csv",
        default="shallow_data.csv",
        help="Path to CSV file with 'full_name' column"
    )
    parser.add_argument(
        "--max-prs",
        type=int,
        default=None,
        help="Max number of PRs to extract per repo"
    )
    args = parser.parse_args()

    token = load_token()
    gh = Github(token)

    base_dir = Path("data/repos")

    # ——— ȘTERGERE GLOBALĂ (toate prs.csv) ———
    if base_dir.exists():
        for old in base_dir.rglob("prs.csv"):
            old.unlink()
            log(f"Removed old file → {old.resolve()}")
    # ————————————————————————————————

    repos = read_repo_list(args.csv)
    log(f"Starting extraction for {len(repos)} repos")

    for full_name in repos:
        log(f"Processing PRs → {full_name}")
        folder = ensure_repo_folder(full_name, base_dir)
        extract_prs(full_name, gh, folder, max_prs=args.max_prs)


if __name__ == "__main__":
    main()