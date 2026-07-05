"""
Per-source adapters: each API returns a differently-shaped payload.
These normalize both shapes into one common dict so run_etl.py never
has to branch on source itself — it just calls the right adapter once.
"""

from etl.salary_parser import parse_adzuna_salary, parse_usajobs_salary
from etl.industry_mapper import resolve_industry


def adapt_adzuna(payload: dict, country: str) -> dict:
    salary_info = parse_adzuna_salary(payload, country)
    return {
        "raw_title": payload.get("title", ""),
        "company_name": (payload.get("company") or {}).get("display_name", "Unknown"),
        "location": (payload.get("location") or {}).get("display_name"),
        "created_str": payload.get("created"),
        "description": payload.get("description"),
        "industry_name": resolve_industry("adzuna", payload),
        **salary_info,
    }

def adapt_usajobs(payload: dict) -> dict:
    descriptor = payload.get("MatchedObjectDescriptor", {}) or {}
    salary_info = parse_usajobs_salary(descriptor)

    org_name = descriptor.get("OrganizationName") or descriptor.get("DepartmentName", "Unknown")
    location_list = descriptor.get("PositionLocation") or []
    location = location_list[0].get("LocationName") if location_list else None

    description = build_description_text(descriptor)

    return {
        "raw_title": descriptor.get("PositionTitle", ""),
        "company_name": org_name,
        "location": location,
        "created_str": descriptor.get("PublicationStartDate"),
        "description": description or None,
        "industry_name": resolve_industry("usajobs", payload),
        **salary_info,
    }


def build_description_text(descriptor: dict) -> str:
    """PositionFormattedDescription is a LIST of labeled sections
    (e.g. Duties, Requirements), not a plain string — flatten it."""
    parts = []

    qualification_summary = descriptor.get("QualificationSummary")
    if isinstance(qualification_summary, str):
        parts.append(qualification_summary)

    formatted = descriptor.get("PositionFormattedDescription")
    if isinstance(formatted, list):
        for section in formatted:
            if isinstance(section, dict):
                label_desc = section.get("LabelDescription")
                if isinstance(label_desc, str):
                    parts.append(label_desc)
    elif isinstance(formatted, str):
        parts.append(formatted)

    return " ".join(parts)