"""Resume and Job Matcher: entry point and navigation."""
import streamlit as st

nav = st.navigation([
    st.Page("pages/0_Match_Analysis.py", title="Match Analysis", default=True),
    st.Page("pages/1_Compare_Jobs.py", title="Compare Jobs", url_path="Compare_Jobs"),
    st.Page("pages/2_Recruiter_Mode.py", title="Recruiter Mode", url_path="Recruiter_Mode"),
    st.Page("pages/3_Evaluation.py", title="Evaluation", url_path="Evaluation"),
])
nav.run()
