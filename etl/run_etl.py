from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from database.connection import get_session
from database.models import RawPosting, Industry, Company, JobTitleNormalized, JobPosting

from etl.salary_parser import parse_salary
from etl.title_normalizer import normalize_title
from etl.industry_mapper import resolve_industry

COUNTRY = "us"

def get_or_create(session, model, lookup: dict, defaults: dict | None = None):
    instance = session.execute(select(model).filter_by(**lookup)).scalar_one_or_none()
    if instance:
        return instance
    instance = model(**lookup, **(defaults or {}))
    session.add(instance)
    session.flush()
    return instance

def parse_created_date(created_str: str | None):
    if not created_str:
        return None
    try:
        return datetime.fromisoformat(created_str.replace("Z", "+00:00")).date()
    except ValueError:
        return None

def run_etl():
    with get_session() as session:
        raw_rows = session.execute(select(RawPosting).where(RawPosting.source == "adzuna")).scalars().all()
        print(f"Processing {len(raw_rows)} raw postings...")
        processed = 0

        for row in raw_rows:
            payload = row.payload

            industry = get_or_create(session, Industry, lookup={"name": resolve_industry(payload)})

            company_name = (payload.get("company") or {}).get("display_name", "Unknown")
            company = get_or_create(session, Company, lookup={"name": company_name}, defaults={"industry_id": industry.id})

            canonical_title, family = normalize_title(payload.get("title", ""))
            title_obj = get_or_create(session, JobTitleNormalized, lookup={"canonical_title": canonical_title}, defaults={"family": family})

            salary_info = parse_salary(payload, COUNTRY)

            stmt = pg_insert(JobPosting).values(
                source="adzuna",
                external_id=row.external_id,
                company_id=company.id,
                title_id=title_obj.id,
                raw_title=payload.get("title", ""),
                location=(payload.get("location") or {}).get("display_name"),
                posted_date=parse_created_date(payload.get("created")),
                raw_description=payload.get("description"),
                **salary_info,
            ).on_conflict_do_nothing(index_elements=["source", "external_id"])
            session.execute(stmt)
            processed += 1

            if processed % 200 == 0:
                session.commit()
                print(f"  ...{processed} processed")

        session.commit()
        print(f"Done. {processed} postings processed into the warehouse tables.")

if __name__ == "__main__":
    run_etl()