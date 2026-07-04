from datetime import datetime, date

from sqlalchemy import (
    String, Text, Numeric, Date, DateTime, ForeignKey, Float, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class RawPosting(Base):
    """Landing table — every Adzuna API response stored untouched."""
    __tablename__ = "raw_postings"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)  # will just be "adzuna" for now
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_raw_postings_source_external_id"),
    )


class Industry(Base):
    __tablename__ = "industries"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    companies: Mapped[list["Company"]] = relationship(back_populates="industry")


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry_id: Mapped[int | None] = mapped_column(ForeignKey("industries.id"))
    size: Mapped[str | None] = mapped_column(String(50))

    industry: Mapped["Industry"] = relationship(back_populates="companies")
    postings: Mapped[list["JobPosting"]] = relationship(back_populates="company")


class JobTitleNormalized(Base):
    __tablename__ = "job_titles_normalized"
    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_title: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    family: Mapped[str | None] = mapped_column(String(100))
    postings: Mapped[list["JobPosting"]] = relationship(back_populates="title")


class JobPosting(Base):
    __tablename__ = "job_postings"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"))
    title_id: Mapped[int | None] = mapped_column(ForeignKey("job_titles_normalized.id"))
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_title: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    salary_min: Mapped[float | None] = mapped_column(Numeric(12, 2))
    salary_max: Mapped[float | None] = mapped_column(Numeric(12, 2))
    salary_is_predicted: Mapped[bool | None] = mapped_column()
    currency: Mapped[str | None] = mapped_column(String(10))
    posted_date: Mapped[date | None] = mapped_column(Date)
    raw_description: Mapped[str | None] = mapped_column(Text)

    company: Mapped["Company"] = relationship(back_populates="postings")
    title: Mapped["JobTitleNormalized"] = relationship(back_populates="postings")
    skills: Mapped[list["JobSkill"]] = relationship(back_populates="posting")

    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_job_postings_source_external_id"),
    )


class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    postings: Mapped[list["JobSkill"]] = relationship(back_populates="skill")


class JobSkill(Base):
    __tablename__ = "job_skills"
    job_posting_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), primary_key=True)
    confidence: Mapped[float | None] = mapped_column(Float)

    posting: Mapped["JobPosting"] = relationship(back_populates="skills")
    skill: Mapped["Skill"] = relationship(back_populates="postings")