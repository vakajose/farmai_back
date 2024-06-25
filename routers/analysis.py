from fastapi import APIRouter, UploadFile, File
from typing import List
import os
from services.openai import *
from pydantic import BaseModel

router = APIRouter()
class DiagnosisRequest(BaseModel):
    diagnosis_type: str
    image_paths: List[str]

diagnosis_bands = {
    "NDVI": ["B08", "B04"],
    "EVI": ["B08", "B04", "B02"],
    "Estrés Hídrico": ["B08", "B11"],
    "Plagas": ["B08", "B04"],
    "Nutrientes en el Suelo": ["B08", "B04", "B11"],
    "LAI": ["B08", "B04"],
    "Malezas": ["B08", "B04"],
    "Biomasa": ["B08", "B11"],
    "Crecimiento de los Cultivos": ["B08", "B04", "B03"],
    "Enfermedades de las Plantas": ["B08", "B04", "B03"]
}

diagnosis_frequency = {
    "NDVI": "Semanal",
    "EVI": "Semanal",
    "Estrés Hídrico": "Semanal",
    "Plagas": "Diaria/Semanal",
    "Nutrientes en el Suelo": "Mensual",
    "LAI": "Quincenal",
    "Malezas": "Semanal",
    "Biomasa": "Mensual",
    "Crecimiento de los Cultivos": "Semanal",
    "Enfermedades de las Plantas": "Diaria/Semanal"
}

@router.post("/analyze")
async def analyze_diagnosis(request: DiagnosisRequest):
    diagnosis_type = request.diagnosis_type
    image_paths = request.image_paths
    
    if diagnosis_type not in diagnosis_bands:
        return {"error": "Invalid diagnosis type"}

    # Call the GPT-4 analysis function
    result = analyze_images(diagnosis_type, image_paths)

    return {
        "diagnosis_type": diagnosis_type,
        "bands_needed": diagnosis_bands[diagnosis_type],
        "frequency": diagnosis_frequency[diagnosis_type],
        "result": result
    }