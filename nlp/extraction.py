"""
Matches skills from SKILL_TAXONOMY against a block of text (title +
description) using case-insensitive, whole-word/phrase matching.
"""

import re

from nlp.skill_taxonomy import SKILL_TAXONOMY


def build_patterns():
    """Precompiles one regex per skill, using word boundaries so 'R'
    doesn't match inside 'Regional', and escaping special characters
    like the '+' in 'C++' or '.' in 'Node.js'."""
    patterns = {}
    for skill_name, _category in SKILL_TAXONOMY:
        escaped = re.escape(skill_name)
        pattern = re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", re.IGNORECASE)
        patterns[skill_name] = pattern
    return patterns


_PATTERNS = build_patterns()


def extract_skills(text: str) -> list[str]:
    """Returns the list of skill names (from the taxonomy) found in `text`."""
    if not text:
        return []

    found = []
    for skill_name, pattern in _PATTERNS.items():
        if pattern.search(text):
            found.append(skill_name)
    return found