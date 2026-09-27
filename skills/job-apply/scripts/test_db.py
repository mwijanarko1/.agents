#!/usr/bin/env python3
import sqlite3
import tempfile
import unittest
from pathlib import Path

import db


class ApplicationTests(unittest.TestCase):
    def test_reapplying_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "jobs.sqlite3"
            jsonl_path = Path(tmp) / "outcomes.jsonl"
            conn = db.connect(db_path)
            ts = db.now()
            job_id = conn.execute(
                """INSERT INTO jobs
                   (fingerprint, title, company, url, first_seen_at, last_seen_at, status)
                   VALUES ('roleacme', 'Role', 'Acme', '', ?, ?, 'tailored')""",
                (ts, ts),
            ).lastrowid
            conn.commit()
            conn.close()

            db.upsert_application(
                job_id=job_id,
                status="applied",
                applied=True,
                channel="email",
                db_path=db_path,
                jsonl_path=jsonl_path,
            )
            conn = sqlite3.connect(db_path)
            first_applied_at = conn.execute(
                "SELECT applied_at FROM applications WHERE job_id=?", (job_id,)
            ).fetchone()[0]
            conn.close()

            db.upsert_application(
                job_id=job_id,
                status="applied",
                applied=True,
                channel="email",
                db_path=db_path,
                jsonl_path=jsonl_path,
            )

            conn = sqlite3.connect(db_path)
            applied_at = conn.execute(
                "SELECT applied_at FROM applications WHERE job_id=?", (job_id,)
            ).fetchone()[0]
            sent_count = conn.execute(
                "SELECT count(*) FROM outcomes WHERE job_id=? AND outcome='sent'", (job_id,)
            ).fetchone()[0]
            conn.close()

            self.assertEqual(applied_at, first_applied_at)
            self.assertEqual(sent_count, 1)
            self.assertEqual(len(jsonl_path.read_text().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
