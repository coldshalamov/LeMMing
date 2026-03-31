import os
from playwright.sync_api import sync_playwright

def run_cuj(page):
    # Navigate to the Wizard page directly
    page.goto("http://localhost:3000/wizard")
    page.wait_for_timeout(2000)

    # Step 1: Identity
    page.locator("#agent-slug").fill("test_agent")
    page.wait_for_timeout(500)
    page.locator("#agent-title").fill("Test Title")
    page.wait_for_timeout(500)
    page.locator("#agent-desc").fill("Test Description for the agent")
    page.wait_for_timeout(500)

    # Click Next to go to Step 2 (Brain)
    page.locator("button:has-text('Next')").click()
    page.wait_for_timeout(1000)

    # Click Next to go to Step 3 (Schedule)
    page.locator("button:has-text('Next')").click()
    page.wait_for_timeout(1000)

    # Click Next to go to Step 4 (Permissions)
    page.locator("button:has-text('Next')").click()
    page.wait_for_timeout(1000)

    # Step 4: Open Tool Selector
    page.locator("button:has-text('Select Capabilities')").click()
    page.wait_for_timeout(1000)

    # Select two tools: File Access and Write Files
    page.locator("button", has_text="File Access").click()
    page.wait_for_timeout(500)
    page.locator("button", has_text="Write Files").click()
    page.wait_for_timeout(500)

    # Save Selection
    page.locator("button", has_text="Save Selection").click()
    page.wait_for_timeout(1000)

    # Take screenshot of the initial selected tools state
    os.makedirs("/home/jules/verification/screenshots", exist_ok=True)
    page.screenshot(path="/home/jules/verification/screenshots/verification_initial.png")
    page.wait_for_timeout(500)

    # Remove one tool using the new inline remove button
    # The button has aria-label="Remove {tool} capability"
    # The tool ID is 'file_read'
    page.get_by_label("Remove file_read capability").click()
    page.wait_for_timeout(1000)

    # Take screenshot after removal
    page.screenshot(path="/home/jules/verification/screenshots/verification_final.png")
    page.wait_for_timeout(1000)

if __name__ == "__main__":
    os.makedirs("/home/jules/verification/videos", exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            record_video_dir="/home/jules/verification/videos",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()
        try:
            run_cuj(page)
        except Exception as e:
            print(f"Test failed: {e}")
            page.screenshot(path="/home/jules/verification/screenshots/verification_error.png")
            raise
        finally:
            context.close()
            browser.close()
