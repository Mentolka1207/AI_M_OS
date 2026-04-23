"""
PostgreSQL logger for AI_M_OS metrics.
Uses psycopg2 (sync) - sufficient for 1-second interval.
"""
import logging
import os
import psycopg2
from psycopg2.extras import execute_values
from collectors.metrics import SystemSnapshot

logger = logging.getLogger(__name__)

DSN = os.getenv(
    "AIMOS_DB_DSN",
    "postgresql://aimos:aimos@localhost:5432/aimos_metrics"
)

def get_conn():
    return psycopg2.connect(DSN)

def init_schema(conn):
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path) as f:
        sql = f.read()
    with conn.cu(r) as cur:
        cur.execute(sql)
    conn.commit()
    logger.info("Schema initialized")

def log_snapshot(conn, snap: SystemSnapshot):
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO metrics_cpu(ts, total_pct, cores_pct, load_avg) "
                "VALUES (to_timestamp(%s), %s, %s, %s)",
                (snap.timestamp, snap.cpu_total_pct,
                 snap.cpu_cores_pct, snap.load_avg_1)
            )
            cur.execute(
                "INSERT INTO metrics_memory(ts, total_kb, used_kb, swap_total_kb, swap_used_kb) "
                "VALUES (to_timestamp(%s), %s, %s, %s, %s)",
                (snap.timestamp, snap.mem_total_kb, snap.mem_used_kb,
                 snap.swap_total_kb, snap.swap_used_kb)
            )
            # FIX: pass raw float timestamp directly, not a string
            if snap.net_ifaces:
                rows = [
                    (snap.timestamp, iface,
                     stats.get("rx_bps", 0), stats.get("tx_bps", 0))
                    for iface, stats in snap.net_ifaces.items()
                ]
                execute_values(
                    cur,
                    "INSERT INTO metrics_network(ts, iface, rx_bps, tx_bps) "
                    "VALUES %s",
                    rows,
                    template="(to_timestamp(%s), %s, %s, %s)"
                )
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error("DB write failed: %s", e)

def log_scheduler_event(conn, pid: int, action: str,
                        old_nice: int, new_nice: int, reason: str):
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO scheduler_events(pid, action, old_nice, new_nice, reason) "
                "VALUES (%s, %s, %s, %s, %s)",
                (pid, action, old_nice, new_nice, reason)
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error("Scheduler event log failed: %s", e)
