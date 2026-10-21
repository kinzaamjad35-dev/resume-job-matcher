"""Curated, offline learning notes for skill gaps (no web calls)."""
from __future__ import annotations

from .skills import SKILL_CATEGORY

NOTES = {
    "Python": "Core syntax, functions, classes and virtual environments; practise with small automation scripts.",
    "SQL": "SELECT, JOINs, GROUP BY and window functions; practise on a public dataset in PostgreSQL or SQLite.",
    "JavaScript": "ES6+ syntax, async/await, DOM manipulation and modules.",
    "TypeScript": "Types, interfaces and generics; convert a small JavaScript project to TypeScript.",
    "Machine Learning": "Supervised learning, train/test splits, cross-validation and evaluation metrics with scikit-learn.",
    "Deep Learning": "Neural network basics, back-propagation and training loops in PyTorch; build an image or text classifier.",
    "NLP": "Tokenisation, embeddings and transformer models; fine-tune a small Hugging Face model for classification.",
    "Computer Vision": "CNNs, transfer learning and data augmentation; train a classifier on a public image dataset.",
    "Time-Series Forecasting": "Trend, seasonality, lag features and time-based validation; compare a baseline with gradient boosting.",
    "Statistics": "Distributions, confidence intervals, hypothesis tests and A/B test design.",
    "Data Visualization": "Choosing the right chart and building dashboards with Plotly, Streamlit, Power BI or Tableau.",
    "LLMs": "Prompt design, embeddings and retrieval-augmented generation; build a document Q&A prototype.",
    "MLOps": "Model versioning, experiment tracking (MLflow), containerised serving and monitoring for drift.",
    "pandas": "DataFrames, groupby, merges and reshaping; clean a messy CSV end to end.",
    "scikit-learn": "Pipelines, preprocessing, model selection and GridSearchCV.",
    "TensorFlow": "Keras Sequential and Functional APIs; train and save a model.",
    "PyTorch": "Tensors, Dataset/DataLoader and writing a training loop.",
    "Spark": "DataFrames, transformations vs actions and partitioning with PySpark.",
    "React": "Components, props, state, hooks (useState, useEffect) and routing; build a small multi-page app.",
    "Next.js": "File-based routing, server components and data fetching; deploy a project on Vercel.",
    "Node.js": "Express servers, middleware, async I/O and connecting to a database.",
    "Redux": "Store, slices and selectors with Redux Toolkit.",
    "Jest": "Unit tests, mocks and component tests with React Testing Library.",
    "Tailwind CSS": "Utility classes, responsive breakpoints and theming.",
    "AWS": "Core services (EC2, S3, IAM, Lambda, RDS); aim for the AWS Cloud Practitioner or Solutions Architect Associate.",
    "Azure": "Core services and identity; the AZ-900 fundamentals certification is a good start.",
    "GCP": "Compute Engine, Cloud Storage, BigQuery and IAM; Google Cloud Digital Leader is an entry certificate.",
    "Docker": "Images, Dockerfiles, volumes and docker compose; containerise one of your projects.",
    "Kubernetes": "Pods, deployments, services and Helm; practise locally with kind or minikube.",
    "Terraform": "Providers, resources, state and modules; provision a small cloud environment as code.",
    "Ansible": "Inventories, playbooks and roles for configuration management.",
    "CI/CD": "Automated test and deploy pipelines with GitHub Actions; add one to an existing repository.",
    "Linux": "Command line, permissions, processes, systemd and shell scripting.",
    "Prometheus": "Metrics, exporters and PromQL queries.",
    "Grafana": "Dashboards and alerting on top of Prometheus or other data sources.",
    "REST APIs": "HTTP methods, status codes and API design; build an API with FastAPI or Express.",
    "GraphQL": "Schemas, queries, mutations and resolvers.",
    "Airflow": "DAGs, operators and scheduling for data pipelines.",
    "dbt": "Models, tests and documentation for SQL transformations.",
    "Power BI": "Data modelling, DAX measures and report publishing.",
    "Tableau": "Calculated fields, dashboards and storytelling; Tableau Public is free.",
    "Accessibility": "WCAG 2.2 guidelines, semantic HTML, ARIA and keyboard navigation testing.",
    "Testing": "Unit and integration tests, test coverage and test-driven development.",
    "Agile": "Scrum roles, sprints and user stories; the Scrum Guide is free online.",
    "SEO": "Keyword research, on-page optimisation and technical SEO audits.",
    "Google Analytics": "GA4 events, conversions and reporting; Google offers a free certification.",
    "Paid Advertising": "Campaign structure, bidding and conversion tracking in Google Ads and Meta Ads.",
    "Accounting": "Double-entry bookkeeping, reconciliations and IFRS basics.",
    "Financial Reporting": "Preparing income statements, balance sheets and month-end close procedures.",
}
CATEGORY_NOTES = {
    "Programming": "Work through the official documentation and complete one small project in the language.",
    "Data and ML": "Take a structured course module on the topic and apply it to a public dataset.",
    "Libraries": "Follow the official getting-started tutorial and use it in a portfolio project.",
    "Data platforms": "Use the free tier or community edition to build a small end-to-end example.",
    "Cloud and DevOps": "Use a free-tier account to deploy a small project using this tool.",
    "Design and product": "Study the core principles and apply them to an existing project.",
    "Business": "Complete a short introductory course and document a practical case study.",
}


def learning_note(skill: str) -> str:
    return NOTES.get(skill) or CATEGORY_NOTES.get(SKILL_CATEGORY.get(skill, ""), "Study the fundamentals and apply them in a small project.")
