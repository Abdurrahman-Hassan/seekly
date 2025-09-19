from pydantic import BaseModel
from typing import List, Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from services.dynamic import scrape_dynamic

app = FastAPI(title="Seekly API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchResult(BaseModel):
    retailer: str
    title: str
    price: str  # Changed to string to handle currency symbols
    currency: str
    url: str
    image: Optional[str] = None

class ScrapeResponse(BaseModel):
    success: bool
    data: List[SearchResult]
    count: int
    source: str

@app.get("/")
def home():
    return {"message": "Seekly API is running 🚀", "version": "0.1.0"}

@app.get("/scrape", response_model=ScrapeResponse)
def scrape_item(url: str = Query(..., description="URL to scrape")):
    try:
        result = scrape_dynamic(url)
        return {
            "success": True,
            "data": result,
            "count": len(result),
            "source": "OLX" if "olx" in url.lower() else "Unknown"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@app.get("/search", response_model=ScrapeResponse)
def search_items(url: str = Query(..., description="URL to scrape")):
    try:
        result = scrape_dynamic(url)
        return {
            "success": True,
            "data": result,
            "count": len(result),
            "source": "OLX" if "olx" in url.lower() else "Unknown"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "seekly-scraper"}