"""Capture README screenshots and the demo GIF from a running app.
Run:  streamlit run app.py --server.port 8611  then  python tools/capture.py"""
import os
import sys

from PIL import Image
from playwright.sync_api import sync_playwright

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
URL = os.environ.get("APP_URL", "http://localhost:8611")
CHROME = os.environ.get("CHROME", "/usr/bin/google-chrome")
OUT = "docs/screenshots"
os.makedirs(OUT, exist_ok=True)
shots = []


def wait(page):
    page.wait_for_timeout(1500)
    page.wait_for_function("() => !document.querySelector('[data-testid=\"stStatusWidget\"]')", timeout=120000)
    page.wait_for_timeout(1500)


def scroll_to(page, y):
    page.evaluate("""y => { for (const el of document.querySelectorAll('*')) {
        if (el.scrollHeight > el.clientHeight + 50 && getComputedStyle(el).overflowY.match(/auto|scroll/)) el.scrollTop = y; }
        window.scrollTo(0, y); }""", y)
    page.wait_for_timeout(700)


def snap(page, name):
    path = f"{OUT}/{name}.png"
    page.screenshot(path=path)
    shots.append(path)
    print("saved", path)


with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.goto(URL); wait(page)
    scroll_to(page, 330)
    snap(page, "Match_Overview")
    for tab, name in [("Skills and learning plan", "Skills_and_Learning_Plan"), ("Keyword optimisation", "Keyword_Optimisation"),
                      ("ATS check", "ATS_Check"), ("Bullet improver", "Bullet_Improver"), ("Experience fit", "Experience_Fit")]:
        page.get_by_role("tab", name=tab).click(); page.wait_for_timeout(1500)
        scroll_to(page, 330)
        snap(page, name)
    for path, name, scroll in [("Compare_Jobs", "Compare_Jobs", 420), ("Recruiter_Mode", "Recruiter_Mode", 260), ("Evaluation", "Evaluation", 0)]:
        page.goto(f"{URL}/{path}"); wait(page)
        if scroll:
            scroll_to(page, scroll)
        snap(page, name)
    b.close()

frames = [Image.open(s).convert("RGB").resize((1080, 675), Image.LANCZOS) for s in shots]
pal = [f.quantize(colors=200, method=Image.Quantize.MEDIANCUT) for f in frames]
pal[0].save("docs/demo.gif", save_all=True, append_images=pal[1:], duration=2200, loop=0, optimize=True)
print("saved docs/demo.gif", len(frames), "frames")
sys.exit(0)
