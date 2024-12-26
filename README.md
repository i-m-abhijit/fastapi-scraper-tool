# FastAPI Scraper Tool

This project is a **web scraper tool** built with **FastAPI**. It scrapes product information (title, price, and image) from the specified website and stores the data locally in JSON format.

---

## **Features**
- Scrapes product title, price, and image.
- Optional settings:
  - Limit the number of pages to scrape.
  - Use a proxy (if required).
- Stores scraped data locally in `scraped_data.json`.
- Caches results to avoid redundant updates.
- Downloads and saves product images locally.
- Notifies about scraping status.
- Built-in authentication using a static token.

---

## **Project Structure**
```
fastapi_scraper_tool/
├── main.py                 # Main application code
├── requirements.txt        # Dependencies
├── scraped_data.json       # Output data (JSON format)
├── cache.json              # Cached data for optimization
├── images/                 # Folder for downloaded images
```

---

## **Installation**
1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd fastapi_scraper_tool
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## **Usage**
### **Run the FastAPI Server**
```bash
uvicorn main:app --reload
```
- Server runs at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

### **API Endpoint**
**POST /scrape** - Start scraping process.

#### **Request Example**
```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/scrape?token=secret_token' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "max_pages": 2,
  "proxy": null
}'
```

#### **Parameters**
| Parameter   | Type    | Description                                                  |
|-------------|---------|--------------------------------------------------------------|
| `max_pages` | integer | Number of pages to scrape (optional).                        |
| `proxy`     | string  | Proxy URL for scraping (optional). Example: `http://proxy.com:8080` |

---

### **Output Example (scraped_data.json)**
```json
[
  {
    "product_title": "Product Name",
    "product_price": 1380.0,
    "path_to_image": "images/product_image.jpg"
  }
]
```

---

## **Authentication**
- Token is passed as a **query parameter**:
  ```
  ?token=secret_token
  ```

---

## **Error Handling**
- Logs errors to console for debugging.
- Handles missing elements (title, price, image) gracefully.
- Supports retries and fallback mechanisms for proxy failures.

---

## **Extending Features**
- Replace JSON storage with a database (e.g., SQLite or MongoDB).
- Implement more notification strategies (email, Slack, etc.).
- Add filtering and sorting for scraped data.

---
