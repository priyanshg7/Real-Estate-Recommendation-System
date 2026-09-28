import os
from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from analytics_engine import AnalyticsEngine
from recommender_engine import RecommenderEngine

app = FastAPI(
    title="Gurgaon Real Estate Analytics & Recommendation Engine",
    description="Interactive data analytics, exploratory visualizations, price prediction, and property recommendations.",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize engines
analytics = AnalyticsEngine(data_dir=BASE_DIR)
recommender = RecommenderEngine(analytics)

# Static and Templates directories
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")
os.makedirs(os.path.join(static_dir, "css"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "js"), exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Pydantic models for request bodies
class FilterRequest(BaseModel):
    property_type: Optional[str] = "all"
    sector: Optional[str] = "all"
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_area: Optional[float] = None
    max_area: Optional[float] = None
    bedrooms: Optional[List[int]] = None
    furnishing: Optional[str] = "all"
    min_luxury: Optional[float] = None
    study_room: Optional[bool] = False
    servant_room: Optional[bool] = False
    store_room: Optional[bool] = False
    pooja_room: Optional[bool] = False
    search_query: Optional[str] = None
    page: int = 1
    page_size: int = 20
    sort_by: str = "price"
    sort_order: str = "asc"

class PredictPriceRequest(BaseModel):
    property_type: str = "flat"
    sector: str = "Sector 102"
    built_up_area: float = 1800.0
    bedRoom: int = 3
    bathroom: int = 3
    floorNum: float = 5.0
    luxury_score: float = 45.0
    furnishing_desc: str = "Semi-Furnished"
    study_room: int = 0
    servant_room: int = 0
    store_room: int = 0
    pooja_room: int = 0

class RecommendRequest(BaseModel):
    budget_min: float = 1.0
    budget_max: float = 3.5
    target_sector: Optional[str] = "all"
    property_type: Optional[str] = "all"
    preferred_bhk: Optional[int] = 3
    min_luxury: float = 0.0
    need_servant_room: bool = False
    need_study_room: bool = False
    top_k: int = 8

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(BASE_DIR, "templates", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Dashboard template not found. Please verify templates/index.html exists.</h1>"

@app.get("/api/overview")
async def get_overview():
    return analytics.get_overview_kpis()

@app.get("/api/eda/univariate")
async def get_univariate(feature: str = Query("price", description="Feature name to analyze")):
    result = analytics.get_univariate_analysis(feature)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.get("/api/eda/multivariate")
async def get_multivariate():
    return analytics.get_multivariate_analysis()

@app.get("/api/sectors")
async def get_sectors():
    return analytics.get_sectors_intelligence()

@app.get("/api/sectors/{sector_name}")
async def get_sector_detail(sector_name: str):
    result = analytics.get_sector_deep_dive(sector_name)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.post("/api/properties/filter")
async def filter_properties(req: FilterRequest):
    return analytics.filter_properties(
        property_type=req.property_type,
        sector=req.sector,
        min_price=req.min_price,
        max_price=req.max_price,
        min_area=req.min_area,
        max_area=req.max_area,
        bedrooms=req.bedrooms,
        furnishing=req.furnishing,
        min_luxury=req.min_luxury,
        study_room=req.study_room,
        servant_room=req.servant_room,
        store_room=req.store_room,
        pooja_room=req.pooja_room,
        search_query=req.search_query,
        page=req.page,
        page_size=req.page_size,
        sort_by=req.sort_by,
        sort_order=req.sort_order
    )

@app.get("/api/properties/{prop_id}")
async def get_property_detail(prop_id: int):
    prop = analytics.get_property_by_id(prop_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop

@app.post("/api/predict-price")
async def predict_price(req: PredictPriceRequest):
    try:
        return recommender.predict_price(
            property_type=req.property_type,
            sector=req.sector,
            built_up_area=req.built_up_area,
            bedRoom=req.bedRoom,
            bathroom=req.bathroom,
            floorNum=req.floorNum,
            luxury_score=req.luxury_score,
            furnishing_desc=req.furnishing_desc,
            study_room=req.study_room,
            servant_room=req.servant_room,
            store_room=req.store_room,
            pooja_room=req.pooja_room
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommend")
async def get_recommendations(req: RecommendRequest):
    try:
        results = recommender.recommend_properties(
            budget_min=req.budget_min,
            budget_max=req.budget_max,
            target_sector=req.target_sector,
            property_type=req.property_type,
            preferred_bhk=req.preferred_bhk,
            min_luxury=req.min_luxury,
            need_servant_room=req.need_servant_room,
            need_study_room=req.need_study_room,
            top_k=req.top_k
        )
        return {"recommendations": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
