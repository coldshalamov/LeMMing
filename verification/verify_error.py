from playwright.sync_api import sync_playwright, expect

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Debug: log requests
        # page.on("request", lambda request: print(f"Request: {request.method} {request.url}"))
        # page.on("response", lambda response: print(f"Response: {response.status} {response.url}"))
        # page.on("console", lambda msg: print(f"Console: {msg.text}"))

        # Mock the config fetch (GET) and update (POST)
        def handle_config(route):
            # print(f"Intercepted: {route.request.method} {route.request.url}")
            if route.request.method == "GET":
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body='{"openai_api_key": "", "anthropic_api_key": ""}'
                )
            elif route.request.method == "POST":
                # print("Failing POST request...")
                route.fulfill(status=500, body="Internal Server Error")
            else:
                route.continue_()

        # Try matching everything containing /api/engine/config
        page.route("**/api/engine/config", handle_config)

        # Mock other API calls
        page.route("**/api/agents", lambda route: route.fulfill(status=200, body="[]"))
        page.route("**/api/org-graph", lambda route: route.fulfill(status=200, body='{"nodes": [], "edges": []}'))
        page.route("**/api/status", lambda route: route.fulfill(status=200, body='{}'))
        # Use regex for messages to handle query params
        page.route("**/api/messages*", lambda route: route.fulfill(status=200, body='[]'))

        try:
            # Go to home page
            page.goto("http://localhost:3000")

            # Wait for settings button
            settings_btn = page.get_by_label("Global Settings")
            expect(settings_btn).to_be_visible()
            settings_btn.click()

            # Fill in dummy data
            page.get_by_role("textbox", name="OpenAI API Key").fill("sk-test-123")

            # Click Save
            save_btn = page.get_by_role("button", name="SAVE CONFIG")
            expect(save_btn).to_be_enabled()
            save_btn.click()

            # Wait for error message - use exact text from api.ts
            error_msg = page.get_by_text("Failed to update config")
            expect(error_msg).to_be_visible(timeout=5000)

            # Check for RETRY button
            retry_btn = page.get_by_role("button", name="RETRY")
            expect(retry_btn).to_be_visible()

            print("Verification successful!")

        except Exception as e:
            print(f"Verification failed: {e}")
        finally:
            # Take screenshot regardless of success/failure
            page.screenshot(path="verification/verification.png")
            browser.close()

if __name__ == "__main__":
    run()
