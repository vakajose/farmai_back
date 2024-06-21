from fastapi import APIRouter, HTTPException
from models import Parcela
from schemas import ParcelaCreate, Parcela
from typing import List
from starlette import status

router = APIRouter()


@router.post("/create", response_model=Parcela, summary="Crear una nueva parcela",
             description="Crear una nueva parcela para un usuario especifico")
def create_parcela(parcela: ParcelaCreate):
    new_parcela = Parcela(**parcela.dict(), id=parcela.nombre.replace(" ", "_").lower())
    new_parcela.save()
    return new_parcela


@router.get("/{usuario_id}/{parcela_id}", response_model=Parcela, summary="Obtener una parcela por ID",
            description="Obtener los detalles de una parcela especifica por su ID")
def read_parcela(usuario_id: str, parcela_id: str):
    parcela = Parcela.get_by_id(usuario_id, parcela_id)
    if parcela:
        return parcela
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcela no encontrada")


@router.get("/{usuario_id}", response_model=List[Parcela],
            summary="Obtener todas las parcelas de un usuario por ID usuario",
            description="Obtener los detalles de todas las parcelas por ID usuario")
def read_all_parcelas(usuario_id: str):
    parcelas = Parcela.get_all(usuario_id)
    if parcelas:
        return parcelas
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcelas no encontradas")


@router.delete("/{usuario_id}/{parcela_id}", summary="Eliminar una parcela por ID",
               description="Eliminar una parcela especifica por su ID")
def delete_parcela(usuario_id: str, parcela_id: str):
    Parcela.delete(usuario_id, parcela_id)
    return {"message": "Parcela eliminada correctamente"}


@router.put("/{usuario_id}/{parcela_id}", response_model=Parcela, summary="Actualizar una parcela por ID",
            description="Actualizar los detalles de una parcela especifica por su ID")
def update_parcela(usuario_id: str, parcela_id: str, parcela: ParcelaCreate):
    existing_parcela = Parcela.get_by_id(usuario_id, parcela_id)
    if existing_parcela:
        updated_parcela = Parcela(**parcela.dict(), id=parcela_id)
        updated_parcela.save()
        return updated_parcela
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parcela no encontrada")
