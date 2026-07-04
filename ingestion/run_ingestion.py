from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.dialects.postgresql import insert as pg_insert

from database.connection import get_session
from database.models import RawPosting
from ingestion.clients import adzuna_client

SEARCH_TERMS = ["data analyst", "data scientist", "software engineer"]
MAX_PAGES_PER_TERM = 1

def upsert_raw_posting(session, source: str, ext_id: str, payload: dict):
    stmt = pg_insert(RawPosting).values(
        source=source, external_id=ext_id, payload=payload,
    ).on_conflict_do_nothing(index_elements=["source", "external_id"])
    session.execute(stmt)

def run_adzuna():
    print("Fetching from Adzuna...")
    with get_session() as session:
        count = 0
        for term in SEARCH_TERMS:
            for job in adzuna_client.fetch_postings(what=term, max_pages=MAX_PAGES_PER_TERM):
                upsert_raw_posting(session, "adzuna", adzuna_client.external_id(job), job)
                count += 1
        session.commit()
    print(f"Adzuna: processed {count} postings.")

if __name__ == "__main__":
    run_adzuna()
    print("Done.")