import time
import csv
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
CSV_FILENAME = "filtered_cards.csv"
PROCESSED_CARDS_FILE = "scraped_cards.txt"

ENGLISH_POKEMON_SETS = [
    "Pokemon 1999 Topps Movie",
    "Pokemon 1999 Topps Movie Evolution",
    "Pokemon 1999 Topps TV",
    "Pokemon 2000 Topps Chrome",
    "Pokemon 2000 Topps TV",
    "Pokemon 2020 Battle Academy",
    "Pokemon Ancient Origins",
    "Pokemon Aquapolis",
    "Pokemon Arceus",
    "Pokemon Astral Radiance",
    "Pokemon BREAKpoint",
    "Pokemon BREAKthrough",
    "Pokemon Base Set",
    "Pokemon Base Set 2",
    "Pokemon Battle Styles",
    "Pokemon Best of Game",
    "Pokemon Black & White",
    "Pokemon Boundaries Crossed",
    "Pokemon Brilliant Stars",
    "Pokemon Burger King",
    "Pokemon Burning Shadows",
    "Pokemon Call of Legends",
    "Pokemon Celebrations",
    "Pokemon Celestial Storm",
    "Pokemon Champion's Path",
    "Pokemon Chilling Reign",
    "Pokemon Cosmic Eclipse",
    "Pokemon Crimson Invasion",
    "Pokemon Crown Zenith",
    "Pokemon Crystal Guardians",
    "Pokemon Dark Explorers",
    "Pokemon Darkness Ablaze",
    "Pokemon Delta Species",
    "Pokemon Deoxys",
    "Pokemon Detective Pikachu",
    "Pokemon Diamond & Pearl",
    "Pokemon Double Crisis",
    "Pokemon Dragon",
    "Pokemon Dragon Frontiers",
    "Pokemon Dragon Majesty",
    "Pokemon Dragon Vault",
    "Pokemon Dragons Exalted",
    "Pokemon Emerald",
    "Pokemon Emerging Powers",
    "Pokemon Evolutions",
    "Pokemon Evolving Skies",
    "Pokemon Expedition",
    "Pokemon Fates Collide",
    "Pokemon Fire Red & Leaf Green",
    "Pokemon Flashfire",
    "Pokemon Forbidden Light",
    "Pokemon Fossil",
    "Pokemon Furious Fists",
    "Pokemon Fusion Strike",
    "Pokemon Generations",
    "Pokemon Go",
    "Pokemon Great Encounters",
    "Pokemon Guardians Rising",
    "Pokemon Gym Challenge",
    "Pokemon Gym Heroes",
    "Pokemon HeartGold & SoulSilver",
    "Pokemon Hidden Fates",
    "Pokemon Hidden Legends",
    "Pokemon Holon Phantoms",
    "Pokemon Journey Together",
    "Pokemon Jungle",
    "Pokemon Legend Maker",
    "Pokemon Legendary Collection",
    "Pokemon Legendary Treasures",
    "Pokemon Legends Awakened",
    "Pokemon Lost Origin",
    "Pokemon Lost Thunder",
    "Pokemon Majestic Dawn",
    "Pokemon McDonalds 2018",
    "Pokemon McDonalds 2019",
    "Pokemon McDonalds 2021",
    "Pokemon McDonalds 2022",
    "Pokemon McDonalds 2023",
    "Pokemon McDonalds 2024",
    "Pokemon Mysterious Treasures",
    "Pokemon Neo Destiny",
    "Pokemon Neo Discovery",
    "Pokemon Neo Genesis",
    "Pokemon Neo Revelation",
    "Pokemon Next Destinies",
    "Pokemon Noble Victories",
    "Pokemon Obsidian Flames",
    "Pokemon Paldea Evolved",
    "Pokemon Paldean Fates",
    "Pokemon Paradox Rift",
    "Pokemon Phantom Forces",
    "Pokemon Pikachu Libre & Suicune",
    "Pokemon Plasma Blast",
    "Pokemon Plasma Freeze",
    "Pokemon Plasma Storm",
    "Pokemon Platinum",
    "Pokemon POP Series 1",
    "Pokemon POP Series 2",
    "Pokemon POP Series 3",
    "Pokemon POP Series 4",
    "Pokemon POP Series 5",
    "Pokemon POP Series 9",
    "Pokemon Power Keepers",
    "Pokemon Primal Clash",
    "Pokemon Prismatic Evolutions",
    "Pokemon Promo",
    "Pokemon Rebel Clash",
    "Pokemon Rising Rivals",
    "Pokemon Roaring Skies",
    "Pokemon Ruby & Sapphire",
    "Pokemon Rumble",
    "Pokemon Sandstorm",
    "Pokemon Scarlet & Violet",
    "Pokemon Scarlet & Violet 151",
    "Pokemon Scarlet & Violet Energy",
    "Pokemon Secret Wonders",
    "Pokemon Shining Fates",
    "Pokemon Shining Legends",
    "Pokemon Shrouded Fable",
    "Pokemon Silver Tempest",
    "Pokemon Skyridge",
    "Pokemon Southern Islands",
    "Pokemon Steam Siege",
    "Pokemon Stellar Crown",
    "Pokemon Stormfront",
    "Pokemon Sun & Moon",
    "Pokemon Supreme Victors",
    "Pokemon Surging Sparks",
    "Pokemon Sword & Shield",
    "Pokemon TCG Classic: Blastoise Deck",
    "Pokemon TCG Classic: Charizard Deck",
    "Pokemon TCG Classic: Venusaur Deck",
    "Pokemon Team Magma & Team Aqua",
    "Pokemon Team Rocket",
    "Pokemon Team Rocket Returns",
    "Pokemon Team Up",
    "Pokemon Temporal Forces",
    "Pokemon Trick or Trade 2022",
    "Pokemon Trick or Trade 2023",
    "Pokemon Trick or Trade 2024",
    "Pokemon Triumphant",
    "Pokemon Twilight Masquerade",
    "Pokemon Ultra Prism",
    "Pokemon Unbroken Bonds",
    "Pokemon Undaunted",
    "Pokemon Unified Minds",
    "Pokemon Unleashed",
    "Pokemon Unseen Forces",
    "Pokemon Vivid Voltage",
    "Pokemon World Championships 2007",
    "Pokemon World Championships 2023",
    "Pokemon XY"
]

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
        if set_name.lower() == link.text.strip().lower():
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
    # Filter out cards containing Japanese or Chinese (case insensitive)
    if any(word in name.lower() for word in ["japanese", "chinese"]):
        print(f"Skipped non-English card: {name}")
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

    image_url = ""
    try:
        image_url = driver.find_element(By.CSS_SELECTOR, "img#product_image").get_attribute("src")
    except NoSuchElementException:
        image_url = ""

    return {
        "Name": name,
        "Price": raw_price,
        "Grade 7": grade_7,
        "Grade 8": grade_8,
        "Grade 9": grade_9,
        "Grade 9.5": grade_9_5,
        "PSA 10": psa_10,
        "Rarity": rarity,
        "Model Number": model_number,
        "Image URL": image_url,
        "URL": card_url,
    }

