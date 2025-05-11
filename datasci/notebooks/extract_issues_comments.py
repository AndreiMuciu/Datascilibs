#!/usr/bin/env python3
"""
extract_issue_comments.py

Extrage comentariile de pe issue-uri GitHub pentru fiecare repository listat
într-un CSV și salvează rezultatul în data/repos/<owner>_<repo>/issue_comments.csv.

Usage:
    python extract_issue_comments.py [--csv PATH_TO_CSV] [--max-comments N]

Exemplu:
    python extract_issue_comments.py --csv shallow_data.csv --max-comments 100
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


def extract_issue_comments(
    repo_full_name: str,
    gh: Github,
    dest_folder: Path,
    max_comments: int | None = None
) -> pd.DataFrame:
    """
    Extrage toate comentariile de pe issue-uri dintr-un repo.
    - repo_full_name: 'owner/repo'
    - gh: clientul PyGithub autenticat
    - dest_folder: Path către folderul repo-ului
    - max_comments: dacă nu None, limitează totalul de comentarii extrase
    """
    repo = gh.get_repo(repo_full_name)
    rows = []
    count = 0

    for issue in repo.get_issues(state="all"):
        for comment in issue.get_comments():
            if max_comments and count >= max_comments:
                break
            r = comment.raw_data.get("reactions", {})
            rows.append({
                "repo_full_name":  repo_full_name,
                "issue_id":        issue.id,
                "comment_id":      comment.id,
                "user_login":      comment.user.login,
                "user_id":         comment.user.id,
                "created_at":      comment.created_at.isoformat(),
                "updated_at":      comment.updated_at.isoformat(),
                "body":            comment.body,
                "reactions_total": r.get("total_count", 0),
                "reactions_plus1": r.get("+1", 0),
                "reactions_minus1":r.get("-1", 0),
                "reactions_laugh": r.get("laugh", 0),
                "reactions_hooray":r.get("hooray", 0),
                "reactions_confused": r.get("confused", 0),
                "reactions_heart": r.get("heart", 0)
            })
            count += 1
        if max_comments and count >= max_comments:
            break

    df = pd.DataFrame(rows)
    outfile = dest_folder / "issue_comments.csv"
    df.to_csv(outfile, index=False)
    log(f"Saved {len(df)} issue comments to {outfile}")
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Extrage comentariile de pe issue-uri pentru lista de repo-uri."
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

    repos = read_repo_list(args.csv)
    log(f"Starting issue-comments extraction for {len(repos)} repos")

    for full_name in repos:
        log(f"Processing issue comments → {full_name}")
        folder = ensure_repo_folder(full_name)
        extract_issue_comments(full_name, gh, folder, max_comments=args.max_comments)


if __name__ == "__main__":
    main()