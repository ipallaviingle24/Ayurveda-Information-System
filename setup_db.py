"""
Run this ONCE to build ayurveda.db from your CSV.
    python setup_db.py
"""

import sqlite3
import csv
from collections import defaultdict
import os

DB_PATH = "ayurveda.db"
CSV_PATH = "ayurveda_dataset.csv"

# ── 1. Delete old DB if exists ──────────────────────────────────────────────
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"Removed old {DB_PATH}")

# ── 2. Create DB & tables ────────────────────────────────────────────────────
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.executescript("""
    CREATE TABLE conditions (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        name          TEXT    NOT NULL UNIQUE,
        dosha         TEXT,
        body_system   TEXT,
        chronic_acute TEXT,
        seasonal      TEXT
    );

    CREATE TABLE symptoms (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        condition_id INTEGER NOT NULL REFERENCES conditions(id),
        symptom      TEXT    NOT NULL
    );

    CREATE TABLE remedies (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        condition_id INTEGER NOT NULL REFERENCES conditions(id),
        remedy       TEXT    NOT NULL
    );

    CREATE TABLE medicines (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        condition_id INTEGER NOT NULL REFERENCES conditions(id),
        medicine     TEXT    NOT NULL
    );

    CREATE TABLE contraindications (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        condition_id INTEGER NOT NULL REFERENCES conditions(id),
        note         TEXT    NOT NULL
    );

    -- Fast lookup index
    CREATE INDEX idx_symptoms_symptom ON symptoms(symptom);
    CREATE INDEX idx_symptoms_cid     ON symptoms(condition_id);
""")

conn.commit()
print("Tables created.")

# ── 3. Read & group CSV ───────────────────────────────────────────────────────
grouped = defaultdict(lambda: {
    "symptoms": set(), "remedies": set(), "medicines": set(),
    "dosha": set(), "body_system": set(),
    "contraindications": set(), "seasonal": set(), "chronic_acute": set()
})

with open(CSV_PATH, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        base = row["Problem"].split(" - ")[0].strip()
        for s in row["Symptoms"].split(";"):
            if s.strip(): grouped[base]["symptoms"].add(s.strip().lower())
        for r in row["Remedies"].split(";"):
            if r.strip(): grouped[base]["remedies"].add(r.strip())
        for m in row["Medicines"].split(","):
            if m.strip(): grouped[base]["medicines"].add(m.strip())
        grouped[base]["dosha"].add(row["Dosha Type"].strip())
        grouped[base]["body_system"].add(row["Body System"].strip())
        if row["Contraindications"].strip():
            grouped[base]["contraindications"].add(row["Contraindications"].strip())
        grouped[base]["seasonal"].add(row["Seasonal Suitability"].strip())
        grouped[base]["chronic_acute"].add(row["Chronic/Acute"].strip())

print(f"CSV grouped into {len(grouped)} conditions.")

# ── 4. Insert into DB ─────────────────────────────────────────────────────────
for condition_name, info in grouped.items():
    dosha         = ", ".join(info["dosha"])
    body_system   = list(info["body_system"])[0]  if info["body_system"]   else "General"
    chronic_acute = list(info["chronic_acute"])[0] if info["chronic_acute"] else "Acute"
    seasonal      = list(info["seasonal"])[0]      if info["seasonal"]      else "All seasons"

    cur.execute(
        "INSERT INTO conditions (name, dosha, body_system, chronic_acute, seasonal) VALUES (?,?,?,?,?)",
        (condition_name, dosha, body_system, chronic_acute, seasonal)
    )
    cid = cur.lastrowid

    cur.executemany("INSERT INTO symptoms (condition_id, symptom) VALUES (?,?)",
                    [(cid, s) for s in info["symptoms"]])

    cur.executemany("INSERT INTO remedies (condition_id, remedy) VALUES (?,?)",
                    [(cid, r) for r in list(info["remedies"])[:8]])   # top 8

    cur.executemany("INSERT INTO medicines (condition_id, medicine) VALUES (?,?)",
                    [(cid, m) for m in list(info["medicines"])[:6]])  # top 6

    cur.executemany("INSERT INTO contraindications (condition_id, note) VALUES (?,?)",
                    [(cid, c) for c in list(info["contraindications"])[:3]])

conn.commit()

# ── 5. Summary ────────────────────────────────────────────────────────────────
cur.execute("SELECT COUNT(*) FROM conditions")
print(f"  conditions   : {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM symptoms")
print(f"  symptoms     : {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM remedies")
print(f"  remedies     : {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM medicines")
print(f"  medicines    : {cur.fetchone()[0]}")

conn.close()
print(f"\n✅ Database ready → {DB_PATH}")
print("Now run:  python app.py")