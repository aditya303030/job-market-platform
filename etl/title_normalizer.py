# making sure all titles lower case / upper case are all normalized and treated the same
import re

TITLE_RULES = [
    ("data_analyst", "Data Analyst", ["data analyst"]),
    ("data_scientist", "Data Scientist", ["data scientist"]),
    ("software_engineer", "Software Engineer", ["software engineer", "software developer", "swe"]),
    ("machine_learning_engineer", "Machine Learning Engineer", ["machine learning engineer", "ml engineer"]),
    ("business_analyst", "Business Analyst", ["business analyst"]),
    ("product_manager", "Product Manager", ["product manager"]),
    ("data_engineer", "Data Engineer", ["data engineer"]),
    ("financial_analyst", "Financial Analyst", ["financial analyst"]),
    ("marketing_analyst", "Marketing Analyst", ["marketing analyst"]),
    ("project_manager", "Project Manager", ["project manager"]),
    ("ux_designer", "UX Designer", ["ux designer", "user experience designer"]),
    ("cybersecurity_analyst", "Cybersecurity Analyst", ["cybersecurity analyst", "security analyst"]),
]

NOISE_PATTERN = re.compile(r"\b(senior|sr\.?|junior|jr\.?|lead|principal|i{1,3}|iv|v)\b", re.IGNORECASE)

def normalize_title(raw_title: str) -> tuple[str, str]:
    lowered = raw_title.lower()
    for family, canonical, keywords in TITLE_RULES:
        if any(kw in lowered for kw in keywords):
            return canonical, family
    cleaned = NOISE_PATTERN.sub("", lowered)
    cleaned = re.sub(r"\s+", " ", cleaned).strip().title()
    return (cleaned or raw_title), "other"