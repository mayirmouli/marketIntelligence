import hashlib
from sqlalchemy import text
from app.storage.db import engine


SEED_OPPORTUNITIES = [
    {
        "source_name": "HiTechPros",
        "external_id": "SEED-001",
        "title": "Mission Data Engineer Azure Databricks",
        "raw_text": "Client bancaire recherche un Data Engineer senior pour construire des pipelines ETL sur Azure, Databricks, Spark et SQL. Mission longue durée en hybride. Démarrage rapide.",
        "url": "https://example.com/seed-001",
    },
    {
        "source_name": "Email Alert",
        "external_id": "SEED-002",
        "title": "Consultant Power BI Reporting Finance",
        "raw_text": "Mission BI pour créer des dashboards Power BI, suivre les KPI financiers et structurer les données dans un data warehouse. Profil confirmé demandé.",
        "url": "https://example.com/seed-002",
    },
    {
        "source_name": "LinkedIn Export",
        "external_id": "SEED-003",
        "title": "AI Engineer LLM RAG Chatbot",
        "raw_text": "Entreprise cherche un AI Engineer pour développer un chatbot interne avec LLM, RAG, Python et APIs. Démarrage ASAP, full remote.",
        "url": "https://example.com/seed-003",
    },
    {
        "source_name": "HiTechPros",
        "external_id": "SEED-004",
        "title": "DevOps Engineer Kubernetes AWS",
        "raw_text": "Client industrie recherche un DevOps Engineer pour automatiser CI/CD, Docker, Kubernetes, Terraform et AWS. Mission sur site avec télétravail partiel.",
        "url": "https://example.com/seed-004",
    },
    {
        "source_name": "Email Alert",
        "external_id": "SEED-005",
        "title": "Cybersecurity Consultant SIEM SOC",
        "raw_text": "Mission cybersécurité pour renforcer un SOC, analyser les alertes SIEM, accompagner la conformité ISO 27001 et améliorer les processus de sécurité.",
        "url": "https://example.com/seed-005",
    },
    {
        "source_name": "LinkedIn Export",
        "external_id": "SEED-006",
        "title": "Développeur Fullstack React Node.js",
        "raw_text": "Startup e-commerce recherche un développeur fullstack React, Node.js, TypeScript et PostgreSQL pour une refonte d'application web.",
        "url": "https://example.com/seed-006",
    },
    {
        "source_name": "HiTechPros",
        "external_id": "SEED-007",
        "title": "Consultant SAP S/4HANA Finance",
        "raw_text": "Grand groupe recherche un consultant fonctionnel SAP S/4HANA sur module finance. Projet ERP, ateliers métier, paramétrage et accompagnement utilisateurs.",
        "url": "https://example.com/seed-007",
    },
    {
        "source_name": "Email Alert",
        "external_id": "SEED-008",
        "title": "QA Engineer automatisation Cypress",
        "raw_text": "Client recherche QA Engineer pour automatiser les tests avec Cypress, participer à la recette et améliorer la qualité des releases.",
        "url": "https://example.com/seed-008",
    },
    {
        "source_name": "LinkedIn Export",
        "external_id": "SEED-009",
        "title": "Cloud Engineer GCP Terraform",
        "raw_text": "Mission cloud pour déployer des infrastructures GCP avec Terraform, Kubernetes et CI/CD. Profil senior attendu.",
        "url": "https://example.com/seed-009",
    },
    {
        "source_name": "HiTechPros",
        "external_id": "SEED-010",
        "title": "Product Owner application mobile",
        "raw_text": "Client transport recherche Product Owner pour cadrer une application mobile iOS et Android, prioriser le backlog et coordonner les équipes agile.",
        "url": "https://example.com/seed-010",
    },
]


def create_hash(title: str, raw_text: str, url: str) -> str:
    return hashlib.sha256(f"{title}|{raw_text}|{url}".encode("utf-8")).hexdigest()


def seed_raw_opportunities() -> int:
    inserted_count = 0

    with engine.begin() as connection:
        for item in SEED_OPPORTUNITIES:
            content_hash = create_hash(item["title"], item["raw_text"], item["url"])

            result = connection.execute(
                text("""
                    INSERT INTO raw_opportunities
                    (source_name, external_id, title, raw_text, url, content_hash)
                    VALUES
                    (:source_name, :external_id, :title, :raw_text, :url, :content_hash)
                    ON CONFLICT (content_hash) DO NOTHING
                """),
                {
                    **item,
                    "content_hash": content_hash,
                },
            )

            inserted_count += result.rowcount

    return inserted_count


if __name__ == "__main__":
    count = seed_raw_opportunities()
    print(f"Seed raw opportunities inserted: {count}")