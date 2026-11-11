from playwright.sync_api import sync_playwright

def run_cuj(page):
    page.goto("http://localhost:3000")
    page.wait_for_timeout(2000)

    # Hover the "Run one tick" button to see tooltip before clicking
    button = page.get_by_role("button", name="Run one tick")
    button.hover()
    page.wait_for_timeout(1000)

    # Click the button (should trigger isTicking)
    button.click()
    page.wait_for_timeout(100) # Short wait, then hover to see "Executing tick..." tooltip

    # Hover again while it's ticking
    button.hover()
    page.wait_for_timeout(500)
    page.screenshot(path="/home/jules/verification/screenshots/verification.png")

    page.wait_for_timeout(1000)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos",
            viewport={"width": 1280, "height": 720}
        )

        # Route to mock API responses since backend might not be fully running/configured
        context.route("**/api/agents", lambda route: route.fulfill(status=200, json=[
            {"name": "Agent1", "title": "Test Agent", "model": "gpt-4o-mini", "tools": [], "schedule": {"run_every_n_ticks": 1, "phase_offset": 0}, "description": "Test"}
        ]))
        context.route("**/api/status", lambda route: route.fulfill(status=200, json={"tick": 1, "status": "running"}))
        context.route("**/api/messages*", lambda route: route.fulfill(status=200, json=[]))

        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
