import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

SBR_WS_CDP = "wss://brd-customer-hl_88159e9c-zone-scraping_browser1:vkc832p1vt2c@brd.superproxy.io:9222"


class RSS:
    def __init__(self) -> None:
        self.url = "https://dashboard.rss.com/auth/sign-in/"

    def login(self, email, password):
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(SBR_WS_CDP)
            context = browser.new_context()

            # Open a new page
            page = context.new_page()
            
            # Go to the login page
            page.goto(self.url)

            # Fill in email and password inputs and click login
            page.fill('input[name="email"]', email)  # Replace with your email
            page.fill('input[name="password"]', password)  # Replace with your password
            page.click('button[data-testid="buttonSignin"]')

            # Wait for navigation to complete
            page.is_visible("div.podcast-content", timeout=30000)

            html = page.inner_html("div.podcast-content")
            print(html)

            # Get the HTTP status code after login
            status_code = page.evaluate("() => window.location.href").split('/')[-1]
            print(f"Request Status Code after successful login: {status_code}")
            
            # Get the URL after successful login
            redirected_url = page.url
            print(f"Redirected URL after successful login: {redirected_url}")

            # Navigate to the redirected page (or perform further actions based on the redirection)
            redirected_page = context.new_page()
            redirected_page.goto(redirected_url)

            # Click the button with data-testid="buttonNewEpisode"
            redirected_page.click('[data-testid="buttonNewEpisode"]')

            # Wait for navigation after clicking the button
            redirected_page.wait_for_load_state('networkidle')

            # Get the URL after clicking the button
            final_redirected_url = redirected_page.url
            print(f"URL after clicking the button: {final_redirected_url}")

            print(final_redirected_url.content())

            # Close the browser
            browser.close()




if __name__ == "__main__":
    load_dotenv()
    rss = RSS()
    rss.login(os.environ.get("RSS_EMAIL"), os.environ.get("RSS_PASSWORD"))