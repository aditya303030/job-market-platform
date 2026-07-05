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


def load_cache(session, model, key_field):
    rows = session.execute(select(model)).scalars().all()
    return {getattr(row, key_field): row for row in rows}


def get_or_create_cached(session, cache, model, key, lookup, defaults=None):
    if key in cache:
        return cache[key]
    instance = model(**lookup, **(defaults or {}))
    session.add(instance)
    session.flush()
    cache[key] = instance
    return instance


def parse_created_date(created_str):
    if not created_str:
        return None
    try:
        return datetime.fromisoformat(created_str.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def run_etl():
    with get_session() as session:
        industry_cache = load_cache(session, Industry, "name")
        company_cache = load_cache(session, Company, "name")
        title_cache = load_cache(session, JobTitleNormalized, "canonical_title")

        raw_rows = session.execute(select(RawPosting)).scalars().all()
        print(f"Processing {len(raw_rows)} raw postings across all sources...")
        processed = 0

        for row in raw_rows:
            if row.source == "adzuna":
                fields = adapt_adzuna(row.payload, COUNTRY)
            elif row.source == "usajobs":
                fields = adapt_usajobs(row.payload)
            else:
                continue  # unknown source — skip rather than guess

            industry = get_or_create_cached(
                session, industry_cache, Industry, fields["industry_name"],
                lookup={"name": fields["industry_name"]},
            )
            company = get_or_create_cached(
                session, company_cache, Company, fields["company_name"],
                lookup={"name": fields["company_name"]}, defaults={"industry_id": industry.id},
            )
            canonical_title, family = normalize_title(fields["raw_title"])
            title_obj = get_or_create_cached(
                session, title_cache, JobTitleNormalized, canonical_title,
                lookup={"canonical_title": canonical_title}, defaults={"family": family},
            )

            stmt = pg_insert(JobPosting).values(
                source=row.source,
                external_id=row.external_id,
                company_id=company.id,
                title_id=title_obj.id,
                raw_title=fields["raw_title"],
                location=fields["location"],
                posted_date=parse_created_date(fields["created_str"]),
                raw_description=fields["description"],
                salary_min=fields["salary_min"],
                salary_max=fields["salary_max"],
                currency=fields["currency"],
                salary_is_predicted=fields["salary_is_predicted"],
            ).on_conflict_do_nothing(index_elements=["source", "external_id"])
            session.execute(stmt)
            processed += 1

            if processed % 500 == 0:
                session.commit()
                print(f"  ...{processed}/{len(raw_rows)} processed")

        session.commit()
        print(f"Done. {processed} postings processed.")


if __name__ == "__main__":
    run_etl()