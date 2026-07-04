def resolve_industry(payload: dict) -> str:
    category = payload.get("category") or {}
    return category.get("label", "Unknown")