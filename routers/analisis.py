from fastapi import APIRouter, HTTPException, status
from models import Analisis, Parcela
from schemas import AnalisisCreate, AnalisisResponse,ImagenSatelital
from typing import List
from services import sentinelhub, openai

router = APIRouter()


@router.post("/{usuario_id}/{parcela_id}/create", response_model=AnalisisResponse, summary="Crear un nuevo analisis",
             description="Crear un nuevo analisis para una parcela especifica")
def create_analisis(usuario_id: str, parcela_id: str, analisis: AnalisisCreate):
    try:
        new_analisis = Analisis(**analisis.dict())
        new_analisis.save(usuario_id, parcela_id)
        return new_analisis
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{usuario_id}/{parcela_id}/{analisis_id}", response_model=AnalisisResponse,
            summary="Obtener un analisis por ID",
            description="Obtener los detalles de un analisis especifico por su ID")
def read_analisis(usuario_id: str, parcela_id: str, analisis_id: str):
    try:
        analisis = Analisis.get_by_id(usuario_id, parcela_id, analisis_id)
        if analisis:
            return analisis
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analisis no encontrado")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{usuario_id}/{parcela_id}/", response_model=List[AnalisisResponse],
            summary="Obtener todos los analisis de una parcela por ID",
            description="Obtener los detalles de todos los analisis por ID de la parcela")
def read_all_analisis(usuario_id: str, parcela_id: str):
    try:
        analisis_list = Analisis.get_all(usuario_id, parcela_id)
        if analisis_list:
            return analisis_list
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analisis no encontrados")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{usuario_id}/{parcela_id}/{analisis_id}", response_model=AnalisisResponse, summary="Actualizar un analisis por ID",
            description="Actualizar los detalles de un analisis especifico por su ID")
def update_analisis(usuario_id: str, parcela_id: str, analisis_id: str, analisis: AnalisisCreate):
    try:
        existing_analisis = Analisis.get_by_id(usuario_id, parcela_id, analisis_id)
        if existing_analisis:
            update_analisis = Analisis(**analisis.dict(),id=analisis_id)
            update_analisis.save(usuario_id, parcela_id)
            return update_analisis
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analisis no encontrado")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{usuario_id}/{parcela_id}/{analisis_id}", summary="Eliminar un analisis por ID",
               description="Eliminar un analisis especifico por su ID")
def delete_analisis(usuario_id: str, parcela_id: str, analisis_id: str):
    try:
        Analisis.delete(usuario_id, parcela_id, analisis_id)
        return {"message": "Analisis eliminado correctamente"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/last_by_tipo/{usuario_id}/{parcela_id}/{tipo}", response_model=List[AnalisisResponse],
            summary="Obtener solo el ultimo analisis de un respectivo tipo",
            description="Obtener solo el ultimo analisis de un respectivo tipo de analisis basado en la fecha de creacion")
def get_last_analisis_by_tipo(usuario_id: str, parcela_id: str, tipo: str):
    analisis = Analisis.get_last_analisis_by_tipo(usuario_id, parcela_id, tipo)
    if analisis:
        return analisis
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analisis no encontrado")


@router.get("/ejecutar/{usuario_id}/{parcela_id}/{tipo}", response_model=List[ImagenSatelital],
            summary="Ejecutar un analisis",
            description="Ejecuta el analisis para una parcela especifica y devuelve el resultado del diagnostico")
def ejecutar_analisis(usuario_id: str, parcela_id: str, tipo: str):
    #Traer las imagenes en funcion del tipo de analisis desde sentinelHub
    try:
        sentinel_hub_service = sentinelhub.SentinelHubService()
        parcela = Parcela.get_by_id(usuario_id, parcela_id)
        imagenes = sentinel_hub_service.fetch_images(parcela, tipo)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    #return imagenes
    #Si existe las imagenes, realizar el analisis con OpenAI
    if imagenes:
        nuevo_analisis = Analisis(tipo=tipo, imagenes=imagenes)
        nuevo_analisis.save(usuario_id, parcela_id)
        return imagenes
    #     respuesta = openai.analyze_images(tipo, imagenes)
    #     #si existe respuesta, guardar el analisis
    #     if respuesta:
    #         analisis = Analisis(tipo=tipo, imagenes=imagenes, evaluacion=respuesta)
    #         analisis.save(usuario_id, parcela_id)
    #         return respuesta

