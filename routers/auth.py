from fastapi import APIRouter, HTTPException
from schemas import UserCreate, UserLogin, UserResponse
from services.firebase import create_user, get_user_by_username

router = APIRouter()


@router.post("/register", response_model=UserResponse, summary="Registro de Usuario",
             response_description="El usuario registrado")
async def register(user: UserCreate):
    """
    Registra un nuevo usuario en la aplicación.

    - **username**: El nombre de usuario para registro.
    - **password**: La contraseña del usuario para registro.
    """
    existing_user = get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    create_user(user.dict())
    return UserResponse(username=user.username)


@router.post("/login", response_model=UserResponse, summary="Inicio de Sesión",
             response_description="El usuario autenticado")
async def login(user: UserLogin):
    """
    Autentica un usuario existente en la aplicación.

    - **username**: El nombre de usuario para inicio de sesión.
    - **password**: La contraseña del usuario para inicio de sesión.
    """
    db_user = get_user_by_username(user.username)
    if not db_user or db_user['password'] != user.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return UserResponse(username=user.username)
