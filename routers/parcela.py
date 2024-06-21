from fastapi import APIRouter, HTTPException
from models import Parcela
from schemas import ParcelaCreate, ParcelaResponse
from typing import List
from starlette import status

router = APIRouter()


@router.post("/create", response_model=ParcelaResponse, summary="Crear una nueva parcela",
             description="Crear una nueva parcela para un usuario especifico")
def create_parcela(parcela: ParcelaCreate):
    try:
        new_parcela = Parcela(**parcela.dict(), id=parcela.nombre.replace(" ", "_").lower())
        new_parcela.save()
        return new_parcela
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{usuario_id}/{parcela_id}", response_model=ParcelaResponse, summary="Obtener una parcela por ID",
            description="Obtener los detalles de una parcela especifica por su ID")
def read_parcela(usuario_id: str, parcela_id: str):
    try:
        parcela = Parcela.get_by_id(usuario_id, parcela_id)
        if parcela:
            return parcela
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcela no encontrada")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{usuario_id}", response_model=List[ParcelaResponse],
            summary="Obtener todas las parcelas de un usuario por ID usuario",
            description="Obtener los detalles de todas las parcelas por ID usuario")
def read_all_parcelas(usuario_id: str):
    try:
        parcelas = Parcela.get_all(usuario_id)
        if parcelas:
            return parcelas
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelas no encontradas")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{usuario_id}/{parcela_id}", summary="Eliminar una parcela por ID",
               description="Eliminar una parcela especifica por su ID")
def delete_parcela(usuario_id: str, parcela_id: str):
    try:
        Parcela.delete(usuario_id, parcela_id)
        return {"message": "Parcela eliminada correctamente"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{usuario_id}/{parcela_id}", response_model=ParcelaResponse, summary="Actualizar una parcela por ID",
            description="Actualizar los detalles de una parcela especifica por su ID")
def update_parcela(usuario_id: str, parcela_id: str, parcela: ParcelaCreate):
    try:
        existing_parcela = Parcela.get_by_id(usuario_id, parcela_id)
        if existing_parcela:
            updated_parcela = Parcela(**parcela.dict(), id=parcela_id)
            updated_parcela.save()
            return updated_parcela
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcela no encontrada")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
