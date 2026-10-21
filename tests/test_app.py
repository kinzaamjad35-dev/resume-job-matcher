"""Headless page tests with Streamlit AppTest."""
import glob
import os

import pytest
from streamlit.testing.v1 import AppTest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGES = ["app.py"] + sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(ROOT, "pages", "*.py")))


@pytest.mark.parametrize("page", PAGES)
def test_page_runs(page):
    at = AppTest.from_file(os.path.join(ROOT, page), default_timeout=300).run()
    assert not at.exception, [e.value for e in at.exception]


def test_recruiter_must_have_filter():
    at = AppTest.from_file(os.path.join(ROOT, "pages", "2_Recruiter_Mode.py"), default_timeout=300).run()
    at.multiselect[0].set_value(["LightGBM"]).run()
    assert not at.exception
    assert any("of 8 candidates" in m.value for m in at.markdown)
