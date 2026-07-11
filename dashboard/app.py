import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

st.set_page_config(page_title="Job Market Explorer", layout="wide")


def get_database_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
    try:
        return st.secrets["DATABASE_URL"]
    except Exception:
        raise RuntimeError(
            "DATABASE_URL not found. Set it in a local .env file, "
            "or in Streamlit Cloud's Secrets under app settings."
        )


@st.cache_resource
def get_engine():
    return create_engine(get_database_url(), pool_pre_ping=True, pool_recycle=300)


@st.cache_data(ttl=3600)
def run_query(query: str, params: dict | None = None) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn, params=params or {})


st.title("Job Market Explorer")
st.caption("Live data from Adzuna and USAJOBS, aggregated by industry, job title, and skill.")

industries = run_query("SELECT * FROM industry_stats ORDER BY posting_count DESC")

st.subheader("Industries by hiring volume")
st.bar_chart(industries.set_index("industry_name")["posting_count"])

col1, col2 = st.columns(2)
with col1:
    st.metric("Industries covered", len(industries))
with col2:
    st.metric("Total postings analyzed", int(industries["posting_count"].sum()))

selected_industry = st.selectbox("Explore an industry", industries["industry_name"])
industry_id = int(industries.loc[industries["industry_name"] == selected_industry, "industry_id"].iloc[0])

jobs = run_query(
    "SELECT * FROM job_stats_by_industry WHERE industry_id = :iid ORDER BY posting_count DESC",
    {"iid": industry_id},
)

st.subheader(f"Job titles within {selected_industry}")
if jobs.empty:
    st.info("Not enough data for this industry yet.")
else:
    st.bar_chart(jobs.set_index("canonical_title")["posting_count"])

    selected_job = st.selectbox("Explore a job title", jobs["canonical_title"])
    title_id = int(jobs.loc[jobs["canonical_title"] == selected_job, "title_id"].iloc[0])

    skills = run_query(
        "SELECT * FROM skill_stats_by_job WHERE title_id = :tid ORDER BY mention_count DESC LIMIT 15",
        {"tid": title_id},
    )

    st.subheader(f"Top skills for {selected_job}")
    if skills.empty:
        st.info("Not enough skill data extracted for this title yet.")
    else:
        st.bar_chart(skills.set_index("skill_name")["pct_of_postings"])
        sample_size = int(jobs.loc[jobs["canonical_title"] == selected_job, "posting_count"].iloc[0])
        st.caption(f"Based on {sample_size} postings for this title.")