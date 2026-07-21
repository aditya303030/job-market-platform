import os
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
st.set_page_config(page_title="Job Market Explorer", layout="wide")

MIN_SKILLS_FOR_JOB_DISPLAY = 3   # a job title needs at least this many distinct
                                   # skill matches to be worth showing a chart for
CHART_TEMPLATE = "plotly_white"


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
        df = pd.read_sql(text(query), conn, params=params or {})
    # Postgres NUMERIC columns come back as Decimal via psycopg2 — cast to
    # float so plotly's sizing/coloring math doesn't choke on them.
    for col in df.columns:
        if "salary" in col or "pct_" in col:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


st.title("Job Market Explorer")
st.caption("Live data from Adzuna and USAJOBS, aggregated by industry, job title, and skill.")

tab1, tab2 = st.tabs(["Industry Overview", "Jobs & Skills Drill-down"])

# ---------------------------------------------------------------------------
# TAB 1 — Industry overview
# ---------------------------------------------------------------------------
with tab1:
    industries = run_query("SELECT * FROM industry_stats ORDER BY posting_count DESC")

    col1, col2, col3 = st.columns(3)
    col1.metric("Industries covered", len(industries))
    col2.metric("Total postings analyzed", f"{int(industries['posting_count'].sum()):,}")
    col3.metric("Highest avg. salary", f"${industries['avg_salary'].max():,.0f}")

    st.subheader("Industries by hiring volume")
    fig_volume = px.bar(
        industries.sort_values("posting_count").tail(15),
        x="posting_count", y="industry_name", orientation="h",
        template=CHART_TEMPLATE,
        labels={"posting_count": "Number of postings", "industry_name": ""},
        hover_data={"avg_salary": ":$,.0f", "posting_count": ":,"},
    )
    fig_volume.update_traces(marker_color="#3b82f6")
    fig_volume.update_layout(height=520, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_volume, use_container_width=True)

    st.subheader("Pay vs. hiring volume — which industries are both hot and lucrative")
    fig_scatter = px.scatter(
        industries, x="posting_count", y="avg_salary", text="industry_name",
        size="posting_count", size_max=45, color="avg_salary",
        color_continuous_scale="Sunset", template=CHART_TEMPLATE,
        labels={"posting_count": "Hiring volume (postings)", "avg_salary": "Average salary ($)"},
        hover_data={"posting_count": ":,", "avg_salary": ":$,.0f"},
    )
    fig_scatter.update_traces(textposition="top center")
    fig_scatter.update_layout(height=550, margin=dict(l=10, r=10, t=10, b=10), coloraxis_showscale=False)
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.caption("Top-right = hiring a lot AND paying well. Bottom-left = neither.")

    st.subheader("Average vs. median salary — where pay is skewed by outliers")
    salary_compare = industries.sort_values("avg_salary", ascending=False).head(12).melt(
        id_vars="industry_name", value_vars=["avg_salary", "median_salary"],
        var_name="metric", value_name="salary",
    )
    salary_compare["metric"] = salary_compare["metric"].map(
        {"avg_salary": "Average", "median_salary": "Median"}
    )
    fig_compare = px.bar(
        salary_compare, x="salary", y="industry_name", color="metric",
        barmode="group", orientation="h", template=CHART_TEMPLATE,
        color_discrete_map={"Average": "#3b82f6", "Median": "#f97316"},
        labels={"salary": "Salary ($)", "industry_name": "", "metric": ""},
    )
    fig_compare.update_layout(height=500, margin=dict(l=10, r=10, t=10, b=10), legend_title=None)
    st.plotly_chart(fig_compare, use_container_width=True)
    st.caption("A big gap between average and median means a few very high (or low) salaries are pulling the average away from what's typical.")

