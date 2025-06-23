import time
import csv
import os
import zipfile
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
BASE_URL = "https://www.pricecharting.com"
CSV_FILENAME = "filtered_cards.csv"
PROCESSED_CARDS_FILE = "scraped_cards.txt"

# ENGLISH_POKEMON_SETS already defined above

def init_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(1920, 1080)
    return driver

def get_card_links_from_set(driver, set_name):
    print(f"Searching for set: {set_name}")
    driver.get("https://www.pricecharting.com/category/pokemon-cards")
    time.sleep(3)
    links = driver.find_elements(By.CSS_SELECTOR, "div.sets a")
    for link in links:
        if set_name.lower() in link.text.strip().lower():
            return get_card_links(driver, link.get_attribute("href"))
    print(f"Set not found: {set_name}")
    return []

def get_card_links(driver, set_url):
    driver.get(set_url)
    time.sleep(2)
    card_links = set()
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        cards = driver.find_elements(By.CSS_SELECTOR, "a[href^='/game/']")
        card_links.update(card.get_attribute('href') for card in cards)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    return list(card_links)

def clean_price(price_elem):
    if price_elem:
        text = price_elem.text.strip()
        return text if text != "-" else "N/A"
    return "N/A"

def fetch_card_data(driver, card_url):
    driver.get(card_url)
    wait = WebDriverWait(driver, 10)
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1#product_name")))
    except TimeoutException:
        print(f"Timeout loading card page: {card_url}")
        return None

    name = driver.find_element(By.CSS_SELECTOR, "h1#product_name").text.strip()
    if any(word in name.lower() for word in ["japanese", "jpn", "japan"]):
        print(f"Skipped Japanese card: {name}")
        return None

    prices = driver.find_elements(By.CSS_SELECTOR, "span.price.js-price")
    raw_price = clean_price(prices[0]) if prices else "N/A"

    try:
        numeric_price = float(raw_price.replace("$", "").replace(",", ""))
        if numeric_price < 10:
            print(f"Skipped low-value card: {name} (${numeric_price})")
            return None
    except ValueError:
        pass

    grade_7 = clean_price(prices[1]) if len(prices) > 1 else "N/A"
    grade_8 = clean_price(prices[2]) if len(prices) > 2 else "N/A"
    grade_9 = clean_price(prices[3]) if len(prices) > 3 else "N/A"
    grade_9_5 = clean_price(prices[4]) if len(prices) > 4 else "N/A"
    psa_10 = clean_price(prices[5]) if len(prices) > 5 else "N/A"

    try:
        rarity = driver.find_element(By.CSS_SELECTOR, "td.details[itemprop='description']").text.strip()
    except NoSuchElementException:
        rarity = "none"
    try:
        model_number = driver.find_element(By.CSS_SELECTOR, "td.details[itemprop='model-number']").text.strip()
    except NoSuchElementException:
        model_number = "N/A"

    image_url = next((img.get_attribute("src") for img in driver.find_elements(By.CSS_SELECTOR, "img") if img.get_attribute("src") and "1600.jpg" in img.get_attribute("src")), "N/A")

    return {
        "Name": name,
        "Raw Price": raw_price,
        "Grade 7 Price": grade_7,
        "Grade 8 Price": grade_8,
        "Grade 9 Price": grade_9,
        "Grade 9.5 Price": grade_9_5,
        "PSA 10 Price": psa_10,
        "Rarity": rarity,
        "Model Number": model_number,
        "Image URL": image_url,
        "Card URL": card_url
    }

def save_to_csv(data, filename=CSV_FILENAME, write_header=False, mode='a'):
    if not data:
        return
    with open(filename, mode, newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        if write_header:
            writer.writeheader()
        writer.writerows(data)
    print(f"Saved {len(data)} cards to {filename}")

def main():
    driver = init_driver()
    try:
        processed_cards = set()
        if os.path.exists(PROCESSED_CARDS_FILE):
            with open(PROCESSED_CARDS_FILE, "r", encoding="utf-8") as f:
                processed_cards = set(line.strip() for line in f)

        all_cards_data = []
        first_save = True
        processed_count = 0

        for set_name in ENGLISH_POKEMON_SETS:
            card_links = get_card_links_from_set(driver, set_name)
            for card_url in card_links:
                if card_url in processed_cards:
                    continue
                card_data = fetch_card_data(driver, card_url)
                if card_data:
                    all_cards_data.append(card_data)
                    with open(PROCESSED_CARDS_FILE, "a", encoding="utf-8") as f:
                        f.write(card_url + "\n")
                    processed_cards.add(card_url)
                    processed_count += 1
                if processed_count % 1000 == 0:
                    save_to_csv(all_cards_data, write_header=first_save)
                    all_cards_data = []
                    first_save = False
                time.sleep(1)

        if all_cards_data:
            save_to_csv(all_cards_data, write_header=first_save)
    finally:
        driver.quit()
        print("Driver closed.")

if __name__ == "__main__":
    main()
