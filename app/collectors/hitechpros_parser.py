from pathlib import Path
from bs4 import BeautifulSoup
import re


SNAPSHOT_FILE = "data/hitechpros_snapshot2.html"

def is_start_or_date(value: str) -> bool:
    if value.upper() == "ASAP":
        return True
    return re.fullmatch(r"\d{2}/\d{2}/\d{2}", value) is not None

def is_mission_ref(value: str) -> bool:
    return value.isdigit() and len(value) == 6


def parse_hitechpros_snapshot(file_path: str = SNAPSHOT_FILE) -> list[dict]:
    html = Path(file_path).read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")

    lines = [
        line.strip()
        for line in soup.get_text("\n", strip=True).split("\n")
        if line.strip()
    ]

    missions = []

    for i, line in enumerate(lines):
        if not is_mission_ref(line):
            continue

        block = lines[i:i + 12]

        title = block[1] if len(block) > 1 else ""
        skills = []
        start_date = None
        location = None
        remote_policy = None
        company = None
        published_at = None

        for item in block[2:]:
            if is_start_or_date(item):
                start_date = item
                break
            skills.append(item)

        remaining = block[2 + len(skills) + 1:]

        if len(remaining) > 0:
            location = remaining[0]
        if len(remaining) > 1 and remaining[1].lower() in ["hybride", "remote", "présentiel", "presentiel"]:
            remote_policy = remaining[1]
            if len(remaining) > 2:
                company = remaining[2]
            if len(remaining) > 3:
                published_at = remaining[3]
        else:
            if len(remaining) > 1:
                company = remaining[1]
            if len(remaining) > 2:
                published_at = remaining[2]

        raw_text = "\n".join([
            f"Référence: {line}",
            f"Titre: {title}",
            f"Compétences: {', '.join(skills)}",
            f"Début: {start_date or ''}",
            f"Lieu: {location or ''}",
            f"Mode: {remote_policy or ''}",
            f"Société: {company or ''}",
            f"Date: {published_at or ''}",
        ])

        missions.append({
            "external_id": line,
            "title": title,
            "raw_text": raw_text,
            "url": f"https://esn.hitechpros.com",
            "skills": skills,
            "location": location,
            "remote_policy": remote_policy,
            "company": company,
            "published_at_raw": published_at,
        })

    return missions


if __name__ == "__main__":
    missions = parse_hitechpros_snapshot()

    print(f"Parsed missions: {len(missions)}")
    for mission in missions[:5]:
        print(mission)