# ---------------------------------------------------------------------------
# TAB 2 — Drill-down: industry → job titles → skills
# ---------------------------------------------------------------------------
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
        jc1, jc2 = st.columns(2)
        jc1.metric("Job titles found", len(jobs))
        jc2.metric("Top-paying title", jobs.sort_values("avg_salary", ascending=False).iloc[0]["canonical_title"])

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**Most in-demand titles (by postings)**")
            fig_jobs_volume = px.bar(
                jobs.sort_values("posting_count").tail(12),
                x="posting_count", y="canonical_title", orientation="h",
                template=CHART_TEMPLATE,
                labels={"posting_count": "Postings", "canonical_title": ""},
                hover_data={"avg_salary": ":$,.0f"},
            )
            fig_jobs_volume.update_traces(marker_color="#3b82f6")
            fig_jobs_volume.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_jobs_volume, use_container_width=True)

        with col_b:
            st.markdown("**Highest-paying titles**")
            fig_jobs_pay = px.bar(
                jobs.sort_values("avg_salary").tail(12),
                x="avg_salary", y="canonical_title", orientation="h",
                template=CHART_TEMPLATE,
                labels={"avg_salary": "Average salary ($)", "canonical_title": ""},
                hover_data={"posting_count": ":,"},
            )
            fig_jobs_pay.update_traces(marker_color="#10b981")
            fig_jobs_pay.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_jobs_pay, use_container_width=True)

        st.markdown("**Pay vs. demand for titles in this industry**")
        fig_job_scatter = px.scatter(
            jobs, x="posting_count", y="avg_salary", text="canonical_title",
            size="posting_count", size_max=40, color="avg_salary",
            color_continuous_scale="Sunset", template=CHART_TEMPLATE,
            labels={"posting_count": "Postings", "avg_salary": "Average salary ($)"},
        )
        fig_job_scatter.update_traces(textposition="top center")
        fig_job_scatter.update_layout(height=480, margin=dict(l=10, r=10, t=10, b=10), coloraxis_showscale=False)
        st.plotly_chart(fig_job_scatter, use_container_width=True)

        # ---------------------------------------------------------------
        # Skill drill-down for a chosen job title, filtered to titles that
        # actually have enough skill signal to be worth charting
        # ---------------------------------------------------------------
        skill_counts = run_query(
            "SELECT title_id, COUNT(DISTINCT skill_id) AS skill_count FROM skill_stats_by_job GROUP BY title_id"
        )
        jobs_with_counts = jobs.merge(skill_counts, on="title_id", how="left")
        jobs_with_counts["skill_count"] = jobs_with_counts["skill_count"].fillna(0)

        eligible_jobs = jobs_with_counts[jobs_with_counts["skill_count"] >= MIN_SKILLS_FOR_JOB_DISPLAY]
        excluded_count = len(jobs_with_counts) - len(eligible_jobs)

        st.divider()
        st.subheader("Explore required skills for a job title")

        if eligible_jobs.empty:
            st.info("No job titles in this industry have enough extracted skill data yet.")
        else:
            if excluded_count > 0:
                st.caption(
                    f"{excluded_count} title(s) in this industry have posting data but fewer than "
                    f"{MIN_SKILLS_FOR_JOB_DISPLAY} distinct skills detected, so they're left out here."
                )

            selected_job = st.selectbox("Choose a job title", eligible_jobs["canonical_title"])
            title_id = int(eligible_jobs.loc[eligible_jobs["canonical_title"] == selected_job, "title_id"].iloc[0])
            sample_size = int(eligible_jobs.loc[eligible_jobs["canonical_title"] == selected_job, "posting_count"].iloc[0])

            skills = run_query(
                "SELECT * FROM skill_stats_by_job WHERE title_id = :tid ORDER BY mention_count DESC LIMIT 15",
                {"tid": title_id},
            )

            skills_sorted = skills.sort_values("pct_of_postings", ascending=True)
            chart_height = max(320, 32 * len(skills_sorted) + 120)

            fig_skills = px.bar(
                skills_sorted, x="pct_of_postings", y="skill_name", orientation="h",
                text=skills_sorted["pct_of_postings"].round(1).astype(str) + "%",
                hover_data={"mention_count": True, "pct_of_postings": ":.1f"},
                template=CHART_TEMPLATE,
                color="pct_of_postings", color_continuous_scale="Greens",
                labels={"pct_of_postings": "% of postings mentioning this skill", "skill_name": ""},
            )
            fig_skills.update_traces(textposition="outside")
            fig_skills.update_layout(
                height=chart_height, margin=dict(l=10, r=40, t=10, b=10), coloraxis_showscale=False
            )
            st.plotly_chart(fig_skills, use_container_width=True)
            st.caption(f"Based on {sample_size} postings for {selected_job}, {int(eligible_jobs.loc[eligible_jobs['canonical_title'] == selected_job, 'skill_count'].iloc[0])} distinct skills detected.")