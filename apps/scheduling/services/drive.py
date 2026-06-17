"""Integração Google Drive para upload de relatórios (Sprint 09, SDD §22.2.7).

Salva os 2 .md gerados por execução em:
  hermes-backup/{tenant_slug}/relatorios-solver/
  hermes-backup/{tenant_slug}/grades-geradas/

No MVP, usa LocalUploader (salva em disco). Produção usa DriveUploader
(com GAPI, upload real pro Drive).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Protocol

from django.conf import settings

logger = logging.getLogger(__name__)

# Diretório base pra upload local (dev/CI).
UPLOAD_DIR = Path("./reports")

# Folder ID do Google Drive onde os backup são salvos.
# Em produção, configure via settings.DRIVE_BACKUP_FOLDER_ID.
DRIVE_BACKUP_FOLDER_ID = getattr(settings, "DRIVE_BACKUP_FOLDER_ID", "")


class BaseUploader(Protocol):
    """Interface para uploaders de relatório."""

    def get_or_create_folder(self, tenant_slug: str, subfolder: str) -> str:
        """Retorna o ID (Drive) ou caminho (local) da pasta destino."""
        ...

    def upload_md(self, folder_id_or_path: str, filename: str, content: str) -> str:
        """Faz upload de um arquivo .md. Retorna o ID (Drive) ou caminho (local)."""
        ...


class LocalUploader:
    """Uploader que salva em disco (dev/CI)."""

    def get_or_create_folder(self, tenant_slug: str, subfolder: str) -> str:
        path = UPLOAD_DIR / tenant_slug / subfolder
        path.mkdir(parents=True, exist_ok=True)
        return str(path)

    def upload_md(self, folder_path: str, filename: str, content: str) -> str:
        path = Path(folder_path) / filename
        path.write_text(content, encoding="utf-8")
        logger.info("LocalUploader: saved %s", path)
        return str(path)


class DriveUploader:
    """Uploader que salva no Google Drive via GAPI.

    Requer:
    - google-api-python-client instalado
    - Token válido em settings.DRIVE_CREDENTIALS_PATH
    - DRIVE_BACKUP_FOLDER_ID configurado
    """

    def __init__(self) -> None:
        from google.oauth2.credentials import Credentials  # noqa: F401 - import lazy
        from googleapiclient.discovery import build

        token_path = Path(getattr(settings, "DRIVE_CREDENTIALS_PATH", ""))
        if not token_path.exists():
            raise FileNotFoundError(f"Drive token not found: {token_path}")

        creds_data = json.loads(token_path.read_text())
        self._creds = Credentials.from_authorized_user_info(creds_data)
        self._service = build("drive", "v3", credentials=self._creds)

    def get_or_create_folder(self, tenant_slug: str, subfolder: str) -> str:
        """Busca ou cria folder no Drive. Retorna o folder ID."""
        parent_id = self._get_or_create_subfolder(DRIVE_BACKUP_FOLDER_ID, tenant_slug)
        return self._get_or_create_subfolder(parent_id, subfolder)

    def _get_or_create_subfolder(self, parent_id: str, name: str) -> str:
        """Busca subfolder pelo nome dentro de parent_id. Cria se não existe."""
        from googleapiclient.errors import HttpError

        query = (
            f"'{parent_id}' in parents and "
            f"name='{name}' and "
            "mimeType='application/vnd.google-apps.folder' and "
            "trashed=false"
        )
        try:
            results = (
                self._service.files()
                .list(q=query, spaces="drive", fields="files(id, name)")
                .execute()
            )
            folders = results.get("files", [])
            if folders:
                return folders[0]["id"]
        except HttpError:
            logger.exception("Drive API error searching folder '%s'", name)

        # Create folder
        file_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }
        folder = self._service.files().create(body=file_metadata, fields="id").execute()
        logger.info("DriveUploader: created folder '%s' (id: %s)", name, folder["id"])
        return folder["id"]

    def upload_md(self, folder_id: str, filename: str, content: str) -> str:
        """Faz upload de um .md pro Drive. Retorna o file ID."""
        import io

        from googleapiclient.http import MediaInMemoryUpload

        file_metadata = {
            "name": filename,
            "parents": [folder_id],
        }
        media = MediaInMemoryUpload(
            content.encode("utf-8"),
            mimetype="text/markdown",
            resumable=True,
        )
        file = (
            self._service.files()
            .create(body=file_metadata, media_body=media, fields="id, webViewLink")
            .execute()
        )
        logger.info("DriveUploader: uploaded %s (id: %s)", filename, file.get("id"))
        return file.get("webViewLink", file.get("id", ""))


def upload_reports(
    school_year,
    runs: list,
    winning_run,
    uploader: BaseUploader | None = None,
) -> tuple[str, str]:
    """Gera os 2 .md e faz upload via uploader.

    Args:
        school_year: Instância de SchoolYear.
        runs: Lista de SolverRun.
        winning_run: SolverRun vencedor.
        uploader: Uploader a usar. Se None, usa LocalUploader.

    Returns:
        (relatorio_uri, grade_uri) — URI do arquivo salvo.
    """
    from apps.scheduling.services.report import (
        generate_grade_md,
        generate_solver_report_md,
    )

    if uploader is None:
        uploader = LocalUploader()

    from apps.scheduling.services.report import _ts_filename

    ts = _ts_filename()
    sy_slug = school_year.name.lower().replace(" ", "-")
    tenant_slug = str(school_year.tenant_id)[:8] if school_year.tenant_id else "default"

    relatorio_content = generate_solver_report_md(school_year, runs)
    grade_content = generate_grade_md(school_year, winning_run)

    relatorio_filename = f"relatorio-solver-{sy_slug}-{ts}.md"
    grade_filename = f"grade-{sy_slug}-{ts}.md"

    # Upload com try/except — falha não pode quebrar pipeline (§3.10)
    relatorio_uri = ""
    grade_uri = ""

    try:
        solver_folder = uploader.get_or_create_folder(tenant_slug, "relatorios-solver")
        relatorio_uri = uploader.upload_md(solver_folder, relatorio_filename, relatorio_content)
    except Exception:
        logger.exception("Falha ao fazer upload do relatório solver")

    try:
        grade_folder = uploader.get_or_create_folder(tenant_slug, "grades-geradas")
        grade_uri = uploader.upload_md(grade_folder, grade_filename, grade_content)
    except Exception:
        logger.exception("Falha ao fazer upload da grade")

    return relatorio_uri, grade_uri