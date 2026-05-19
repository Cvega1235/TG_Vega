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

# ---------------------------------------------------------------------------
# Trabajos de enriquecimiento en memoria
# ---------------------------------------------------------------------------
_ENRICH_JOBS: dict[str, dict] = {}
_ENRICH_LOCK = threading.Lock()

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

# Pasos por fuente (para calcular total_steps en la barra de progreso)
_GMAPS_ZONES = 12        # len(config.GMAPS_QUERIES)
_BOLIVIA_PAGES = 5       # config.BOLIVIA_MAX_PAGES
_TRIPADVISOR_STEPS = 1   # TripAdvisor API se trata como un bloque único
_IMPORT_STEP = 1         # importar a BD
_WEBSITE_STEP = 1        # scraping de sitios web propios


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
        if source == "all":
            steps_total += _TRIPADVISOR_STEPS
        steps_total += _IMPORT_STEP     # importar a BD
        steps_total += _WEBSITE_STEP    # scraping de sitios web propios

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
        # step_offset lleva cuenta del paso acumulado entre fuentes
        step_offset = 0

        try:
            # ── Google Maps ──────────────────────────────────────────────────
            if source in ("gmaps", "all"):
                logger.info("Iniciando scraper de Google Maps...")
                self._update_job(job_id, current_step="Iniciando Google Maps...")
                _offset = step_offset

                def gmaps_cb(message: str, step: int, _total: int) -> None:
                    with _JOBS_LOCK:
                        if job_id in _JOBS:
                            _JOBS[job_id]["current_step"] = message
                            _JOBS[job_id]["steps_done"] = _offset + step

                try:
                    gmaps = GoogleMapsScraper(headless=headless)
                    gmaps_data = gmaps.scrape(limit=limit, progress_callback=gmaps_cb)
                    all_results.extend(gmaps_data)
                    logger.info(f"Google Maps: {len(gmaps_data)} restaurantes")
                except Exception as e:
                    logger.error(f"Error en Google Maps scraper: {e}")
                step_offset += _GMAPS_ZONES

            # ── Bolivia en tus Manos ─────────────────────────────────────────
            if source in ("bolivia", "all"):
                logger.info("Iniciando scraper de Bolivia en tus Manos...")
                self._update_job(job_id, current_step="Iniciando Bolivia en tus Manos...")
                _offset = step_offset

                def bolivia_cb(message: str, step: int, _total: int) -> None:
                    with _JOBS_LOCK:
                        if job_id in _JOBS:
                            _JOBS[job_id]["current_step"] = message
                            _JOBS[job_id]["steps_done"] = _offset + step

                try:
                    bolivia = BoliviaEnTusManosScraper()
                    bolivia_data = bolivia.scrape(limit=limit, progress_callback=bolivia_cb)
                    all_results.extend(bolivia_data)
                    logger.info(f"Bolivia en tus Manos: {len(bolivia_data)} restaurantes")
                except Exception as e:
                    logger.error(f"Error en Bolivia scraper: {e}")
                step_offset += _BOLIVIA_PAGES

            # ── TripAdvisor API ───────────────────────────────────────────────
            if source == "all":
                logger.info("Iniciando scraper de TripAdvisor API...")
                self._update_job(
                    job_id,
                    current_step="TripAdvisor API: buscando restaurantes...",
                    steps_done=step_offset,
                )
                try:
                    from scraping_don_piotr.tripadvisor_api import TripAdvisorAPIScraper
                    trip_api = TripAdvisorAPIScraper()
                    trip_data = trip_api.scrape(limit=limit)
                    all_results.extend(trip_data)
                    logger.info(f"TripAdvisor API: {len(trip_data)} restaurantes")
                except ValueError as e:
                    logger.warning(f"TripAdvisor API no disponible: {e}")
                except Exception as e:
                    logger.error(f"Error en TripAdvisor API scraper: {e}")
                step_offset += _TRIPADVISOR_STEPS

            # ── Importar a BD ────────────────────────────────────────────────
            self._update_job(
                job_id,
                current_step="Importando a base de datos...",
                steps_done=step_offset,
                total_scraped=len(all_results),
            )

            if not all_results:
                self._update_job(
                    job_id,
                    status="completed",
                    message="No se encontraron restaurantes.",
                    steps_done=step_offset + _IMPORT_STEP + _WEBSITE_STEP,
                    finished_at=datetime.now(timezone.utc).isoformat(),
                )
                return

            from app.database import SessionLocal
            db = SessionLocal()
            try:
                records = [r.to_dict() for r in all_results]
                imported, skipped = self._import_to_db_session(records, source, db)
            finally:
                db.close()
            step_offset += _IMPORT_STEP

            # ── Scraping de sitios web propios ───────────────────────────────
            self._update_job(
                job_id,
                current_step="Scraping de sitios web propios...",
                steps_done=step_offset,
                imported=imported,
                skipped=skipped,
            )
            try:
                from scraping_don_piotr.website_scraper import run as run_website_scraper
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                run_website_scraper(limit=limit)
                logger.info("Scraping de sitios web completado")
            except Exception as e:
                logger.error(f"Error en website scraper: {e}")
            step_offset += _WEBSITE_STEP

            self._update_job(
                job_id,
                status="completed",
                imported=imported,
                skipped=skipped,
                steps_done=step_offset,
                current_step="Completado",
                message=(
                    f"Scraping completado: {len(records)} encontrados, "
                    f"{imported} importados, {skipped} omitidos (duplicados)"
                ),
                finished_at=datetime.now(timezone.utc).isoformat(),
            )

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
    # Enriquecimiento de datos de clientes existentes
    # ------------------------------------------------------------------

    def start_enrichment(self, headless: bool = True) -> str:
        """Lanza el enriquecimiento en background y retorna el job_id.

        Busca automáticamente todos los clientes con campos vacíos
        (teléfono, coordenadas, rating, tipo de cocina, sitio web) y
        ejecuta una búsqueda dirigida en Google Maps para cada uno.
        """
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            from sqlalchemy import or_
            enrichable = (
                db.query(Restaurant)
                .filter(
                    Restaurant.status == "cliente",
                    or_(
                        Restaurant.telefono.is_(None),
                        Restaurant.latitud.is_(None),
                        Restaurant.rating.is_(None),
                        Restaurant.tipo_cocina.is_(None),
                        Restaurant.website_url.is_(None),
                    ),
                )
                .with_entities(Restaurant.id, Restaurant.nombre, Restaurant.direccion)
                .all()
            )
            targets = [{"id": r.id, "nombre": r.nombre, "direccion": r.direccion} for r in enrichable]
        finally:
            db.close()

        job_id = str(uuid.uuid4())
        with _ENRICH_LOCK:
            _ENRICH_JOBS[job_id] = {
                "status": "running",
                "steps_done": 0,
                "steps_total": len(targets),
                "current_step": "Iniciando...",
                "results": [],
                "message": "",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "finished_at": None,
            }

        thread = threading.Thread(
            target=self._run_enrichment,
            args=(job_id, targets, headless),
            daemon=True,
        )
        thread.start()
        return job_id

    def _run_enrichment(self, job_id: str, targets: list[dict], headless: bool) -> None:
        """Ejecuta el enriquecimiento en segundo plano."""
        _scraping_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        if str(_scraping_root) not in sys.path:
            sys.path.insert(0, str(_scraping_root))

        results = []
        scraper = None
        try:
            from scraping_don_piotr.gmaps_scraper import GoogleMapsScraper
            from app.database import SessionLocal

            scraper = GoogleMapsScraper(headless=headless)
            scraper.setup_driver()
            for idx, target in enumerate(targets):
                rid = target["id"]
                nombre = target["nombre"]
                direccion = target.get("direccion")

                with _ENRICH_LOCK:
                    _ENRICH_JOBS[job_id]["current_step"] = f"Buscando: {nombre}"
                    _ENRICH_JOBS[job_id]["steps_done"] = idx

                try:
                    found = scraper.search_one(nombre, direccion)
                except Exception as e:
                    logger.warning(f"Error buscando '{nombre}': {e}")
                    found = None

                entry: dict = {"restaurant_id": rid, "restaurant_nombre": nombre, "found": False, "updates": {}}
                if found:
                    updates: dict = {}
                    if found.telefono:
                        updates["telefono"] = found.telefono
                    if found.latitud is not None:
                        updates["latitud"] = found.latitud
                    if found.longitud is not None:
                        updates["longitud"] = found.longitud
                    if found.rating is not None:
                        updates["rating"] = found.rating
                    if found.num_resenas is not None:
                        updates["num_resenas"] = found.num_resenas
                    if found.tipo_cocina:
                        updates["tipo_cocina"] = found.tipo_cocina
                    if found.website_url:
                        updates["website_url"] = found.website_url

                    if updates:
                        # Only keep updates for fields currently NULL in DB
                        db = SessionLocal()
                        try:
                            r = db.query(Restaurant).filter(Restaurant.id == rid).first()
                            if r:
                                filtered: dict = {}
                                for field, val in updates.items():
                                    if getattr(r, field, None) is None:
                                        filtered[field] = val
                                updates = filtered
                        finally:
                            db.close()

                    if updates:
                        entry["found"] = True
                        entry["updates"] = updates

                results.append(entry)

            with _ENRICH_LOCK:
                _ENRICH_JOBS[job_id].update({
                    "status": "completed",
                    "steps_done": len(targets),
                    "current_step": "Completado",
                    "results": results,
                    "message": (
                        f"{sum(1 for r in results if r['found'])} restaurantes con datos nuevos "
                        f"de {len(targets)} buscados."
                    ),
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                })

        except Exception as e:
            logger.error(f"Error fatal en enriquecimiento {job_id}: {e}")
            with _ENRICH_LOCK:
                _ENRICH_JOBS[job_id].update({
                    "status": "error",
                    "message": f"Error: {e}",
                    "results": results,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                })
        finally:
            try:
                if scraper.driver:
                    scraper.driver.quit()
            except Exception:
                pass

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
