from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from model_master import Lokasi,Provinces, Districts, Cities, Village, Cuaca, VsText, WeatherDesc, WeatherDescEn, cuaca_to_dict, parse_cuaca_matrix, parse_cuaca_matrix_for_listcuaca
from typing import List, Optional   
import requests
import html
import json

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://127.0.0.1",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

    
    

# Load provinces from provinces.json
def load_provinces() -> List[Provinces]:
    try:
        with open('provinces.json', 'r') as f:
            provinces_data = json.load(f)
        return [Provinces(**province) for province in provinces_data]
    except Exception as e:
        print(f"Error loading provinces: {e}")
        return []

# Load provinces from provinces.json
def load_provinces() -> List[Provinces]:
    try:
        with open('provinces.json', 'r') as f:
            provinces_data = json.load(f)
        return [Provinces(**province) for province in provinces_data]
    except Exception as e:
        print(f"Error loading provinces: {e}")
        return []

# Load cities from cities.json
def load_cities() -> List[Cities]:
    try:
        with open('cities.json', 'r') as f:
            cities_data = json.load(f)
        return [Cities(**city) for city in cities_data]
    except Exception as e:
        print(f"Error loading cities: {e}")
        return []
    
# Load districts from districts.json
def load_districts() -> List[Districts]:
    try:
        with open('districts.json', 'r') as f:
            districts_data = json.load(f)
        return [Districts(**district) for district in districts_data]
    except Exception as e:
        print(f"Error loading districts: {e}")
        return []
    
# Load villages from villages.json
def load_villages() -> List[Village]:
    try:
        with open('villages.json', 'r') as f:
            villages_data = json.load(f)
        return [Village(**village) for village in villages_data]
    except Exception as e:
        print(f"Error loading villages: {e}")
        return []

provinces = load_provinces()
cities = load_cities()
districts = load_districts()
villages = load_villages()

@app.get("/")
def prakiraan_cuaca():
    api_url = "https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4=64.71.01.1001"
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json() 
        # parse Lokasi using pydantic (support v2/v1)
        lokasi_raw = data.get("lokasi", {})
        try:
            loc = Lokasi.model_validate(lokasi_raw)
        except Exception:
            try:
                loc = Lokasi.parse_obj(lokasi_raw)
            except Exception:
                loc = Lokasi(**lokasi_raw)

        cuaca_raw = data.get("data", [{}])[0].get("cuaca", [[]])
        list_cuaca = parse_cuaca_matrix_for_listcuaca(cuaca_raw)

        def serialize_model(m):
            if hasattr(m, "model_dump"):
                return m.model_dump()
            if hasattr(m, "dict"):
                return m.dict()
            try:
                return vars(m)
            except Exception:
                return None

        cuaca_serialized = {
            "now": [cuaca_to_dict(c) for c in (list_cuaca.now or [])],
            "day1": [cuaca_to_dict(c) for c in (list_cuaca.day1 or [])],
            "day2": [cuaca_to_dict(c) for c in (list_cuaca.day2 or [])],
        }

        return JSONResponse(content={
            "lokasi": serialize_model(loc),
            "cuaca": cuaca_serialized
        })
    except Exception as e:
        return Response(
            content=f"ERROR: Gagal mengambil data. ({e})",
            media_type="text/plain"
        )
  

@app.get("/provinces", response_model=List[Provinces])
def list_provinces():
    return provinces

@app.get("/cities/byparentid/{parent_id}", response_model=List[Cities])
def list_cities_by_parent_id(parent_id: int):
    return [city for city in cities if city.province_id == parent_id]

@app.get("/districts/byparentid/{parent_id}", response_model=List[Districts])
def list_districts_by_parent_id(parent_id: int):
    return [district for district in districts if district.city_id == parent_id]

@app.get("/villages/byparentid/{parent_id}", response_model=List[Village])
def list_villages_by_parent_id(parent_id: int):
    return [village for village in villages if village.district_id == parent_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9999)
