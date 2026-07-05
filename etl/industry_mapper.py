GOVERNMENT_INDUSTRY_NAME = "Government / Public Sector"


def resolve_industry(source: str, payload: dict) -> str:
    if source == "adzuna":
        category = payload.get("category") or {}
        return category.get("label", "Unknown")
    elif source == "usajobs":
        return GOVERNMENT_INDUSTRY_NAME
    return "Unknown"