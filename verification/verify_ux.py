from playwright.sync_api import sync_playwright

def verify_dashboard_ux(page):
    page.goto("http://localhost:3000")

    # Wait for the "NEW UNIT" button (header) or "INITIALIZE_FIRST_AGENT" (empty state)
    # Since I refactored both to be Links, I want to verify they are visible and look like buttons.

    # Check for "NEW UNIT" link-button
    new_unit_btn = page.get_by_role("link", name="NEW UNIT")
    if new_unit_btn.is_visible():
        print("Found NEW UNIT button")

    # Check for "INITIALIZE_FIRST_AGENT" link-button (likely visible if no agents)
    init_agent_btn = page.get_by_role("link", name="INITIALIZE_FIRST_AGENT")
    if init_agent_btn.is_visible():
        print("Found INITIALIZE_FIRST_AGENT button")

    # Take a screenshot
    page.screenshot(path="verification/dashboard_ux.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            verify_dashboard_ux(page)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()
