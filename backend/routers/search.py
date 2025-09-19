from fastapi import APIRouter, Query
from services.scraper import scrape_pakwheels, scrape_olx

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/")
def search_all(q: str = Query(..., description="Search term")):
    results = []
    results.extend(scrape_pakwheels(q))
    results.extend(scrape_olx(q))
    return results
