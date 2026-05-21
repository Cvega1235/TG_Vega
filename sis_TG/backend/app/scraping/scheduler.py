"""
scheduler.py
Gestiona el scraping periódico automático con APScheduler.
"""

import logging
from datetime import datetime, timezone, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger("app.scraping.scheduler")

_scheduler = BackgroundScheduler(timezone="America/La_Paz")
_JOB_ID = "scraping_periodic"


def _run_scraping(source: str, interval_days: int) -> None:
    """Ejecuta el scraping y actualiza next_run_at en la BD."""
    from app.database import SessionLocal
    from app.scraping.service import ScrapingService
    from app.restaurants.models import ScrapingScheduleConfig

    logger.info(f"Scheduler: iniciando scraping automático (fuente={source})")
    db = SessionLocal()
    try:
        service = ScrapingService(db)
        service.start_scraper(source=source, headless=True)

        cfg = db.query(ScrapingScheduleConfig).first()
        if cfg and cfg.active:
            cfg.next_run_at = datetime.now(timezone.utc) + timedelta(days=interval_days)
            db.commit()
            logger.info(f"Scheduler: próxima ejecución en {cfg.next_run_at}")
    except Exception as e:
        logger.error(f"Scheduler: error en scraping automático: {e}")
    finally:
        db.close()


def start_scheduler() -> None:
    """Arranca el scheduler y restaura la configuración guardada en BD."""
    if not _scheduler.running:
        _scheduler.start()
        logger.info("APScheduler iniciado")

    _restore_from_db()


def _restore_from_db() -> None:
    """Carga la config persistida y reprograma el job si está activo."""
    from app.database import SessionLocal
    from app.restaurants.models import ScrapingScheduleConfig

    db = SessionLocal()
    try:
        cfg = db.query(ScrapingScheduleConfig).first()
        if cfg and cfg.active:
            _schedule_job(cfg.source, cfg.interval_days, cfg.start_at)
            logger.info(f"Scheduler: job restaurado (intervalo={cfg.interval_days}d, fuente={cfg.source})")
    except Exception as e:
        logger.error(f"Scheduler: error restaurando config: {e}")
    finally:
        db.close()


def _schedule_job(source: str, interval_days: int, start_at: datetime) -> None:
    """Programa o reprograma el job periódico."""
    _remove_job()

    now = datetime.now(timezone.utc)
    if start_at.tzinfo is None:
        start_at = start_at.replace(tzinfo=timezone.utc)

    if start_at > now:
        # Primera ejecución en el futuro — usar DateTrigger para la primera vez
        # y luego el propio job reprogramará con IntervalTrigger
        _scheduler.add_job(
            _run_scraping,
            trigger=DateTrigger(run_date=start_at),
            id=_JOB_ID,
            kwargs={"source": source, "interval_days": interval_days},
            replace_existing=True,
            misfire_grace_time=3600,
        )
    else:
        # start_at ya pasó — calcular próxima ejecución basada en intervalo
        elapsed = (now - start_at).total_seconds()
        interval_secs = interval_days * 86400
        periods_passed = int(elapsed // interval_secs)
        next_run = start_at + timedelta(seconds=interval_secs * (periods_passed + 1))

        _scheduler.add_job(
            _run_scraping,
            trigger=IntervalTrigger(days=interval_days, start_date=next_run),
            id=_JOB_ID,
            kwargs={"source": source, "interval_days": interval_days},
            replace_existing=True,
            misfire_grace_time=3600,
        )


def _remove_job() -> None:
    if _scheduler.get_job(_JOB_ID):
        _scheduler.remove_job(_JOB_ID)


def save_schedule(source: str, interval_days: int, start_at: datetime) -> datetime:
    """Persiste la config en BD, programa el job y retorna next_run_at."""
    from app.database import SessionLocal
    from app.restaurants.models import ScrapingScheduleConfig

    _schedule_job(source, interval_days, start_at)

    now = datetime.now(timezone.utc)
    if start_at.tzinfo is None:
        start_at = start_at.replace(tzinfo=timezone.utc)

    if start_at > now:
        next_run_at = start_at
    else:
        elapsed = (now - start_at).total_seconds()
        interval_secs = interval_days * 86400
        periods_passed = int(elapsed // interval_secs)
        next_run_at = start_at + timedelta(seconds=interval_secs * (periods_passed + 1))

    db = SessionLocal()
    try:
        cfg = db.query(ScrapingScheduleConfig).first()
        if cfg:
            cfg.active = True
            cfg.interval_days = interval_days
            cfg.source = source
            cfg.start_at = start_at
            cfg.next_run_at = next_run_at
            cfg.updated_at = now
        else:
            cfg = ScrapingScheduleConfig(
                active=True,
                interval_days=interval_days,
                source=source,
                start_at=start_at,
                next_run_at=next_run_at,
                updated_at=now,
            )
            db.add(cfg)
        db.commit()
    finally:
        db.close()

    logger.info(f"Scheduler guardado: intervalo={interval_days}d fuente={source} próxima={next_run_at}")
    return next_run_at


def cancel_schedule() -> None:
    """Desactiva el schedule en BD y elimina el job."""
    from app.database import SessionLocal
    from app.restaurants.models import ScrapingScheduleConfig

    _remove_job()

    db = SessionLocal()
    try:
        cfg = db.query(ScrapingScheduleConfig).first()
        if cfg:
            cfg.active = False
            cfg.next_run_at = None
            cfg.updated_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()

    logger.info("Scheduler cancelado")


def get_schedule_status() -> dict:
    """Retorna el estado actual del schedule desde la BD."""
    from app.database import SessionLocal
    from app.restaurants.models import ScrapingScheduleConfig

    db = SessionLocal()
    try:
        cfg = db.query(ScrapingScheduleConfig).first()
        if not cfg:
            return {"active": False}
        return {
            "active": cfg.active,
            "interval_days": cfg.interval_days,
            "source": cfg.source,
            "start_at": cfg.start_at.isoformat() if cfg.start_at else None,
            "next_run_at": cfg.next_run_at.isoformat() if cfg.next_run_at else None,
        }
    finally:
        db.close()


def shutdown_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("APScheduler detenido")
