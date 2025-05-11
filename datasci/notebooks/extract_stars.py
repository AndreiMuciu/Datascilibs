#!/usr/bin/env python3
import os
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from github import Github

def load_token():
    load_dotenv()
    token = os.getenv("GH_TOKEN")
    if not token:
        raise ValueError("Environment variable GH_TOKEN is not set")
    return token

def read_repo_list(csv_path: str) -> list[str]:
    df = pd.read_csv(csv_path)
    if "full_name" not in df.columns:
        raise ValueError(f"CSV {csv_path} nu conține coloana 'full_name'")
    return df["full_name"].dropna().unique().tolist()

def ensure_repo_folder(full_name: str, base_dir: Path) -> Path:
    owner, repo = full_name.split("/")
    folder = base_dir / f"{owner}_{repo}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder

def log(msg: str):
    print(f"[{datetime.utcnow().isoformat()}] {msg}")

def extract_stars(repo_full_name: str, gh: Github, dest_folder: Path, max_stars: int | None):
    repo = gh.get_repo(repo_full_name)
    rows, count = [], 0
    for sg in repo.get_stargazers_with_dates():
        if max_stars and count >= max_stars:
            break
        u = sg.user
        rows.append({
            "repo_full_name": repo_full_name,
            "user_login":     u.login,
            "user_id":        u.id,
            "starred_at":     sg.starred_at.isoformat(),
            "user_type":      u.type,
            "user_location":  u.location,
            "user_company":   u.company
        })
        count += 1
    df = pd.DataFrame(rows)
    outfile = dest_folder / "stars.csv"
    df.to_csv(outfile, index=False)
    log(f"Saved {len(df)} stars to {outfile}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="shallow_data.csv")
    parser.add_argument("--max-stars", type=int, default=None)
    args = parser.parse_args()

    token = load_token()
    gh    = Github(token)
    base_dir = Path("data/repos")

    # ——— ȘTERGERE GLOBALĂ ———
    if base_dir.exists():
        for old in base_dir.rglob("stars.csv"):
            old.unlink()
            log(f"Removed old file → {old.resolve()}")
    # —————————————————————————

    repos = read_repo_list(args.csv)
    log(f"Încep extracția pentru {len(repos)} repo-uri")

    for full_name in repos:
        folder = ensure_repo_folder(full_name, base_dir)
        extract_stars(full_name, gh, folder, args.max_stars)

if __name__ == "__main__":
    main()