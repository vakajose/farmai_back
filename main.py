from fastapi import FastAPI
from routers import auth

app = FastAPI(
    title="FarmAI Backend API",
    description="API para la gestión de FarmAI",
    version="1.0.0",
    contact={
        "name": "José Luis Vaca Fernández",
        "email": "vakajose@gmail.com",
    }
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])


@app.get("/", summary="Endpoint de Bienvenida", response_description="Mensaje de bienvenida")
async def root():
    """
    Endpoint principal de bienvenida de la API.
    """
    return {"message": "Welcome to Farmai Backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# This will automatically generate the OpenAPI documentation at /docs
