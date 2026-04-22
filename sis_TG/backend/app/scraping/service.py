"""Servicio para ejecutar scrapers desde el backend."""

import logging
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.restaurants.models import Restaurant, ScrapingImport
from app.scoring.engine import calculate_all_scores
from app.migration_tool.migrate_sqlite import (
    clean_address, clean_phone, parse_coords_from_url, detect_zone,
)

logger = logging.getLogger("app.scraping.service")

# Agregar el directorio raíz del proyecto al path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ---------------------------------------------------------------------------
# Registro en memoria de trabajos de scraping en curso / completados
# ---------------------------------------------------------------------------
# Estructura de cada trabajo:
# {
#   "status": "running" | "completed" | "error",
#   "source": str,
#   "steps_done": int,
#   "steps_total": int,
#   "current_step": str,
#   "total_scraped": int,
#   "imported": int,
#   "skipped": int,
#   "message": str,
#   "started_at": str (ISO),
#   "finished_at": str | None,
# }
_JOBS: dict[str, dict] = {}
_JOBS_LOCK = threading.Lock()

# Zonas de Google Maps + páginas de Bolivia para calcular total_steps
_GMAPS_ZONES = 12   # len(config.GMAPS_QUERIES)
_BOLIVIA_PAGES = 5  # config.BOLIVIA_MAX_PAGES


def get_job(job_id: str) -> Optional[dict]:
    """Retorna el estado de un trabajo por su ID."""
    return _JOBS.get(job_id)


def list_jobs() -> list[dict]:
    """Retorna todos los trabajos registrados."""
    with _JOBS_LOCK:
        return [{"job_id": jid, **data} for jid, data in _JOBS.items()]


