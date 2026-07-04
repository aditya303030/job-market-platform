from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.dialects.postgresql import insert as pg_insert

from database.connection import get_session
from database.models import RawPosting
from ingestion.clients import adzuna_client

MAX_PAGES_PER_CATEGORY = 5  


def upsert_raw_posting(session, source: str, ext_id: str, payload: dict):
    stmt = pg_insert(RawPosting).values(
        source=source, external_id=ext_id, payload=payload,
    ).on_conflict_do_nothing(index_elements=["source", "external_id"])
    session.execute(stmt)


def run_adzuna():
    categories = adzuna_client.fetch_categories()
    print(f"Found {len(categories)} categories: {[c['tag'] for c in categories]}")

    with get_session() as session:
        count = 0
        for cat in categories:
            tag = cat["tag"]
            print(f"  Fetching category: {tag}")
            for job in adzuna_client.fetch_postings(category=tag, max_pages=MAX_PAGES_PER_CATEGORY):
                upsert_raw_posting(session, "adzuna", adzuna_client.external_id(job), job)
                count += 1
            session.commit()   # commit after each category, not just at the very end
        print(f"Adzuna: processed {count} postings across {len(categories)} categories.")


if __name__ == "__main__":
    run_adzuna()
    print("Done.")