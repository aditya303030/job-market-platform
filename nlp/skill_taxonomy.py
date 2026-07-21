"""
Reference list of skills to search for in job descriptions.
Extend this over time as you notice gaps — it directly controls
what your "top skills for this job" charts can ever show.
"""

SKILL_TAXONOMY = [
    # Programming languages
    ("Python", "language"),
    ("SQL", "language"),
    ("R", "language"),
    ("Java", "language"),
    ("JavaScript", "language"),
    ("C++", "language"),
    ("Scala", "language"),

    # Data / analytics tools
    ("Excel", "tool"),
    ("Tableau", "tool"),
    ("Power BI", "tool"),
    ("Looker", "tool"),
    ("SAS", "tool"),
    ("SPSS", "tool"),
    ("Microsoft Office", "tool"),
    ("data entry", "tool"),

    # Cloud / infrastructure
    ("AWS", "cloud"),
    ("Azure", "cloud"),
    ("Google Cloud", "cloud"),
    ("Docker", "cloud"),
    ("Kubernetes", "cloud"),
    ("Snowflake", "cloud"),

    # Data engineering / ML
    ("Spark", "framework"),
    ("Hadoop", "framework"),
    ("Airflow", "framework"),
    ("TensorFlow", "framework"),
    ("PyTorch", "framework"),
    ("scikit-learn", "framework"),
    ("machine learning", "concept"),
    ("deep learning", "concept"),
    ("natural language processing", "concept"),
    ("ETL", "concept"),
    ("data warehousing", "concept"),
    ("data modeling", "concept"),

    # Web / software engineering
    ("React", "framework"),
    ("Node.js", "framework"),
    ("REST API", "concept"),
    ("Git", "tool"),
    ("CI/CD", "concept"),
    ("Agile", "concept"),
    ("Scrum", "concept"),

    # Business / soft skills
    ("communication", "soft_skill"),
    ("project management", "soft_skill"),
    ("stakeholder management", "soft_skill"),
    ("leadership", "soft_skill"),
    ("problem solving", "soft_skill"),
    ("time management", "soft_skill"),
    ("attention to detail", "soft_skill"),
    ("customer service", "soft_skill"),
    ("teamwork", "soft_skill"),
    ("multitasking", "soft_skill"),
    ("organizational skills", "soft_skill"),

    # Finance / analyst-specific
    ("financial modeling", "concept"),
    ("forecasting", "concept"),
    ("budgeting", "concept"),
    ("Salesforce", "tool"),
    ("bookkeeping", "concept"),
    ("accounts payable", "concept"),
    ("accounts receivable", "concept"),

    # Security
    ("cybersecurity", "concept"),
    ("penetration testing", "concept"),
    ("network security", "concept"),

    # Operations / warehouse / retail
    ("inventory management", "concept"),
    ("supply chain", "concept"),
    ("forklift", "tool"),
    ("point of sale", "tool"),
    ("scheduling", "concept"),
    ("quality control", "concept"),

    # Healthcare
    ("patient care", "concept"),
    ("HIPAA", "concept"),
    ("electronic health records", "tool"),

    # Certifications
    ("CPA", "certification"),
    ("PMP", "certification"),
    ("Six Sigma", "certification"),
]