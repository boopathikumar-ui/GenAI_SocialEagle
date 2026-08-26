import time
import os
import io
import subprocess
import pyautogui
import win32clipboard
import win32com.client
from PIL import Image

URL = "https://www.livechennai.com/gold_silverrate.asp#google_vignette"
SCREENSHOT_FILE = os.path.abspath("livechennai_screenshot.png")


# --------------------------------------------------
# 1. Open Chrome and the website
# --------------------------------------------------

subprocess.Popen(
    r"C:\Program Files\Google\Chrome\Application\chrome.exe"
)

time.sleep(3)

pyautogui.hotkey("ctrl", "l")
pyautogui.write(URL, interval=0.01)
pyautogui.press("enter")

# Wait for webpage to load
time.sleep(8)


# --------------------------------------------------
# 2. Take screenshot
# --------------------------------------------------

screenshot = pyautogui.screenshot()
screenshot.save(SCREENSHOT_FILE)

print("Screenshot saved:", SCREENSHOT_FILE)


# --------------------------------------------------
# 3. Copy screenshot to Windows clipboard
# --------------------------------------------------

image = Image.open(SCREENSHOT_FILE).convert("RGB")

output = io.BytesIO()
image.save(output, "BMP")

data = output.getvalue()[14:]
output.close()

win32clipboard.OpenClipboard()

try:
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(
        win32clipboard.CF_DIB,
        data
    )
finally:
    win32clipboard.CloseClipboard()

print("Screenshot copied to clipboard.")


# --------------------------------------------------
# 4. Open Microsoft Word using pywin32
# --------------------------------------------------

print("Opening Microsoft Word...")

word = win32com.client.Dispatch("Word.Application")

# Make Word visible
word.Visible = True

# Create a completely blank document
document = word.Documents.Add()

time.sleep(3)


# --------------------------------------------------
# 5. Paste screenshot into Word
# --------------------------------------------------

document.Content.Paste()

print("Screenshot pasted into blank Word document.")

# Keep Word open
