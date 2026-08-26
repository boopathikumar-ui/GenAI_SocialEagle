from playwright.sync_api import sync_playwright

with sync_playwright() as p:

    # Open Chrome/Chromium
    browser = p.chromium.launch(headless=False)

    # Create a page
    page = browser.new_page()

    # Open weather website
    page.goto(
        "https://www.theweathernetwork.com/en/city/india/tamil-nadu/chennai/current",
        wait_until="domcontentloaded"
    )

    # Wait for weather information to appear
    page.wait_for_timeout(5000)

    # Get page text
    weather_text = page.locator("body").inner_text()

    # Print weather information
    print("========== CHENNAI WEATHER ==========")
    print(weather_text[:3000])
    print("======================================")

    # Keep browser open for 5 seconds
    page.wait_for_timeout(5000)

    browser.close()
