from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.database import engine, Base, get_db
from app.models import database_models, schemas
from app.api import endpoints

# Crear tablas en SQLite (para MVP)
database_models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Esperanto PDF Repair API",
    description="API para análisis, auditoría y corrección de documentos PDF.",
    version="1.0.0",
)

# Configurar CORS para permitir requests del frontend (Next.js en el puerto 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router, prefix="/api")

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Esperanto PDF Repair API is running"}


@app.post("/api/projects", response_model=schemas.ProjectSchema)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    db_project = database_models.Project(name=project.name)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@app.get("/api/projects", response_model=list[schemas.ProjectSchema])
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    projects = db.query(database_models.Project).offset(skip).limit(limit).all()
    return projects
