# import json
# from fastapi import APIRouter, HTTPException
# from typing import List
# from pathlib import Path
# from app.models import ScrapedData

# router = APIRouter()

# output_file = Path("data/output.json")

# @router.get("/scraped-data", response_model=List[ScrapedData])
# def get_scraped_data():
#     if not output_file.is_file():
#         raise HTTPException(status_code=404, detail="Scraped data file not found")

#     try:
#         with open(output_file, 'r', encoding='utf-8') as f:
#             scraped_data = json.load(f)
#         return scraped_data
#     except json.JSONDecodeError:
#         raise HTTPException(status_code=500, detail="Error decoding JSON data")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))