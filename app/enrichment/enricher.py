import json
import re
from sqlalchemy import text
from app.storage.db import engine
from app.enrichment.rules import (
    TECH_KEYWORDS,
    PROFILE_KEYWORDS,
    PROJECT_TYPE_KEYWORDS,
    SECTOR_KEYWORDS,
    SENIORITY_KEYWORDS,
    URGENCY_KEYWORDS,
    REMOTE_KEYWORDS,
)


def contains_keyword(text_value: str, keyword: str) -> bool:
    pattern = r"(?<!\w)" + re.escape(keyword.lower()) + r"(?!\w)"
    return re.search(pattern, text_value.lower()) is not None

def has_term(text: str, term: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(term.lower())}(?!\w)", text.lower()) is not None

def detect_multiple(text_value: str, rules: dict[str, list[str]]) -> list[str]:
    detected = []

    for label, keywords in rules.items():
        for keyword in keywords:
            if contains_keyword(text_value, keyword):
                detected.append(label)
                break

    return sorted(set(detected))


def detect_single(text_value: str, rules: dict[str, list[str]], default: str = "Unknown") -> str:
    matches = detect_multiple(text_value, rules)
    return matches[0] if matches else default


def calculate_confidence_score(technologies: list[str], profiles: list[str], project_type: str) -> float:
    score = 0.2

    if technologies:
        score += 0.3
    if profiles:
        score += 0.3
    if project_type != "Unknown":
        score += 0.2

    return min(score, 1.0)


def calculate_market_attractiveness_score(
    technologies: list[str],
    profiles: list[str],
    urgency: str,
    project_type: str
) -> float:
    score = 50

    high_demand_tech = {
        "Python", "AWS", "Azure", "GCP", "Databricks", "Spark",
        "Power BI", "LLM", "Machine Learning", "Kubernetes"
    }

    high_demand_profiles = {
        "Data Engineer", "AI Engineer", "DevOps Engineer",
        "Cloud Engineer", "Cybersecurity Consultant"
    }

    score += len(set(technologies) & high_demand_tech) * 5
    score += len(set(profiles) & high_demand_profiles) * 7

    if urgency == "High":
        score += 10
    elif urgency == "Medium":
        score += 5

    if project_type in ["AI / Machine Learning", "Data Engineering", "Cloud / DevOps", "Cybersecurity"]:
        score += 10

    return min(score, 100)


def enrich_new_clean_opportunities() -> int:
    with engine.begin() as connection:
        clean_rows = connection.execute(
            text("""
                SELECT co.id, co.title, co.description, co.location, co.remote_policy
                FROM clean_opportunities co
                LEFT JOIN enriched_opportunities eo
                    ON eo.clean_opportunity_id = co.id
                WHERE eo.id IS NULL
            """)
        ).mappings().all()

        inserted_count = 0

        for row in clean_rows:
            full_text = f"{row['title'] or ''}\n{row['description'] or ''}"

            technologies = detect_multiple(full_text, TECH_KEYWORDS)
            required_profiles = detect_multiple(full_text, PROFILE_KEYWORDS)
            project_type = detect_single(full_text, PROJECT_TYPE_KEYWORDS)
            text_lower = full_text.lower()

            # 1. Very specific domains
            if any(x in text_lower for x in ["microstrategy", "power bi", "tableau", "data analyst", "reporting"]):
                project_type = "Business Intelligence"

            if "business analyst" in text_lower:
                project_type = "Business Analysis"

            if "data engineer" in text_lower:
                project_type = "Data Engineering"

            if any(x in text_lower for x in ["front-end", "frontend", "svelte", "astro", "angular", "spring", "java/jee"]):
                project_type = "Web Development"

            if any(x in text_lower for x in ["android", "ios", "mobile"]):
                project_type = "Mobile Development"

            # 2. Infrastructure / DBA / mainframe
            if any(x in text_lower for x in ["dba", "oracle", "sql server", "patroni"]):
                project_type = "Database Administration"

            if any(x in text_lower for x in ["réseau", "réseaux", "lan", "wan", "wifi", "cisco", "aruba", "active directory"]):
                project_type = "Network / Infrastructure"

            if any(x in text_lower for x in ["mainframe", "cobol", "pacbase", "z/os", "sysplex", "gdps", "rexx"]):
                project_type = "Mainframe"

            # 3. Cybersecurity
            if (
                has_term(full_text, "cybersécurité")
                or has_term(full_text, "sécurité opérationnelle")
                or has_term(full_text, "secop")
                or has_term(full_text, "siem")
                or has_term(full_text, "edr")
                or has_term(full_text, "soc 2")
                or has_term(full_text, "soc n2")
            ):
                project_type = "Cybersecurity"

            # 4. Management
            if "delivery manager" in text_lower:
                project_type = "Product / Project Management"

            if "pmo" in text_lower or "plan de charge" in text_lower:
                project_type = "Product / Project Management"

            sector = detect_single(full_text, SECTOR_KEYWORDS)
            seniority = detect_single(full_text, SENIORITY_KEYWORDS)
            urgency = detect_single(full_text, URGENCY_KEYWORDS)
            remote_policy = detect_single(full_text, REMOTE_KEYWORDS)

            confidence_score = calculate_confidence_score(
                technologies=technologies,
                profiles=required_profiles,
                project_type=project_type
            )

            market_score = calculate_market_attractiveness_score(
                technologies=technologies,
                profiles=required_profiles,
                urgency=urgency,
                project_type=project_type
            )

            connection.execute(
                text("""
                    INSERT INTO enriched_opportunities
                    (
                        clean_opportunity_id,
                        project_type,
                        sector,
                        seniority,
                        urgency,
                        required_profiles,
                        technologies,
                        market_attractiveness_score,
                        confidence_score
                    )
                    VALUES
                    (
                        :clean_opportunity_id,
                        :project_type,
                        :sector,
                        :seniority,
                        :urgency,
                        :required_profiles,
                        :technologies,
                        :market_attractiveness_score,
                        :confidence_score
                    )
                """),
                {
                    "clean_opportunity_id": row["id"],
                    "project_type": project_type,
                    "sector": sector,
                    "seniority": seniority,
                    "urgency": urgency,
                    "required_profiles": json.dumps(required_profiles),
                    "technologies": json.dumps(technologies),
                    "market_attractiveness_score": market_score,
                    "confidence_score": confidence_score,
                }
            )

            inserted_count += 1

    return inserted_count