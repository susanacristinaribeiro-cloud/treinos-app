"""
Camada de storage: Google Drive via requests + google-auth.
Credenciais e file_id em cache — apenas 1 chamada HTTP por operação.
"""
import json
import os
import logging
import time
from typing import Optional
from models import AppData

logger = logging.getLogger(__name__)

DRIVE_FILENAME = "treinos_data.json"
DRIVE_FOLDER_ID = os.environ.get("DRIVE_FOLDER_ID", "")


class DriveStorage:
    def __init__(self):
        self._memory: Optional[AppData] = None
        self._use_drive = False
        self._creds = None
        self._creds_expiry: float = 0.0
        self._file_id: Optional[str] = None
        self._init_check()

    def _build_credentials(self):
        scopes = ["https://www.googleapis.com/auth/drive"]
        creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if creds_json:
            from google.oauth2 import service_account
            return service_account.Credentials.from_service_account_info(
                json.loads(creds_json), scopes=scopes
            )
        import google.auth
        creds, _ = google.auth.default(scopes=scopes)
        return creds

    def _fresh_token(self) -> str:
        import requests as _requests
        import google.auth.transport.requests
        now = time.time()
        if self._creds is None or now >= self._creds_expiry - 60:
            if self._creds is None:
                self._creds = self._build_credentials()
            session = _requests.Session()
            req = google.auth.transport.requests.Request(session)
            self._creds.refresh(req)
            expiry = getattr(self._creds, "expiry", None)
            if expiry:
                import datetime
                if isinstance(expiry, datetime.datetime):
                    self._creds_expiry = expiry.timestamp()
                else:
                    self._creds_expiry = now + 3600
            else:
                self._creds_expiry = now + 3600
            logger.info("Token Google refrescado.")
        return self._creds.token

    def _session(self):
        import requests as _requests
        s = _requests.Session()
        s.headers.update({"Authorization": f"Bearer {self._fresh_token()}"})
        return s

    def _init_check(self):
        try:
            self._build_credentials()
            self._use_drive = True
            logger.info("Credenciais Google disponíveis.")
        except Exception as e:
            logger.warning(f"Sem credenciais ({e}) — a usar memória.")
            self._use_drive = False

    def _get_file_id(self) -> Optional[str]:
        if self._file_id:
            return self._file_id
        try:
            session = self._session()
            q = f"name='{DRIVE_FILENAME}' and trashed=false"
            if DRIVE_FOLDER_ID:
                q += f" and '{DRIVE_FOLDER_ID}' in parents"
            resp = session.get(
                "https://www.googleapis.com/drive/v3/files",
                params={
                    "q": q,
                    "fields": "files(id,name)",
                    "includeItemsFromAllDrives": "true",
                    "supportsAllDrives": "true",
                },
                timeout=15,
            )
            resp.raise_for_status()
            files = resp.json().get("files", [])
            if files:
                self._file_id = files[0]["id"]
                logger.info(f"Ficheiro encontrado e em cache: {self._file_id}")
                return self._file_id
            logger.warning(f"{DRIVE_FILENAME} não encontrado no Drive.")
            return None
        except Exception as e:
            logger.error(f"Erro ao pesquisar ficheiro: {e}")
            return None

    def load(self) -> AppData:
        if not self._use_drive:
            if self._memory is None:
                self._memory = AppData()
            return self._memory
        file_id = self._get_file_id()
        if not file_id:
            if self._memory is None:
                self._memory = AppData()
            return self._memory
        try:
            session = self._session()
            resp = session.get(
                f"https://www.googleapis.com/drive/v3/files/{file_id}",
                params={"alt": "media", "supportsAllDrives": "true"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return AppData(**data)
        except Exception as e:
            logger.error(f"Erro ao ler Drive: {e}")
            if self._memory is None:
                self._memory = AppData()
            return self._memory

    def save(self, data: AppData) -> bool:
        if not self._use_drive:
            self._memory = data
            return True
        file_id = self._get_file_id()
        if not file_id:
            self._memory = data
            return False
        try:
            session = self._session()
            content = json.dumps(
                data.model_dump(), ensure_ascii=False, indent=2
            ).encode("utf-8")
            resp = session.patch(
                f"https://www.googleapis.com/upload/drive/v3/files/{file_id}",
                params={"uploadType": "media", "supportsAllDrives": "true"},
                data=content,
                headers={"Content-Type": "application/json; charset=utf-8"},
                timeout=20,
            )
            resp.raise_for_status()
            logger.info("Guardado no Drive com sucesso.")
            return True
        except Exception as e:
            logger.error(f"Erro ao guardar: {e}")
            self._memory = data
            return False

    def get_drive_session(self):
        """Sessão autenticada para chamadas directas à Drive API."""
        if not self._use_drive:
            raise RuntimeError("Google Drive não disponível")
        return self._session()

    @property
    def is_using_drive(self) -> bool:
        return self._use_drive


storage = DriveStorage()
