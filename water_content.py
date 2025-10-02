import pyautogui
import time
import keyboard
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from PIL import ImageGrab
from selenium.webdriver.chrome.options import Options






# --- Settings ---
LIGHT_BLUE = (98, 153, 254)
DARK_BLUE = (1, 61, 222)
PIXEL_STEP = 10
COLOR_TOLERANCE = 30
HOVER_TIME = 1.0
MAX_MATCHES = 30
CHROME_DRIVER_PATH = "C:/Users/user/.cache/selenium/chromedriver/win64/131.0.6778.204/chromedriver.exe"  # Update path to your chromedriver
URL = "https://bhuvan-vec1.nrsc.gov.in/bhuvan/sisdpv2/wms?service=WMS&version=1.1.0&request=GetMap&layers=sisdpv2%3ARJ_Baran_lulc_v2&bbox=76.21803732200004%2C24.40477039500007%2C77.42379752000008%2C25.43180322200004&width=768&height=654&srs=EPSG%3A4326&styles=&format=application/openlayers#toggle"  # Change to your map URL


def is_similar_color(rgb, target, tolerance=30):
    return all(abs(rgb[i] - target[i]) <= tolerance for i in range(3))


def scan_screen_for_blue():
    screenshot = ImageGrab.grab()
    pixels = screenshot.load()
    width, height = screenshot.size

    matches = []
    for x in range(0, width, PIXEL_STEP):
        for y in range(0, height, PIXEL_STEP):
            rgb = pixels[x, y]
            if is_similar_color(rgb, LIGHT_BLUE, COLOR_TOLERANCE) or is_similar_color(rgb, DARK_BLUE, COLOR_TOLERANCE):
                matches.append((x, y))

    return matches


def main():
    print("Opening browser...")
    chrome_options = Options()
    chrome_options.binary_location='C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe'
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome( options=chrome_options)
    driver.get(URL)
    time.sleep(5)  # Wait for page to load

    print("Press 'x' to start scanning blue pixels and scraping location values.")
    print("Press 'q' to quit.")

    while True:
        if keyboard.is_pressed("q"):
            print("Quitting...")
            driver.quit()
            break

        if keyboard.is_pressed("x"):
            print("Scanning screen for blue pixels...")
            matches = scan_screen_for_blue()
            print(f"Found {len(matches)} blue-ish pixels.")

            for idx, (x, y) in enumerate(matches[:MAX_MATCHES]):
                pyautogui.moveTo(x, y, duration=0.3)
                time.sleep(HOVER_TIME)

                try:
                    location_div = driver.find_element(By.ID, "location")
                    text = location_div.text.strip()
                    if text and text != " ":
                        print(f"[{idx}] Mouse at ({x},{y}) → Location: {text}")
                    else:
                        print(f"[{idx}] Mouse at ({x},{y}) → Location is empty.")
                except Exception as e:
                    print(f"[{idx}] Error reading location div: {e}")

            print("Scan complete. Press 'x' to scan again or 'q' to quit.")

        time.sleep(0.1)


if __name__ == "__main__":
    main()
