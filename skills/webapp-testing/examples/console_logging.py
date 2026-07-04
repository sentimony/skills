from playwright.sync_api import sync_playwright

# Example: Capturing console logs and page errors during browser automation

url = 'http://localhost:5173'  # Replace with your URL

console_logs = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})

    # Set up console log capture
    def handle_console_message(msg):
        console_logs.append(f"[{msg.type}] {msg.text}")
        print(f"Console: [{msg.type}] {msg.text}")

    # Uncaught JS exceptions are not console events, capture them separately
    def handle_page_error(error):
        console_logs.append(f"[pageerror] {error}")
        print(f"Page error: {error}")

    page.on("console", handle_console_message)
    page.on("pageerror", handle_page_error)

    # Navigate to page and wait for it to render
    page.goto(url, wait_until='domcontentloaded')
    page.wait_for_function("document.body.innerText.trim().length > 0")

    # Interact with the page (triggers console logs)
    page.click('text=Submit')  # Replace with a selector from your app
    page.wait_for_selector('#result')  # Replace with the state your action produces

    browser.close()

# Save console logs to file
with open('/tmp/console.log', 'w') as f:
    f.write('\n'.join(console_logs))

print(f"\nCaptured {len(console_logs)} console messages")
print(f"Logs saved to: /tmp/console.log")
