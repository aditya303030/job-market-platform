import time
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.dialects.postgresql import insert as pg_insert

from database.connection import get_session
from database.models import RawPosting
from ingestion.clients import adzuna_client, usajobs_client
from ingestion.clients.base_client import ApiRequestError

MAX_PAGES_PER_CATEGORY = 10

LOCATIONS = ["New York", "Chicago", "Los Angeles", "Austin", "Remote"]

USAJOBS_KEYWORDS = [
    "data", "analyst", "engineer", "manager", "specialist",
    "scientist", "administrator", "officer", "technician",
    "coordinator", "director", "assistant", "clerk", "supervisor",
]
USAJOBS_MAX_PAGES = 30


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
        failed_combinations = []

        for cat in categories:
            tag = cat["tag"]
            for location in LOCATIONS:
                print(f"  Fetching Adzuna category: {tag} — {location}")
                try:
                    for job in adzuna_client.fetch_postings(
                        category=tag, where=location, max_pages=MAX_PAGES_PER_CATEGORY
                    ):
                        upsert_raw_posting(session, "adzuna", adzuna_client.external_id(job), job)
                        count += 1
                except ApiRequestError as e:
                    print(f"    SKIPPED after repeated failures: {tag} — {location} ({e})")
                    failed_combinations.append((tag, location))
                    continue

                time.sleep(1.5)  # extra pause between each category/location combo

            session.commit()

        print(f"Adzuna: processed {count} postings.")
        if failed_combinations:
            print(f"Adzuna: {len(failed_combinations)} category/location combos failed and were skipped:")
            for tag, location in failed_combinations:
                print(f"  - {tag} — {location}")


def run_usajobs():
    with get_session() as session:
        count = 0
        for keyword in USAJOBS_KEYWORDS:
            print(f"  Fetching USAJOBS keyword: {keyword}")
            try:
                for job in usajobs_client.fetch_postings(keyword=keyword, max_pages=USAJOBS_MAX_PAGES):
                    upsert_raw_posting(session, "usajobs", usajobs_client.external_id(job), job)
                    count += 1
            except ApiRequestError as e:
                print(f"    SKIPPED after repeated failures: {keyword} ({e})")
                continue
            session.commit()
        print(f"USAJOBS: processed {count} postings.")


if __name__ == "__main__":
    run_adzuna()
    run_usajobs()
    print("Done.")