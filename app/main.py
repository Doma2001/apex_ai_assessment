import json
import logging
import os
import sqlite3
import sys

from flask import Flask, jsonify, request

VERSION = os.getenv("APP_VERSION", "dev")
DB_PATH = os.getenv("DB_PATH", "/data/app.db")


class JsonFmt(logging.Formatter):
    def format(self, r):
        d = {"ts": self.formatTime(r), "level": r.levelname,
             "msg": r.getMessage(), "version": VERSION}
        d.update(getattr(r, "fields", {}))
        return json.dumps(d)


log = logging.getLogger("apex")
if not log.handlers:
    _h = logging.StreamHandler(sys.stdout)
    _h.setFormatter(JsonFmt())
    log.addHandler(_h)
log.setLevel(logging.INFO)



def create_app(db_path=None):
    app = Flask(__name__)
    path = db_path or DB_PATH
    counters = {"requests_total": 0, "errors_total": 0}

    def db():
        c = sqlite3.connect(path)
        c.row_factory = sqlite3.Row
        return c

    try:
        with db() as c:
            c.execute("CREATE TABLE IF NOT EXISTS ops (id INTEGER PRIMARY KEY, "
                      "name TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open')")
    except sqlite3.Error as e:
        log.error("db_init_failed", extra={"fields": {"error": str(e), "db_path": path}})

    @app.after_request
    def _log(resp):
        counters["requests_total"] += 1
        if resp.status_code >= 500:
            counters["errors_total"] += 1
        log.info("request", extra={"fields": {
            "method": request.method, "path": request.path, "status": resp.status_code}})
        return resp

    @app.get("/health")
    def health():
        return jsonify(status="ok", version=VERSION)

    @app.get("/ready")
    def ready():
        try:
            with db() as c:
                c.execute("SELECT 1 FROM ops LIMIT 1")
            return jsonify(status="ready")
        except sqlite3.Error as e:
            log.error("db_unavailable", extra={"fields": {"error": str(e)}})
            return jsonify(status="not_ready"), 503

    @app.get("/ops")
    def list_ops():
        with db() as c:
            rows = c.execute("SELECT id, name, status FROM ops").fetchall()
        return jsonify([dict(r) for r in rows])

    @app.post("/ops")
    def create_op():
        name = (request.get_json(silent=True) or {}).get("name", "").strip()
        if not name:
            return jsonify(error="name is required"), 400
        with db() as c:
            cur = c.execute("INSERT INTO ops (name) VALUES (?)", (name,))
        return jsonify(id=cur.lastrowid, name=name, status="open"), 201

    @app.get("/metrics")
    def metrics():
        body = "".join(f"apex_{k} {v}\n" for k, v in counters.items())
        return body, 200, {"Content-Type": "text/plain"}

    return app


app = create_app()