def load_processed_cards():
    if not os.path.exists(PROCESSED_CARDS_FILE):
        return set()
    with open(PROCESSED_CARDS_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_processed_card(card_url):
    with open(PROCESSED_CARDS_FILE, "a") as f:
        f.write(card_url + "\n")

def save_to_csv(data, filename=CSV_FILENAME):
    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "Name", "Price", "Grade 7", "Grade 8", "Grade 9", "Grade 9.5", "PSA 10",
            "Rarity", "Model Number", "Image URL", "URL"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

def main():
    driver = init_driver()
    processed_cards = load_processed_cards()

    try:
        for set_name in ENGLISH_POKEMON_SETS:
            # Skip any sets with Japanese or Chinese in their name
            if any(word in set_name.lower() for word in ["japanese", "chinese"]):
                print(f"Skipping set due to language filter: {set_name}")
                continue

            card_links = get_card_links_from_set(driver, set_name)
            print(f"Found {len(card_links)} cards in set: {set_name}")

            for link in card_links:
                if link in processed_cards:
                    print(f"Skipping already processed card: {link}")
                    continue
                card_data = fetch_card_data(driver, link)
                if card_data:
                    save_to_csv(card_data)
                    save_processed_card(link)
                    print(f"Saved card: {card_data['Name']}")
                else:
                    print(f"Skipped card: {link}")
                time.sleep(2)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
