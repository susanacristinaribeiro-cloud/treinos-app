"""
Modelos Pydantic para a app de treinos.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


def _now(): return datetime.utcnow().isoformat()
def _uid():  return str(uuid.uuid4())


# ── Exercício (biblioteca) ────────────────────────────────────────────────────

class Exercicio(BaseModel):
    id:          str           = Field(default_factory=_uid)
    name:        str
    group:       Optional[str] = None
    emoji:       Optional[str] = "💪"
    description: Optional[str] = None
    video:       Optional[str] = None
    notes:       Optional[str] = None
    photo:       Optional[str] = None
    created_at:  Optional[str] = Field(default_factory=_now)
    updated_at:  Optional[str] = Field(default_factory=_now)

class ExercicioCreate(BaseModel):
    name:        str
    group:       Optional[str] = None
    emoji:       Optional[str] = "💪"
    description: Optional[str] = None
    video:       Optional[str] = None
    notes:       Optional[str] = None
    photo:       Optional[str] = None

class ExercicioUpdate(BaseModel):
    name:        Optional[str] = None
    group:       Optional[str] = None
    emoji:       Optional[str] = None
    description: Optional[str] = None
    video:       Optional[str] = None
    notes:       Optional[str] = None
    photo:       Optional[str] = None


# ── Exercício dentro de um Treino ────────────────────────────────────────────

class TreinoExercise(BaseModel):
    id:          str           = Field(default_factory=_uid)
    exercise_id: Optional[str] = None   # referência à biblioteca
    name:        str
    sets:        Optional[str] = None
    reps:        Optional[str] = None
    rest:        Optional[str] = None
    notes:       Optional[str] = None


# ── Treino ────────────────────────────────────────────────────────────────────

class Treino(BaseModel):
    id:         str                    = Field(default_factory=_uid)
    name:       str
    emoji:      Optional[str]          = "💪"
    notes:      Optional[str]          = None
    exercises:  List[TreinoExercise]   = []
    created_at: Optional[str]          = Field(default_factory=_now)
    updated_at: Optional[str]          = Field(default_factory=_now)

class TreinoCreate(BaseModel):
    name:      str
    emoji:     Optional[str]        = "💪"
    notes:     Optional[str]        = None
    exercises: List[TreinoExercise] = []

class TreinoUpdate(BaseModel):
    name:      Optional[str]                   = None
    emoji:     Optional[str]                   = None
    notes:     Optional[str]                   = None
    exercises: Optional[List[TreinoExercise]]  = None


# ── Nota ─────────────────────────────────────────────────────────────────────

class Nota(BaseModel):
    id:           str           = Field(default_factory=_uid)
    title:        Optional[str] = None
    content:      Optional[str] = None
    links:        List[str]     = []
    exercise_ids: List[str]     = []
    created_at:   Optional[str] = Field(default_factory=_now)
    updated_at:   Optional[str] = Field(default_factory=_now)

class NotaCreate(BaseModel):
    title:        Optional[str] = None
    content:      Optional[str] = None
    links:        List[str]     = []
    exercise_ids: List[str]     = []

class NotaUpdate(BaseModel):
    title:        Optional[str]       = None
    content:      Optional[str]       = None
    links:        Optional[List[str]] = None
    exercise_ids: Optional[List[str]] = None


# ── AppData ───────────────────────────────────────────────────────────────────

class AppData(BaseModel):
    exercicios: List[Exercicio] = []
    treinos:    List[Treino]    = []
    notas:      List[Nota]      = []
