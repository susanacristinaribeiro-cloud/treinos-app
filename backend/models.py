"""
Modelos Pydantic para a app de treinos.
"""
import uuid
from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


def _now(): return datetime.utcnow().isoformat()
def _uid():  return str(uuid.uuid4())


# ── Media (imagens e vídeos) ─────────────────────────────────────────────────

class VideoRef(BaseModel):
    id:     str                        = Field(default_factory=_uid)
    origem: Literal["upload", "url"]
    path:   Optional[str] = None   # usado quando origem == "upload"
    url:    Optional[str] = None   # usado quando origem == "url"


# ── Exercício (biblioteca) ────────────────────────────────────────────────────

class Exercicio(BaseModel):
    id:               str               = Field(default_factory=_uid)
    name:             str
    group:            Optional[str]     = None
    emoji:            Optional[str]     = "💪"
    description:      Optional[str]     = None
    photos:           List[str]         = []          # antes: photo (str único)
    videos:           List[VideoRef]    = []          # antes: video (str único)
    notes:            Optional[str]     = None
    alternative_ids:  List[str]         = []          # ids de outros Exercicio (biblioteca)
    created_at:       Optional[str]     = Field(default_factory=_now)
    updated_at:       Optional[str]     = Field(default_factory=_now)

class ExercicioCreate(BaseModel):
    name:            str
    group:           Optional[str]     = None
    emoji:           Optional[str]     = "💪"
    description:     Optional[str]     = None
    photos:          List[str]         = []
    videos:          List[VideoRef]    = []
    notes:           Optional[str]     = None
    alternative_ids: List[str]         = []

class ExercicioUpdate(BaseModel):
    name:            Optional[str]           = None
    group:           Optional[str]           = None
    emoji:           Optional[str]           = None
    description:     Optional[str]           = None
    photos:          Optional[List[str]]     = None
    videos:          Optional[List[VideoRef]] = None
    notes:           Optional[str]           = None
    alternative_ids: Optional[List[str]]     = None


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
