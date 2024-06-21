from fastapi import APIRouter, HTTPException
from schemas import UserCreate, UserLogin, UserResponse
from starlette import status
from models import *
import logging

router = APIRouter()


@router.post("/register", response_model=UserResponse, summary="Registro de Usuario",
             response_description="El usuario registrado")
async def register(user: UserCreate):
    """
    Registra un nuevo usuario en la aplicación.

    - **username**: El nombre de usuario para registro.
    - **password**: La contraseña del usuario para registro.
    """
    existing_user = User.get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already registered")
    new_user = User(username=user.username, password=user.password)
    new_user.create_user()
    return UserResponse(username=user.username)


@router.post("/login", response_model=UserResponse, summary="Inicio de Sesión",
             response_description="El usuario autenticado")
async def login(user: UserLogin):
    """
    Autentica un usuario existente en la aplicación.

    - **username**: El nombre de usuario para inicio de sesión.
    - **password**: La contraseña del usuario para inicio de sesión.
    """
    db_user = User.get_user_by_username(user.username)
    if not db_user or db_user['password'] != user.password:
        logging.log(logging.INFO, f"Invalid credentials for user {user.username}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return UserResponse(username=user.username)
