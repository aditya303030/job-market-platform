from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from database.connection import get_session
from database.models import RawPosting, Industry, Company, JobTitleNormalized, JobPosting
from etl.title_normalizer import normalize_title
from etl.source_adapters import adapt_adzuna, adapt_usajobs

COUNTRY = "us"
BATCH_SIZE = 500


def load_id_cache(session, model, key_field):
    """Loads {key: id} — plain dicts, not ORM objects, so they survive
    across session swaps with no binding issues."""
    rows = session.execute(select(model.id, getattr(model, key_field))).all()
    return {key: id_ for id_, key in rows}


def get_or_create_id(session, cache, model, key, lookup, defaults=None):
    if key in cache:
        return cache[key]
    instance = model(**lookup, **(defaults or {}))
    session.add(instance)
    session.flush()
    cache[key] = instance.id
    return instance.id


def parse_created_date(created_str):
    if not created_str:
        return None
    try:
        return datetime.fromisoformat(created_str.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def process_row(session, caches, row):
    if row.source == "adzuna":
        fields = adapt_adzuna(row.payload, COUNTRY)
    elif row.source == "usajobs":
        fields = adapt_usajobs(row.payload)
    else:
        return

    industry_id = get_or_create_id(
        session, caches["industry"], Industry, fields["industry_name"],
        lookup={"name": fields["industry_name"]},
    )
    company_id = get_or_create_id(
        session, caches["company"], Company, fields["company_name"],
        lookup={"name": fields["company_name"]}, defaults={"industry_id": industry_id},
    )
    canonical_title, family = normalize_title(fields["raw_title"])
    title_id = get_or_create_id(
        session, caches["title"], JobTitleNormalized, canonical_title,
        lookup={"canonical_title": canonical_title}, defaults={"family": family},
    )

    stmt = pg_insert(JobPosting).values(
        source=row.source, external_id=row.external_id,
        company_id=company_id, title_id=title_id,
        raw_title=fields["raw_title"], location=fields["location"],
        posted_date=parse_created_date(fields["created_str"]),
        raw_description=fields["description"],
        salary_min=fields["salary_min"], salary_max=fields["salary_max"],
        currency=fields["currency"], salary_is_predicted=fields["salary_is_predicted"],
    ).on_conflict_do_nothing(index_elements=["source", "external_id"])
    session.execute(stmt)


def run_etl():
    with get_session() as session:
        raw_row_ids = session.execute(select(RawPosting.id)).scalars().all()
    print(f"Processing {len(raw_row_ids)} raw postings across all sources...")

    with get_session() as session:
        caches = {
            "industry": load_id_cache(session, Industry, "name"),
            "company": load_id_cache(session, Company, "name"),
            "title": load_id_cache(session, JobTitleNormalized, "canonical_title"),
        }

    processed = 0
    for batch_start in range(0, len(raw_row_ids), BATCH_SIZE):
        batch_ids = raw_row_ids[batch_start: batch_start + BATCH_SIZE]

        with get_session() as session:  # ← fresh connection every batch, closed at the end of this block
            rows = session.execute(select(RawPosting).where(RawPosting.id.in_(batch_ids))).scalars().all()
            for row in rows:
                process_row(session, caches, row)
                processed += 1
            session.commit()

        print(f"  ...{processed}/{len(raw_row_ids)} processed")

    print(f"Done. {processed} postings processed.")


if __name__ == "__main__":
    run_etl()