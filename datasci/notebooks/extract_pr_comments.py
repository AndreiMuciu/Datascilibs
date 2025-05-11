#!/usr/bin/env python3
"""
extract_pr_comments.py

Extrage comentariile PR-urilor (atât issue-like cât și review comments)
pentru fiecare repo listat în CSV și salvează rezultatele în
data/repos/<owner>_<repo>/pr_comments.csv.

Usage:
    python extract_pr_comments.py [--csv PATH_TO_CSV] [--max-comments N]

Exemplu:
    python extract_pr_comments.py --csv shallow_data.csv --max-comments 100
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
        raise ValueError(f"CSV '{csv_path}' must contain a 'full_name' column")
    return df["full_name"].dropna().unique().tolist()


def ensure_repo_folder(full_name: str, base_dir: Path) -> Path:
    owner, repo = full_name.split("/")
    folder = base_dir / f"{owner}_{repo}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def log(msg: str):
    print(f"[{datetime.utcnow().isoformat()}] {msg}")


def extract_pr_comments(
    repo_full_name: str,
    gh: Github,
    dest_folder: Path,
    max_comments: int | None = None
) -> pd.DataFrame:
    """
    Extrage comentariile PR-urilor:
      - issue-like comments și review comments
      - max_comments: dacă nu None, limitează totalul de comentarii
    """
    repo  = gh.get_repo(repo_full_name)
    rows  = []
    count = 0

    for pr in repo.get_pulls(state="all"):
        # issue-like comments
        for c in pr.get_comments():
            if max_comments and count >= max_comments:
                break
            r = c.raw_data.get("reactions", {})
            rows.append({
                "repo_full_name":    repo_full_name,
                "pr_id":             pr.id,
                "comment_id":        c.id,
                "user_login":        c.user.login,
                "user_id":           c.user.id,
                "created_at":        c.created_at.isoformat(),
                "updated_at":        c.updated_at.isoformat(),
                "body":              c.body,
                "is_review_comment": False,
                "path":              None,
                "position":          None,
                "diff_hunk":         None,
                "reactions_total":   r.get("total_count", 0),
                "reactions_plus1":   r.get("+1", 0),
                "reactions_minus1":  r.get("-1", 0),
                "reactions_laugh":   r.get("laugh", 0),
                "reactions_hooray":  r.get("hooray", 0),
                "reactions_confused":r.get("confused", 0),
                "reactions_heart":   r.get("heart", 0),
            })
            count += 1
        if max_comments and count >= max_comments:
            break

        # review comments
        for rc in pr.get_review_comments():
            if max_comments and count >= max_comments:
                break
            r = rc.raw_data.get("reactions", {})
            rows.append({
                "repo_full_name":    repo_full_name,
                "pr_id":             pr.id,
                "comment_id":        rc.id,
                "user_login":        rc.user.login,
                "user_id":           rc.user.id,
                "created_at":        rc.created_at.isoformat(),
                "updated_at":        rc.updated_at.isoformat(),
                "body":              rc.body,
                "is_review_comment": True,
                "path":              rc.path,
                "position":          rc.position,
                "diff_hunk":         rc.diff_hunk,
                "reactions_total":   r.get("total_count", 0),
                "reactions_plus1":   r.get("+1", 0),
                "reactions_minus1":  r.get("-1", 0),
                "reactions_laugh":   r.get("laugh", 0),
                "reactions_hooray":  r.get("hooray", 0),
                "reactions_confused":r.get("confused", 0),
                "reactions_heart":   r.get("heart", 0),
            })
            count += 1
        if max_comments and count >= max_comments:
            break

    df = pd.DataFrame(rows)
    outfile = dest_folder / "pr_comments.csv"
    df.to_csv(outfile, index=False)
    log(f"Saved {len(df)} PR comments to {outfile}")
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Extrage comentarii PR pentru lista de repo-uri."
    )
    parser.add_argument(
        "--csv",
        default="shallow_data.csv",
        help="Path to CSV file with 'full_name' column"
    )
    parser.add_argument(
        "--max-comments",
        type=int,
        default=None,
        help="Max number of comments to extract per repo"
    )
    args = parser.parse_args()

    token = load_token()
    gh = Github(token)

    base_dir = Path("data/repos")

    # ——— ȘTERGERE GLOBALĂ (toate pr_comments.csv) ———
    if base_dir.exists():
        for old in base_dir.rglob("pr_comments.csv"):
            old.unlink()
            log(f"Removed old file → {old.resolve()}")
    # ————————————————————————————————

    repos = read_repo_list(args.csv)
    log(f"Starting PR-comments extraction for {len(repos)} repos")

    for full_name in repos:
        log(f"Processing PR comments → {full_name}")
        folder = ensure_repo_folder(full_name, base_dir)
        extract_pr_comments(full_name, gh, folder, max_comments=args.max_comments)


if __name__ == "__main__":
    main()