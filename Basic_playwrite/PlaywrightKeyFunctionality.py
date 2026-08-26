from playwright.sync_api import sync_playwright


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://www.google.com/")
    page.screenshot(path="screenshot.png")
    browser.close()

    page.goto("https://www.accuweather.com/en/in/indore/202190/weather-forecast/202190")
    page.screenshot(path="Weather_forecast.png")

    page.click("text=HOURLY")
page.screenshot(path="Weather_forecast.png")

#typing 
page.fill("input[name='q']", "Playwright")
page.press("Enter")
page.screenshot(path="search_results.png")

#waiting for elements
page.wait_for_selector("text=Playwright: Fast and reliable end-to-end testing for modern web apps | Playwright")    
page.screenshot(path="search_results2.png")

#extracting the data
title = page.title()
print(f"Page title: {title}")
browser.close()