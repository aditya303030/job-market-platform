from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select, update
from database.connection import get_session
from database.models import JobPosting, JobTitleNormalized
from etl.title_normalizer import normalize_title


def run_normalize_titles():
    with get_session() as session:
        title_cache = {
            row.canonical_title: row
            for row in session.execute(select(JobTitleNormalized)).scalars().all()
        }

        distinct_raw_titles = session.execute(
            select(JobPosting.raw_title).distinct()
        ).scalars().all()
        print(f"Re-normalizing {len(distinct_raw_titles)} distinct raw titles...")

        updated = 0
        for raw_title in distinct_raw_titles:
            canonical_title, family = normalize_title(raw_title)

            title_obj = title_cache.get(canonical_title)
            if not title_obj:
                title_obj = JobTitleNormalized(canonical_title=canonical_title, family=family)
                session.add(title_obj)
                session.flush()
                title_cache[canonical_title] = title_obj

            session.execute(
                update(JobPosting)
                .where(JobPosting.raw_title == raw_title)
                .values(title_id=title_obj.id)
            )
            updated += 1

            if updated % 200 == 0:
                session.commit()
                print(f"  ...{updated}/{len(distinct_raw_titles)} titles processed")

        session.commit()
        print(f"Done. {updated} distinct titles re-normalized.")


if __name__ == "__main__":
    run_normalize_titles()