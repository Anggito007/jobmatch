"""Skill vocabulary + ekstraksi berbasis aturan.

Ekstraksi skill memakai daftar istilah terkurasi, dicocokkan dengan batas kata
(case-insensitive) supaya tidak false-positive (mis. "Go" ≠ "Google", "AI" ≠
"email"). Cukup untuk matching skill-overlap; nanti bisa diganti NER/LLM.
"""
from __future__ import annotations

import re

# Istilah teknis umum — meliputi backend, frontend, data, devops, IoT.
SKILL_TERMS: list[str] = [
    # Bahasa & framework
    "Python", "JavaScript", "TypeScript", "Java", "Go", "Golang", "C++", "C#",
    "PHP", "Ruby", "Kotlin", "Swift", "Rust", "SQL", "HTML", "CSS", "React",
    "Next.js", "Vue", "Angular", "Node.js", "Express", "Django", "Flask",
    "FastAPI", "Laravel", "Spring",
    # Data / AI
    "Machine Learning", "Deep Learning", "NLP", "TensorFlow", "PyTorch",
    "Pandas", "NumPy", "Data Analysis", "Data Science", "LLM", "RAG",
    "Embedding", "AI", "Artificial Intelligence",
    # Infra / devops
    "Docker", "Kubernetes", "AWS", "GCP", "Azure", "CI/CD", "Git", "Linux",
    "DevOps", "Terraform", "Jenkins", "Nginx",
    # Database
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Elasticsearch",
    # IoT / embedded
    "IoT", "LoRa", "ESP32", "Arduino", "Raspberry Pi", "MQTT", "Embedded",
    "Sensor", "Microcontroller",
    # Soft skills / umum
    "REST API", "API", "Microservices", "Agile", "Scrum", "GitHub", "Testing",
]


def _matches(term: str, text_lower: str) -> bool:
    """Cocokkan term dengan batas kata (lookaround alnum) supaya akurat."""
    pattern = re.compile(rf"(?<![a-z0-9]){re.escape(term.lower())}(?![a-z0-9])")
    return pattern.search(text_lower) is not None


def extract_skills(text: str) -> list[str]:
    """Kembalikan daftar skill (unik, urutan kemunculan) yang ditemukan di teks."""
    if not text:
        return []
    low = text.lower()
    found: list[str] = []
    seen: set[str] = set()

    for term in SKILL_TERMS:
        if _matches(term, low):
            key = term.lower()
            if key not in seen:
                seen.add(key)
                found.append(term)
    return found


def skill_overlap_score(cv_skills: list[str], job_skills: list[str]) -> float:
    """Skor tumpang-tindih skill 0..1 (Jaccard)."""
    if not cv_skills or not job_skills:
        return 0.0
    a = {s.lower() for s in cv_skills}
    b = {s.lower() for s in job_skills}
    inter = a & b
    union = a | b
    return len(inter) / len(union) if union else 0.0
