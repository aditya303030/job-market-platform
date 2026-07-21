import os
import streamlit as st
import pandas as pd
import plotly.express as px
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
        raise RuntimeError("DATABASE_URL not found in .env or Streamlit secrets.")


@st.cache_resource
def get_engine():
    return create_engine(get_database_url(), pool_pre_ping=True, pool_recycle=300)


@st.cache_data(ttl=3600)
def run_query(query: str, params: dict | None = None) -> pd.DataFrame:
    with get_engine().connect() as conn:
        return pd.read_sql(text(query), conn, params=params or {})


st.title("Job Market Explorer")
st.caption("Live data from Adzuna and USAJOBS, aggregated by industry, job title, and skill.")

tab1, tab2 = st.tabs(["Industry Overview", "Jobs & Skills Drill-down"])

with tab1:
    industries = run_query("SELECT * FROM industry_stats ORDER BY posting_count DESC")

    col1, col2 = st.columns(2)
    col1.metric("Industries covered", len(industries))
    col2.metric("Total postings analyzed", int(industries["posting_count"].sum()))

    st.subheader("Industries by hiring volume")
    fig_volume = px.bar(
        industries.sort_values("posting_count"),
        x="posting_count", y="industry_name", orientation="h",
        labels={"posting_count": "Number of postings", "industry_name": ""},
    )
    fig_volume.update_traces(marker_color="#3b82f6")
    fig_volume.update_layout(height=500, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_volume, use_container_width=True)

    st.subheader("Pay vs. hiring volume — which industries are both hot and lucrative")
    fig_scatter = px.scatter(
        industries, x="posting_count", y="avg_salary", text="industry_name",
        size="posting_count", size_max=40,
        labels={"posting_count": "Hiring volume (postings)", "avg_salary": "Average salary ($)"},
    )
    fig_scatter.update_traces(textposition="top center", marker_color="#f97316")
    fig_scatter.update_layout(height=550, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.caption("Top-right = hiring a lot AND paying well. Bottom-left = neither.")

with tab2:
    industries = run_query("SELECT * FROM industry_stats ORDER BY posting_count DESC")
    selected_industry = st.selectbox("Choose an industry", industries["industry_name"])
    industry_id = int(industries.loc[industries["industry_name"] == selected_industry, "industry_id"].iloc[0])

    jobs = run_query(
        "SELECT * FROM job_stats_by_industry WHERE industry_id = :iid ORDER BY posting_count DESC",
        {"iid": industry_id},
    )

    st.subheader(f"Job titles within {selected_industry}")
    if jobs.empty:
        st.info("No job titles with enough data for this industry yet.")
    else:
        fig_jobs = px.bar(
            jobs.sort_values("posting_count"),
            x="posting_count", y="canonical_title", orientation="h",
            color="avg_salary", color_continuous_scale="Blues",
            labels={"posting_count": "Number of postings", "canonical_title": "", "avg_salary": "Avg salary"},
        )
        fig_jobs.update_layout(height=450, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_jobs, use_container_width=True)

        selected_job = st.selectbox("Choose a job title", jobs["canonical_title"])
        title_id = int(jobs.loc[jobs["canonical_title"] == selected_job, "title_id"].iloc[0])
        sample_size = int(jobs.loc[jobs["canonical_title"] == selected_job, "posting_count"].iloc[0])

        skills = run_query(
            "SELECT * FROM skill_stats_by_job WHERE title_id = :tid ORDER BY mention_count DESC LIMIT 15",
            {"tid": title_id},
        )

        st.subheader(f"Top skills for {selected_job}")
        if skills.empty:
            st.info("Not enough skill data extracted for this title yet.")
        else:
            skills_sorted = skills.sort_values("pct_of_postings", ascending=True)
            fig_skills = px.bar(
                skills_sorted, x="pct_of_postings", y="skill_name", orientation="h",
                text=skills_sorted["pct_of_postings"].round(1).astype(str) + "%",
                hover_data={"mention_count": True, "pct_of_postings": ":.1f"},
                labels={"pct_of_postings": "% of postings mentioning this skill", "skill_name": ""},
            )
            fig_skills.update_traces(marker_color="#10b981", textposition="outside")
            fig_skills.update_layout(height=450, margin=dict(l=10, r=30, t=10, b=10))
            st.plotly_chart(fig_skills, use_container_width=True)
            st.caption(f"Based on {sample_size} postings for this title.")