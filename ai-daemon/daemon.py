#!/usr/bin/env python3
"""
AI_M_OS AI-daemon — Alpha 0.3.0
Сбор метрик → PostgreSQL + эвристики планировщика.

Запуск:
    AIMOS_DB_DSN="postgresql://aimos:aimos@localhost/aimos_metrics" python daemon.py

Env vars:
    AIMOS_DB_DSN    — строка подключения к PostgreSQL
    AIMOS_INTERVAL  — интервал сбора метрик в секундах (default: 1)
    AIMOS_NO_DB     — если задана, логирование в БД отключено
"""
import logging
import os
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("aimos.daemon")

INTERVAL = float(os.getenv("AIMOS_INTERVAL", "1"))
NO_DB    = os.getenv("AIMOS_NO_DB") is not None


def main():
    logger.info("AI_M_OS AI-daemon starting (Alpha 0.3.0)")

    db_conn = None
    if not NO_DB:
        try:
            from db.logger import get_conn, init_schema
            db_conn = get_conn()
            init_schema(db_conn)
            logger.info("PostgreSQL connected")
        except Exception as e:
            logger.warning("PostgreSQL unavailable, running without DB: %s", e)
            db_conn = None

    from collectors.metrics import collect
    from scheduler.heuristics import run_heuristics

    logger.info("Collecting metrics every %.1fs", INTERVAL)

    while True:
        try:
            snap = collect()
            logger.debug(
                "CPU: %.1f%%  RAM: %dMB/%dMB  load: %.2f",
                snap.cpu_total_pct,
                snap.mem_used_kb // 1024,
                snap.mem_total_kb // 1024,
                snap.load_avg_1,
            )

            if db_conn:
                from db.logger import log_snapshot
                log_snapshot(db_conn, snap)

            events = run_heuristics(snap, db_conn)
            for ev in events:
                logger.info("Scheduler event: %s", ev)

        except KeyboardInterrupt:
            logger.info("Shutting down")
            break
        except Exception as e:
            logger.error("Tick error: %s", e)

        time.sleep(INTERVAL)

    if db_conn:
        db_conn.close()


if __name__ == "__main__":
    main()
