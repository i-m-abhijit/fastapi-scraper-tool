from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import requests
from bs4 import BeautifulSoup
import json
import os
from hashlib import md5
import time
from abc import ABC, abstractmethod

# ---------------------- CONFIGURATION ----------------------
API_TOKEN = "secret_token"
DATA_FILE = "scraped_data.json"
CACHE_FILE = "cache.json"
IMAGE_FOLDER = "images"

# Ensure image folder exists
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# ---------------------- AUTHENTICATION ----------------------
app = FastAPI()

def authenticate(token: str):
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Unauthorized")

# ---------------------- MODELS ----------------------
class Product(BaseModel):
    product_title: str
    product_price: float
    path_to_image: str

class ScrapeSettings(BaseModel):
    max_pages: Optional[int] = None
    proxy: Optional[str] = None

# ---------------------- ABSTRACT CACHE HANDLER ----------------------
class CacheHandlerInterface(ABC):
    @abstractmethod
    def get_cache(self):
        pass

    @abstractmethod
    def update_cache(self, key: str, value: dict):
        pass

# ---------------------- CACHE HANDLER ----------------------
class CacheHandler(CacheHandlerInterface):
    def __init__(self, cache_file: str):
        self.cache_file = cache_file
        self._initialize_cache()

    def _initialize_cache(self):
        if not os.path.exists(self.cache_file):
            self._save_cache({})

    def _save_cache(self, cache_data):
        with open(self.cache_file, "w") as file:
            json.dump(cache_data, file)

    def get_cache(self):
        with open(self.cache_file, "r") as file:
            return json.load(file)

    def update_cache(self, key: str, value: dict):
        cache_data = self.get_cache()
        cache_data[key] = value
        self._save_cache(cache_data)

cache_handler = CacheHandler(CACHE_FILE)

# ---------------------- IMAGE HANDLER ----------------------
class ImageHandler:
    @staticmethod
    def download_image(url: str) -> str:
        img_name = md5(url.encode('utf-8')).hexdigest() + ".jpg"
        img_path = os.path.join(IMAGE_FOLDER, img_name)

        if not os.path.exists(img_path):
            img_data = requests.get(url).content
            with open(img_path, 'wb') as handler:
                handler.write(img_data)

        return img_path

# ---------------------- ABSTRACT SCRAPER ----------------------
class ScraperInterface(ABC):
    @abstractmethod
    def scrape(self):
        pass

    @abstractmethod
    def save_to_db(self):
        pass

# ---------------------- SCRAPER CLASS ----------------------
class Scraper(ScraperInterface):
    def __init__(self, settings: ScrapeSettings):
        self.base_url = "https://dentalstall.com/shop/"
        self.settings = settings
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.products = []
        self.proxy = None
        if settings.proxy:
            try:
                # Validate the proxy format
                requests.get("https://www.google.com", proxies={"http": settings.proxy, "https": settings.proxy})
                self.proxy = {"http": settings.proxy, "https": settings.proxy}
            except Exception as e:
                print(f"Invalid proxy: {settings.proxy}. Skipping proxy. Error: {str(e)}")


    def scrape(self):
        page = 1
        while True:
            if self.settings.max_pages and page > self.settings.max_pages:
                break

            url = f"{self.base_url}?page={page}"
            print(f"Scraping page: {page}")

            try:
                response = requests.get(url, headers=self.headers, proxies=self.proxy)
                if response.status_code != 200:
                    time.sleep(5)
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                products = soup.select('.product')  # Adjust CSS selector accordingly
                if not products:
                    break

                self._extract_products(products)
                page += 1
            except Exception as e:
                print(f"Error scraping page {page}: {str(e)}")
                time.sleep(5)
                continue

    def _extract_products(self, products):
        for product in products:
            title_element = product.select_one('.woo-loop-product__title a')
            title = title_element.get_text(strip=True) if title_element else "No Title"
            price_element = product.select_one('.price .woocommerce-Price-amount bdi')
            price = float(price_element.get_text(strip=True).replace('₹', '').replace(',', '')) if price_element else 0.0
            img_element = product.select_one('img')
            img_url = img_element['src'] if img_element else ""


            img_path = ImageHandler.download_image(img_url)
            product_id = md5(title.encode('utf-8')).hexdigest()

            cache = cache_handler.get_cache()
            if product_id in cache and cache[product_id]['product_price'] == price:
                continue

            cache_handler.update_cache(product_id, {"product_title": title, "product_price": price})
            self.products.append(Product(product_title=title, product_price=price, path_to_image=img_path))

    def save_to_db(self):
        with open(DATA_FILE, 'w') as file:
            json.dump([p.dict() for p in self.products], file)

# ---------------------- ENDPOINT ----------------------
@app.post("/scrape")
def start_scraping(settings: ScrapeSettings, token: str = Depends(authenticate)):
    scraper = Scraper(settings)
    scraper.scrape()
    scraper.save_to_db()

    message = f"Scraping complete. Total products scraped: {len(scraper.products)}"
    print(message)
    return {"status": "success", "message": message}

# ---------------------- RUN COMMAND ----------------------
# uvicorn main:app --reload
