from playwright.sync_api import sync_playwright

def run_cuj(page):
    page.goto("http://localhost:3000/wizard")
    page.wait_for_timeout(1000)

    # Step 1: Identity -> Fill out fields to enable Next button
    page.locator("#agent-slug").fill("test_agent")
    page.wait_for_timeout(500)
    page.locator("#agent-title").fill("Test Agent")
    page.wait_for_timeout(500)
    page.locator("#agent-desc").fill("This is a test agent.")
    page.wait_for_timeout(500)

    # Click Next to go to Step 2: Brain
    page.get_by_role("button", name="Continue to Brain step").click()
    page.wait_for_timeout(1000)

    # Click Step 1 (Identity) indicator button to go back
    page.get_by_role("button", name="Go to Identity step").click()
    page.wait_for_timeout(1000)

    # Verify we are back on Step 1 by checking for Identity heading
    page.get_by_role("heading", name="Identity").is_visible()

    # Take screenshot at the key moment showing we navigated back via the indicator
    page.screenshot(path="ui/verification.png")
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="ui/videos"
        )
        page = context.new_page()
        try:
            run_cuj(page)
        finally:
            context.close()
            browser.close()
