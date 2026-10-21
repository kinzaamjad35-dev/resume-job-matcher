"""Curated skills taxonomy and skill extraction.

Each canonical skill maps to a category and a list of aliases. Matching is
case-insensitive and uses word boundaries so that, for example, "R" does not
match inside "React".
"""
from __future__ import annotations

import re
from functools import lru_cache

TAXONOMY: dict[str, dict[str, list[str]]] = {
    "Programming": {
        "Python": ["python"], "R": [r"\bR\b(?! ?&)", "rstudio"], "SQL": ["sql"],
        "Java": [r"java(?!script)"], "JavaScript": ["javascript", r"\bjs\b"],
        "TypeScript": ["typescript", r"\bts\b"], "C++": [r"c\+\+"], "C#": [r"c#", r"\.net"],
        "Go": ["golang", r"\bgo\b(?= ?(?:lang|developer|services|microservices))"],
        "Bash": ["bash", "shell scripting"], "Scala": ["scala"], "PHP": ["php"],
        "HTML": ["html", "html5"], "CSS": ["css", "css3", "sass", "scss"],
    },
    "Data and ML": {
        "Machine Learning": ["machine learning", r"\bml\b"],
        "Deep Learning": ["deep learning", "neural network", "neural networks"],
        "NLP": ["nlp", "natural language processing", "text classification"],
        "Computer Vision": ["computer vision", "image classification", "object detection"],
        "Time-Series Forecasting": ["time-series", "time series", "forecasting"],
        "Statistics": ["statistics", "statistical", "hypothesis testing", "a/b testing", "a/b test"],
        "Data Analysis": ["data analysis", "exploratory data analysis", r"\beda\b", "analytics"],
        "Data Visualization": ["data visualization", "data visualisation", "visualisation", "dashboards", "dashboard"],
        "Feature Engineering": ["feature engineering"],
        "LLMs": ["llm", "llms", "large language model", "large language models", "gpt", "rag",
                 "retrieval-augmented", "prompt engineering"],
        "MLOps": ["mlops", "model deployment", "model monitoring", "mlflow"],
    },
    "Libraries": {
        "pandas": ["pandas"], "NumPy": ["numpy"], "scikit-learn": ["scikit-learn", "sklearn"],
        "TensorFlow": ["tensorflow", "keras"], "PyTorch": ["pytorch", "torch"],
        "XGBoost": ["xgboost"], "LightGBM": ["lightgbm"], "Hugging Face": ["hugging face", "huggingface", "transformers"],
        "spaCy": ["spacy"], "Matplotlib": ["matplotlib", "seaborn"], "Plotly": ["plotly"],
        "Streamlit": ["streamlit"], "FastAPI": ["fastapi"], "Flask": ["flask"], "Django": ["django"],
        "React": ["react", "react.js", "reactjs"], "Next.js": ["next.js", "nextjs"],
        "Vue": ["vue", "vue.js"], "Angular": ["angular"], "Node.js": ["node.js", "nodejs", r"\bnode\b"],
        "Tailwind CSS": ["tailwind"], "Redux": ["redux"], "Jest": ["jest"], "Spark": ["spark", "pyspark"],
    },
    "Data platforms": {
        "PostgreSQL": ["postgresql", "postgres"], "MySQL": ["mysql"], "MongoDB": ["mongodb"],
        "Redis": ["redis"], "Snowflake": ["snowflake"], "BigQuery": ["bigquery"],
        "Airflow": ["airflow"], "dbt": [r"\bdbt\b"], "Excel": ["excel", "spreadsheets"],
        "Power BI": ["power bi", "powerbi"], "Tableau": ["tableau"], "ETL": ["etl", "data pipelines", "data pipeline"],
    },
    "Cloud and DevOps": {
        "AWS": ["aws", "amazon web services", r"\bec2\b", r"\bs3\b", "lambda"], "Azure": ["azure"],
        "GCP": ["gcp", "google cloud"], "Docker": ["docker", "containers", "containerisation", "containerization"],
        "Kubernetes": ["kubernetes", r"\bk8s\b", r"\beks\b", r"\bgke\b"], "Terraform": ["terraform"],
        "Ansible": ["ansible"], "CI/CD": ["ci/cd", "continuous integration", "github actions", "jenkins", "gitlab ci"],
        "Linux": ["linux", "ubuntu"], "Git": [r"\bgit\b", "github", "gitlab"],
        "Prometheus": ["prometheus"], "Grafana": ["grafana"], "Monitoring": ["monitoring", "observability"],
        "Networking": ["networking", "dns", "tcp/ip", "load balancing", "load balancers"],
        "REST APIs": ["rest api", "rest apis", "restful", r"\bapi\b", r"\bapis\b"], "GraphQL": ["graphql"],
        "Microservices": ["microservices"], "Security": ["security", "iam", "devsecops"],
    },
    "Design and product": {
        "UI/UX": ["ui/ux", "user experience", "user interface", "ux design", "ui design"],
        "Figma": ["figma"], "Responsive Design": ["responsive design", "responsive", "mobile-first"],
        "Accessibility": ["accessibility", "wcag", "a11y"], "Testing": ["unit testing", "unit tests", "pytest", "test automation", "testing"],
        "Agile": ["agile", "scrum", "kanban", "sprint"], "Project Management": ["project management", "jira"],
    },
    "Business": {
        "SEO": ["seo", "search engine optimisation", "search engine optimization"],
        "Content Marketing": ["content marketing", "content strategy", "copywriting"],
        "Social Media": ["social media", "instagram", "linkedin ads", "tiktok"],
        "Google Analytics": ["google analytics", r"\bga4\b"], "Paid Advertising": ["google ads", "paid search", "ppc", "paid social", "meta ads"],
        "Email Marketing": ["email marketing", "mailchimp", "hubspot"], "CRM": ["crm", "salesforce"],
        "Budgeting": ["budgeting", "budget management", "forecast budgets"],
        "Accounting": ["accounting", "bookkeeping", "ifrs", "reconciliation", "reconciliations", "general ledger"],
        "Financial Reporting": ["financial reporting", "financial statements", "month-end close"],
        "Communication": ["communication", "presentation skills", "stakeholder management", "stakeholders"],
        "Leadership": ["leadership", "mentoring", "mentored", "team lead", "managed a team"],
    },
}

SKILL_CATEGORY = {skill: cat for cat, skills in TAXONOMY.items() for skill in skills}


@lru_cache(maxsize=1)
def _compiled() -> list[tuple[str, re.Pattern]]:
    out = []
    for cat, skills in TAXONOMY.items():
        for skill, aliases in skills.items():
            parts = []
            for a in aliases:
                is_regex = any(ch in a for ch in "\\(?")
                body = a if is_regex else re.escape(a)
                parts.append(body if is_regex else rf"(?<![\w]){body}(?![\w])")
            flags = 0 if skill == "R" else re.IGNORECASE
            out.append((skill, re.compile("|".join(parts), flags)))
    return out


def extract_skills(text: str) -> dict[str, int]:
    """Return {canonical skill: number of mentions} found in text."""
    found: dict[str, int] = {}
    for skill, pattern in _compiled():
        n = len(pattern.findall(text))
        if n:
            found[skill] = n
    return found
