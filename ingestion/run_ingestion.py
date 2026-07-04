from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.dialects.postgresql import insert as pg_insert

from database.connection import get_session
from database.models import RawPosting
from ingestion.clients import adzuna_client, usajobs_client

MAX_PAGES_PER_CATEGORY = 5

# USAJOBS has no /categories endpoint, so we sweep broad keywords instead
# to get wide coverage across federal job types.
USAJOBS_KEYWORDS = [
    "data", "analyst", "engineer", "manager", "specialist",
    "scientist", "administrator", "officer",
]
USAJOBS_MAX_PAGES = 20


def upsert_raw_posting(session, source: str, ext_id: str, payload: dict):
    stmt = pg_insert(RawPosting).values(
        source=source, external_id=ext_id, payload=payload,
    ).on_conflict_do_nothing(index_elements=["source", "external_id"])
    session.execute(stmt)


def run_adzuna():
    categories = adzuna_client.fetch_categories()
    print(f"Adzuna: found {len(categories)} categories.")

    with get_session() as session:
        count = 0
        for cat in categories:
            tag = cat["tag"]
            print(f"  Fetching Adzuna category: {tag}")
            for job in adzuna_client.fetch_postings(category=tag, max_pages=MAX_PAGES_PER_CATEGORY):
                upsert_raw_posting(session, "adzuna", adzuna_client.external_id(job), job)
                count += 1
            session.commit()
        print(f"Adzuna: processed {count} postings.")


def run_usajobs():
    with get_session() as session:
        count = 0
        for keyword in USAJOBS_KEYWORDS:
            print(f"  Fetching USAJOBS keyword: {keyword}")
            for job in usajobs_client.fetch_postings(keyword=keyword, max_pages=USAJOBS_MAX_PAGES):
                upsert_raw_posting(session, "usajobs", usajobs_client.external_id(job), job)
                count += 1
            session.commit()
        print(f"USAJOBS: processed {count} postings.")


if __name__ == "__main__":
    run_adzuna()
    run_usajobs()
    print("Done.")