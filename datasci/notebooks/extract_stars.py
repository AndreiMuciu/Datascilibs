#!/usr/bin/env python3
"""
extract_stars.py
Usage:
    python extract_stars.py [--csv PATH_TO_CSV] [--max-stars N]

Exemplu:
    python extract_stars.py --csv shallow_data.csv --max-stars 50
"""

import os
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from github import Github


def load_token():
    load_dotenv()
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
        raise ValueError(f"CSV {csv_path} nu conține coloana 'full_name'")
    return df["full_name"].dropna().unique().tolist()


def ensure_repo_folder(full_name: str, base_dir: str = "data/repos") -> Path:
    """
    Creează (dacă nu există) folderul data/repos/owner_repo
    și returnează un Path către el.
    """
    owner, repo = full_name.split("/")
    folder = Path(base_dir) / f"{owner}_{repo}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def log(msg: str):
    """Log cu timestamp UTC."""
    print(f"[{datetime.utcnow().isoformat()}] {msg}")


def extract_stars(
    repo_full_name: str,
    gh: Github,
    dest_folder: Path,
    max_stars: int | None = None
) -> pd.DataFrame:
    """
    Extrage evenimente de tip 'star' pentru un repo.
    - repo_full_name: 'owner/repo'
    - gh: clientul autenticat PyGithub
    - dest_folder: Path unde se va salva 'stars.csv'
    - max_stars: dacă nu e None, limitează numărul de intrări
    """
    repo = gh.get_repo(repo_full_name)
    rows = []
    count = 0

    for sg in repo.get_stargazers_with_dates():
        if max_stars and count >= max_stars:
            break
        user = sg.user
        rows.append({
            "repo_full_name": repo_full_name,
            "user_login":     user.login,
            "user_id":        user.id,
            "starred_at":     sg.starred_at.isoformat(),
            "user_type":      user.type,
            "user_location":  user.location,
            "user_company":   user.company
        })
        count += 1

    df = pd.DataFrame(rows)
    outfile = dest_folder / "stars.csv"
    df.to_csv(outfile, index=False)
    log(f"Saved {len(df)} stars to {outfile}")
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Extrage istoric stele GitHub pentru lista de repo-uri."
    )
    parser.add_argument(
        "--csv",
        default="shallow_data.csv",
        help="Calea către CSV-ul cu lista de repo-uri (coloană full_name)."
    )
    parser.add_argument(
        "--max-stars",
        type=int,
        default=None,
        help="Numărul maxim de evenimente de tip star de extras pentru fiecare repo."
    )
    args = parser.parse_args()

    token = load_token()
    gh = Github(token)

    repos = read_repo_list(args.csv)
    log(f"Încep extracția pentru {len(repos)} repo-uri")

    for full_name in repos:
        log(f"Processing stars → {full_name}")
        folder = ensure_repo_folder(full_name)
        extract_stars(full_name, gh, folder, max_stars=args.max_stars)


if __name__ == "__main__":
    main()