class ScrapingService:
    """Ejecuta scrapers en background y guarda resultados en la DB."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def start_scraper(
        self, source: str = "all", headless: bool = True, limit: Optional[int] = None
    ) -> str:
        """Lanza el scraper en un hilo de background y retorna el job_id.

        Args:
            source: "bolivia", "gmaps", o "all"
            headless: Ejecutar Chrome sin ventana
            limit: Límite de restaurantes por fuente

        Returns:
            job_id (str UUID) para hacer polling del progreso
        """
        job_id = str(uuid.uuid4())

        # Calcular número total de pasos según la fuente
        steps_total = 0
        if source in ("gmaps", "all"):
            steps_total += _GMAPS_ZONES
        if source in ("bolivia", "all"):
            steps_total += _BOLIVIA_PAGES
        steps_total += 1  # paso final: importar a DB

        with _JOBS_LOCK:
            _JOBS[job_id] = {
                "status": "running",
                "source": source,
                "steps_done": 0,
                "steps_total": steps_total,
                "current_step": "Iniciando scraping...",
                "total_scraped": 0,
                "imported": 0,
                "skipped": 0,
                "message": "",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "finished_at": None,
            }

        # Lanzar en hilo daemon (no bloquea el shutdown del servidor)
        thread = threading.Thread(
            target=self._run_in_background,
            args=(job_id, source, headless, limit),
            daemon=True,
        )
        thread.start()

        return job_id

    def _update_job(self, job_id: str, **kwargs) -> None:
        with _JOBS_LOCK:
            if job_id in _JOBS:
                _JOBS[job_id].update(kwargs)

    def _make_progress_callback(self, job_id: str):
        """Crea un callback de progreso que actualiza el registro del trabajo."""
        def callback(message: str, step: int, _total: int) -> None:
            with _JOBS_LOCK:
                if job_id in _JOBS:
                    _JOBS[job_id]["current_step"] = message
                    _JOBS[job_id]["steps_done"] = step
        return callback

    def _run_in_background(
        self, job_id: str, source: str, headless: bool, limit: Optional[int]
    ) -> None:
        """Ejecuta el scraping completo en segundo plano."""
        # El hilo no hereda el sys.path del proceso uvicorn automáticamente.
        # service.py está en sis_TG/backend/app/scraping/ → subir 5 niveles
        # llega a Sistema_Scraping_Don_Piotr/ donde vive scraping_don_piotr/
        _scraping_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        if str(_scraping_root) not in sys.path:
            sys.path.insert(0, str(_scraping_root))

        from scraping_don_piotr.bolivia_scraper import BoliviaEnTusManosScraper
        from scraping_don_piotr.gmaps_scraper import GoogleMapsScraper

        all_results = []
        progress_cb = self._make_progress_callback(job_id)

        try:
            # Google Maps
            if source in ("gmaps", "all"):
                logger.info("Iniciando scraper de Google Maps...")
                self._update_job(job_id, current_step="Iniciando Google Maps...")
                try:
                    gmaps = GoogleMapsScraper(headless=headless)
                    gmaps_data = gmaps.scrape(limit=limit, progress_callback=progress_cb)
                    all_results.extend(gmaps_data)
                    logger.info(f"Google Maps: {len(gmaps_data)} restaurantes")
                except Exception as e:
                    logger.error(f"Error en Google Maps scraper: {e}")

            # Bolivia en tus Manos
            if source in ("bolivia", "all"):
                logger.info("Iniciando scraper de Bolivia en tus Manos...")
                self._update_job(job_id, current_step="Iniciando Bolivia en tus Manos...")
                # Ajustar offset del paso para que continúe donde dejó gmaps
                gmaps_offset = _GMAPS_ZONES if source == "all" else 0

                def bolivia_cb(message: str, step: int, _total: int) -> None:
                    with _JOBS_LOCK:
                        if job_id in _JOBS:
                            _JOBS[job_id]["current_step"] = message
                            _JOBS[job_id]["steps_done"] = gmaps_offset + step

                try:
                    bolivia = BoliviaEnTusManosScraper()
                    bolivia_data = bolivia.scrape(limit=limit, progress_callback=bolivia_cb)
                    all_results.extend(bolivia_data)
                    logger.info(f"Bolivia en tus Manos: {len(bolivia_data)} restaurantes")
                except Exception as e:
                    logger.error(f"Error en Bolivia scraper: {e}")

            self._update_job(
                job_id,
                current_step="Importando a base de datos...",
                total_scraped=len(all_results),
            )

            if not all_results:
                self._update_job(
                    job_id,
                    status="completed",
                    message="No se encontraron restaurantes.",
                    finished_at=datetime.now(timezone.utc).isoformat(),
                )
                return

            # Necesitamos una sesión de DB nueva (el hilo no puede reutilizar la sesión del request)
            from app.database import SessionLocal
            db = SessionLocal()
            try:
                records = [r.to_dict() for r in all_results]
                imported, skipped = self._import_to_db_session(records, source, db)
                self._update_job(
                    job_id,
                    status="completed",
                    imported=imported,
                    skipped=skipped,
                    steps_done=_JOBS[job_id]["steps_total"],
                    current_step="Completado",
                    message=(
                        f"Scraping completado: {len(records)} encontrados, "
                        f"{imported} importados, {skipped} omitidos (duplicados)"
                    ),
                    finished_at=datetime.now(timezone.utc).isoformat(),
                )
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error fatal en job {job_id}: {e}")
            self._update_job(
                job_id,
                status="error",
                message=f"Error: {e}",
                finished_at=datetime.now(timezone.utc).isoformat(),
            )

    def _import_to_db_session(
        self, records: list[dict], source_info: str, db: Session
    ) -> tuple[int, int]:
        """Importa registros de scraping a la base de datos."""
        imported = 0
        skipped = 0

        for record in records:
            nombre = (record.get("nombre") or "").strip()
            fuente = (record.get("fuente") or "").strip()

            if not nombre:
                skipped += 1
                continue

            existing = db.query(Restaurant).filter(
                Restaurant.nombre == nombre, Restaurant.fuente == fuente
            ).first()
            if existing:
                # Actualizar website_url si ahora lo tenemos y antes no
                if record.get("website_url") and not existing.website_url:
                    existing.website_url = record["website_url"]
                    db.commit()
                skipped += 1
                continue

            direccion = clean_address(record.get("direccion"))
            telefono = clean_phone(record.get("telefono"))

            lat, lon = None, None
            if record.get("latitud"):
                try:
                    lat = float(record["latitud"])
                except (ValueError, TypeError):
                    pass
            if record.get("longitud"):
                try:
                    lon = float(record["longitud"])
                except (ValueError, TypeError):
                    pass

            if lat is None or lon is None:
                lat, lon = parse_coords_from_url(record.get("url"))

            rating = None
            if record.get("rating") is not None:
                try:
                    rating = float(record["rating"])
                    if rating < 0 or rating > 5:
                        rating = None
                except (ValueError, TypeError):
                    pass

            num_resenas = None
            if record.get("num_resenas") is not None:
                try:
                    num_resenas = int(record["num_resenas"])
                except (ValueError, TypeError):
                    pass

            restaurant = Restaurant(
                fuente=fuente,
                url=record.get("url"),
                nombre=nombre,
                direccion=direccion,
                telefono=telefono,
                rating=rating,
                num_resenas=num_resenas,
                latitud=lat,
                longitud=lon,
                precio=record.get("precio"),
                tipo_cocina=record.get("tipo_cocina"),
                categoria=record.get("categoria"),
                descripcion=record.get("descripcion"),
                servicios=record.get("servicios"),
                zona=detect_zone(direccion) or record.get("zona"),
                website_url=record.get("website_url"),
                status="nuevo",
                scraped_at=datetime.now(timezone.utc),
            )
            db.add(restaurant)
            imported += 1

        db.commit()

        log = ScrapingImport(
            source_file=f"scraper_{source_info}",
            source_type="scraper",
            records_total=len(records),
            records_imported=imported,
            records_skipped=skipped,
        )
        db.add(log)
        db.commit()

        if imported > 0:
            calculate_all_scores(db)

        logger.info(f"Importados {imported} restaurantes, {skipped} omitidos")
        return imported, skipped

    # ------------------------------------------------------------------
    # Mantener compatibilidad con código antiguo (usado en tests / CLI)
    # ------------------------------------------------------------------
    def run_scraper(
        self, source: str = "all", headless: bool = True, limit: Optional[int] = None
    ) -> dict:
        """Versión síncrona legacy — lanza el job y espera su finalización.
        Usar start_scraper() para la versión asíncrona con progreso.
        """
        job_id = self.start_scraper(source=source, headless=headless, limit=limit)
        # Esperar a que termine (bloqueante — solo para uso directo desde CLI)
        import time
        while True:
            job = get_job(job_id)
            if job and job["status"] in ("completed", "error"):
                return job
            time.sleep(2)
