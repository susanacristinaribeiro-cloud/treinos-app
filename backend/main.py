import os
import re
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends, Security, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security.api_key import APIKeyHeader

from models import (
    Exercicio, ExercicioCreate, ExercicioUpdate,
    Treino, TreinoCreate, TreinoUpdate,
    Nota, NotaCreate, NotaUpdate,
    AppData,
)
from storage import storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Treinos API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.environ.get("API_KEY", "")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(key: Optional[str] = Security(api_key_header)):
    if not API_KEY:
        return
    if key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API Key inválida.")


async def verify_api_key_or_param(
    request: Request,
    header_key: Optional[str] = Security(api_key_header),
):
    """Aceita API key via header ou query param (necessário para src de <video>)."""
    if not API_KEY:
        return
    key = header_key or request.query_params.get("api_key", "")
    if key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API Key inválida.")


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health", tags=["Sistema"])
def health():
    return {
        "status": "ok",
        "storage": "google_drive" if storage.is_using_drive else "memory",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ── Exercícios ────────────────────────────────────────────────────────────────

@app.get("/exercicios", response_model=List[Exercicio], tags=["Exercícios"])
def list_exercicios(deps=Depends(verify_api_key)):
    return storage.load().exercicios


@app.post("/exercicios", response_model=Exercicio, status_code=201, tags=["Exercícios"])
def create_exercicio(body: ExercicioCreate, deps=Depends(verify_api_key)):
    data = storage.load()
    ex = Exercicio(**body.model_dump())
    data.exercicios.append(ex)
    storage.save(data)
    return ex


@app.get("/exercicios/{ex_id}", response_model=Exercicio, tags=["Exercícios"])
def get_exercicio(ex_id: str, deps=Depends(verify_api_key)):
    for e in storage.load().exercicios:
        if e.id == ex_id:
            return e
    raise HTTPException(status_code=404, detail="Exercício não encontrado.")


@app.put("/exercicios/{ex_id}", response_model=Exercicio, tags=["Exercícios"])
def update_exercicio(ex_id: str, body: ExercicioUpdate, deps=Depends(verify_api_key)):
    data = storage.load()
    for i, e in enumerate(data.exercicios):
        if e.id == ex_id:
            updated = e.model_dump()
            patch = {k: v for k, v in body.model_dump().items() if v is not None}
            updated.update(patch)
            updated["updated_at"] = datetime.utcnow().isoformat()
            data.exercicios[i] = Exercicio(**updated)
            storage.save(data)
            return data.exercicios[i]
    raise HTTPException(status_code=404, detail="Exercício não encontrado.")


@app.delete("/exercicios/{ex_id}", status_code=204, tags=["Exercícios"])
def delete_exercicio(ex_id: str, deps=Depends(verify_api_key)):
    data = storage.load()
    original = len(data.exercicios)
    data.exercicios = [e for e in data.exercicios if e.id != ex_id]
    if len(data.exercicios) == original:
        raise HTTPException(status_code=404, detail="Exercício não encontrado.")
    # remove referências em treinos
    for t in data.treinos:
        t.exercises = [x for x in t.exercises if x.exercise_id != ex_id]
    storage.save(data)


# ── Treinos ───────────────────────────────────────────────────────────────────

@app.get("/treinos", response_model=List[Treino], tags=["Treinos"])
def list_treinos(deps=Depends(verify_api_key)):
    return storage.load().treinos


@app.post("/treinos", response_model=Treino, status_code=201, tags=["Treinos"])
def create_treino(body: TreinoCreate, deps=Depends(verify_api_key)):
    data = storage.load()
    treino = Treino(**body.model_dump())
    data.treinos.append(treino)
    storage.save(data)
    return treino


@app.get("/treinos/{treino_id}", response_model=Treino, tags=["Treinos"])
def get_treino(treino_id: str, deps=Depends(verify_api_key)):
    for t in storage.load().treinos:
        if t.id == treino_id:
            return t
    raise HTTPException(status_code=404, detail="Treino não encontrado.")


@app.put("/treinos/{treino_id}", response_model=Treino, tags=["Treinos"])
def update_treino(treino_id: str, body: TreinoUpdate, deps=Depends(verify_api_key)):
    data = storage.load()
    for i, t in enumerate(data.treinos):
        if t.id == treino_id:
            updated = t.model_dump()
            patch = {k: v for k, v in body.model_dump().items() if v is not None}
            updated.update(patch)
            updated["updated_at"] = datetime.utcnow().isoformat()
            data.treinos[i] = Treino(**updated)
            storage.save(data)
            return data.treinos[i]
    raise HTTPException(status_code=404, detail="Treino não encontrado.")


@app.delete("/treinos/{treino_id}", status_code=204, tags=["Treinos"])
def delete_treino(treino_id: str, deps=Depends(verify_api_key)):
    data = storage.load()
    original = len(data.treinos)
    data.treinos = [t for t in data.treinos if t.id != treino_id]
    if len(data.treinos) == original:
        raise HTTPException(status_code=404, detail="Treino não encontrado.")
    storage.save(data)


# ── Notas ─────────────────────────────────────────────────────────────────────

@app.get("/notas", response_model=List[Nota], tags=["Notas"])
def list_notas(deps=Depends(verify_api_key)):
    return storage.load().notas


@app.post("/notas", response_model=Nota, status_code=201, tags=["Notas"])
def create_nota(body: NotaCreate, deps=Depends(verify_api_key)):
    data = storage.load()
    nota = Nota(**body.model_dump())
    data.notas.insert(0, nota)
    storage.save(data)
    return nota


@app.put("/notas/{nota_id}", response_model=Nota, tags=["Notas"])
def update_nota(nota_id: str, body: NotaUpdate, deps=Depends(verify_api_key)):
    data = storage.load()
    for i, n in enumerate(data.notas):
        if n.id == nota_id:
            updated = n.model_dump()
            patch = {k: v for k, v in body.model_dump().items() if v is not None}
            updated.update(patch)
            updated["updated_at"] = datetime.utcnow().isoformat()
            data.notas[i] = Nota(**updated)
            storage.save(data)
            return data.notas[i]
    raise HTTPException(status_code=404, detail="Nota não encontrada.")


@app.delete("/notas/{nota_id}", status_code=204, tags=["Notas"])
def delete_nota(nota_id: str, deps=Depends(verify_api_key)):
    data = storage.load()
    original = len(data.notas)
    data.notas = [n for n in data.notas if n.id != nota_id]
    if len(data.notas) == original:
        raise HTTPException(status_code=404, detail="Nota não encontrada.")
    storage.save(data)


# ── Vídeos (proxy Google Drive) ───────────────────────────────────────────────

@app.get("/videos/{file_id}", tags=["Vídeos"])
async def stream_video(file_id: str, request: Request, deps=Depends(verify_api_key_or_param)):
    """Faz proxy de um ficheiro de vídeo do Google Drive com suporte a Range requests."""
    if not storage.is_using_drive:
        raise HTTPException(status_code=503, detail="Google Drive não disponível.")

    try:
        session = storage.get_drive_session()

        # Metadados: tipo MIME e tamanho
        meta = session.get(
            f"https://www.googleapis.com/drive/v3/files/{file_id}",
            params={"fields": "mimeType,size", "supportsAllDrives": "true"},
            timeout=10,
        )
        if meta.status_code == 404:
            raise HTTPException(status_code=404, detail="Ficheiro não encontrado no Drive.")
        meta.raise_for_status()
        meta_json = meta.json()
        content_type = meta_json.get("mimeType", "video/mp4")
        file_size = int(meta_json.get("size", 0))

        range_header = request.headers.get("Range")
        drive_params = {"alt": "media", "supportsAllDrives": "true"}
        drive_headers = {}

        if range_header and file_size:
            m = re.match(r"bytes=(\d+)-(\d*)", range_header)
            if m:
                start = int(m.group(1))
                end = int(m.group(2)) if m.group(2) else file_size - 1
                end = min(end, file_size - 1)
                drive_headers["Range"] = f"bytes={start}-{end}"

                resp = session.get(
                    f"https://www.googleapis.com/drive/v3/files/{file_id}",
                    params=drive_params,
                    headers=drive_headers,
                    stream=True,
                    timeout=60,
                )
                resp.raise_for_status()

                def _iter():
                    for chunk in resp.iter_content(chunk_size=65536):
                        yield chunk

                return StreamingResponse(
                    _iter(),
                    status_code=206,
                    headers={
                        "Content-Range": f"bytes {start}-{end}/{file_size}",
                        "Accept-Ranges": "bytes",
                        "Content-Length": str(end - start + 1),
                        "Content-Type": content_type,
                    },
                )

        # Pedido completo
        resp = session.get(
            f"https://www.googleapis.com/drive/v3/files/{file_id}",
            params=drive_params,
            stream=True,
            timeout=60,
        )
        resp.raise_for_status()

        headers = {"Accept-Ranges": "bytes", "Content-Type": content_type}
        if file_size:
            headers["Content-Length"] = str(file_size)

        def _iter():
            for chunk in resp.iter_content(chunk_size=65536):
                yield chunk

        return StreamingResponse(_iter(), headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao fazer stream do vídeo {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao aceder ao vídeo.")
