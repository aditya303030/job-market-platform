"""
Reads every job posting's title + description, matches skills from the
taxonomy, and populates skills and job_skills. Safe to re-run — existing
skill rows are reused, and job_skills uses the same idempotent upsert
pattern as ingestion and ETL.

Usage:
    python -m nlp.run_extraction
"""

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from database.connection import get_session
from database.models import JobPosting, Skill, JobSkill
from nlp.skill_taxonomy import SKILL_TAXONOMY
from nlp.extraction import extract_skills


def ensure_skills_exist(session) -> dict[str, int]:
    """Inserts any taxonomy skills not already in the skills table,
    then returns a {skill_name: skill_id} lookup for the whole taxonomy."""
    existing = session.execute(select(Skill)).scalars().all()
    existing_names = {s.name for s in existing}

    for skill_name, category in SKILL_TAXONOMY:
        if skill_name not in existing_names:
            session.add(Skill(name=skill_name, category=category))

    session.commit()

    all_skills = session.execute(select(Skill)).scalars().all()
    return {s.name: s.id for s in all_skills}


def run_extraction():
    with get_session() as session:
        skill_id_by_name = ensure_skills_exist(session)
        print(f"{len(skill_id_by_name)} skills in taxonomy.")

        postings = session.execute(
            select(JobPosting.id, JobPosting.raw_title, JobPosting.raw_description)
        ).all()
        print(f"Scanning {len(postings)} postings for skill mentions...")

        processed = 0
        total_matches = 0

        for posting_id, raw_title, raw_description in postings:
            combined_text = f"{raw_title or ''} {raw_description or ''}"
            matched_skills = extract_skills(combined_text)

            for skill_name in matched_skills:
                skill_id = skill_id_by_name[skill_name]
                stmt = pg_insert(JobSkill).values(
                    job_posting_id=posting_id,
                    skill_id=skill_id,
                    confidence=1.0,   # exact keyword match — always 1.0 for now
                ).on_conflict_do_nothing(
                    index_elements=["job_posting_id", "skill_id"]
                )
                session.execute(stmt)
                total_matches += 1

            processed += 1
            if processed % 500 == 0:
                session.commit()
                print(f"  ...{processed}/{len(postings)} postings scanned")

        session.commit()
        print(f"Done. {processed} postings scanned, {total_matches} skill matches inserted.")


if __name__ == "__main__":
    run_extraction()