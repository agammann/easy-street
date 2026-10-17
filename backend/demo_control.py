"""Persistent, shared inference accounting for the separate judging deployment."""
from contextlib import contextmanager
from datetime import datetime, timezone
import math
from pathlib import Path
import sqlite3
import threading
import uuid

from .provider import (ProviderCallRejected, UsageCounts, cost, generation_input_bound,
                       verification_input_bound, MAX_GENERATION_TOKENS, MAX_VERIFICATION_TOKENS)


class DemoLedger:
    def __init__(self, path: Path, limit: float, concurrency=2):
        if not math.isfinite(limit) or not 0 <= limit <= 10000:
            raise ValueError("Choose a finite demo budget between zero and 10000 USD.")
        self.path, self.limit = path, limit
        self.slots = threading.BoundedSemaphore(concurrency)
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS calls(id TEXT PRIMARY KEY, session_id TEXT NOT NULL,
                    model TEXT NOT NULL, stage TEXT NOT NULL, state TEXT NOT NULL,
                    reserved REAL NOT NULL, actual REAL NOT NULL DEFAULT 0,
                    input_tokens INTEGER NOT NULL DEFAULT 0, output_tokens INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL);
            """)
            # A restarted process cannot know whether an in-flight request was billed.
            db.execute("UPDATE calls SET state='uncertain' WHERE state='in_flight'")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def snapshot(self, db=None):
        if db is None:
            with self.connect() as db:
                return self.snapshot(db)
        row = db.execute("SELECT COALESCE(SUM(actual),0),COALESCE(SUM(reserved),0),"
                         "SUM(CASE WHEN state='uncertain' THEN 1 ELSE 0 END) FROM calls").fetchone()
        spent, reserved = float(row[0]), float(row[1])
        return {"limit_usd":self.limit,"spent_usd":round(spent,8),"reserved_usd":round(reserved,8),
                "remaining_usd":round(max(0,self.limit-spent-reserved),8),"uncertain_calls":row[2] or 0}

    def reserve(self, session_id, model, stage, maximum):
        if not math.isfinite(maximum) or maximum <= 0:
            raise ProviderCallRejected()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if maximum > self.snapshot(db)["remaining_usd"]:
                raise ProviderCallRejected("operator_cutoff")
            call_id = uuid.uuid4().hex
            db.execute("INSERT INTO calls(id,session_id,model,stage,state,reserved,created_at) VALUES(?,?,?,?,?,?,?)",
                       (call_id,session_id,model,stage,"in_flight",maximum,datetime.now(timezone.utc).isoformat()))
        return call_id

    def finish(self, call_id, usage=None, pricing=None, rejected=False):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT state,reserved FROM calls WHERE id=?",(call_id,)).fetchone()
            if not row or row["state"] != "in_flight":
                return
            if usage is not None:
                actual = cost(usage,pricing)
                # Keep any charge over the conservative bound visible, never discard it.
                db.execute("UPDATE calls SET state='completed',reserved=0,actual=?,input_tokens=?,output_tokens=? WHERE id=?",
                           (actual,usage.input_tokens,usage.output_tokens,call_id))
            elif rejected:
                db.execute("UPDATE calls SET state='rejected',reserved=0 WHERE id=?",(call_id,))
            else:
                db.execute("UPDATE calls SET state='uncertain' WHERE id=?",(call_id,))


class MeteredProvider:
    """Global account boundary; visitor deletion cannot erase its aggregate bill."""
    def __init__(self, provider, ledger: DemoLedger, session_id: str):
        self.provider, self.ledger, self.session_id = provider, ledger, session_id
        self.name, self.model, self.pricing = provider.name, provider.model, provider.pricing

    @property
    def key_configured(self):
        return self.provider.key_configured

    def _call(self, stage, payload):
        if not self.key_configured:
            raise ProviderCallRejected("not_configured")
        # Wait briefly for a legitimate concurrent judge; never build an unlimited queue.
        if not self.ledger.slots.acquire(timeout=20):
            raise ProviderCallRejected("queue_busy")
        call_id = None
        try:
            input_tokens = generation_input_bound(payload) if stage == "generation" else verification_input_bound(payload)
            maximum = cost(UsageCounts(input_tokens,MAX_GENERATION_TOKENS if stage == "generation" else MAX_VERIFICATION_TOKENS),self.pricing)
            call_id = self.ledger.reserve(self.session_id,self.model,stage,maximum)
            method = self.provider.generate if stage == "generation" else self.provider.verify
            try:
                result, usage = method(payload)
            except Exception as exc:
                self.ledger.finish(call_id,getattr(exc,"usage",None),self.pricing,isinstance(exc,ProviderCallRejected))
                raise
            self.ledger.finish(call_id,usage,self.pricing)
            return result, usage
        finally:
            self.ledger.slots.release()

    def generate(self, payload):
        return self._call("generation",payload)

    def verify(self, payload):
        return self._call("verification",payload)
