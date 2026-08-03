import sqlite3
from flask import Flask, render_template, request, session, jsonify, g

app = Flask(__name__)
app.secret_key = "ayurveda_secret_key_2024"
DB_PATH = "ayurveda.db"


# ── DB helpers ────────────────────────────────────────────────────────────────

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db:
        db.close()


def query(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv


# ── Build full condition dict ─────────────────────────────────────────────────

def build_condition(row):
    cid = row["id"]
    symptoms          = [r["symptom"]  for r in query("SELECT symptom  FROM symptoms         WHERE condition_id=?", (cid,))]
    remedies          = [r["remedy"]   for r in query("SELECT remedy   FROM remedies          WHERE condition_id=?", (cid,))]
    medicines         = [r["medicine"] for r in query("SELECT medicine FROM medicines         WHERE condition_id=?", (cid,))]
    contraindications = [r["note"]     for r in query("SELECT note     FROM contraindications WHERE condition_id=?", (cid,))]
    return {
        "id":                 cid,
        "condition":          row["name"],
        "dosha":              row["dosha"],
        "body_system":        row["body_system"],
        "chronic_acute":      row["chronic_acute"],
        "seasonal":           row["seasonal"],
        "symptoms":           symptoms,
        "remedies":           remedies,
        "medicines":          medicines,
        "contraindications":  contraindications,
    }


# ── Matching engine ───────────────────────────────────────────────────────────

def predict(user_symptoms):
    all_conditions = query("SELECT * FROM conditions")
    scores = {}

    for cond in all_conditions:
        cid = cond["id"]
        db_symptoms = [r["symptom"] for r in
                       query("SELECT symptom FROM symptoms WHERE condition_id=?", (cid,))]

        score = 0
        matched = []
        for user_sym in user_symptoms:
            user_sym = user_sym.strip().lower()
            if not user_sym:
                continue
            for db_sym in db_symptoms:
                if user_sym == db_sym:
                    score += 3
                    if db_sym not in matched:
                        matched.append(db_sym)
                    break
                elif user_sym in db_sym or db_sym in user_sym:
                    score += 1
                    if db_sym not in matched:
                        matched.append(db_sym)
                    break

        if score > 0:
            scores[cond["id"]] = {
                "row":              cond,
                "score":            score,
                "matched_symptoms": matched,
            }

    if not scores:
        return None, []

    ranked = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
    results = []
    for cid, info in ranked[:3]:
        c = build_condition(info["row"])
        c["matched_symptoms"] = info["matched_symptoms"]
        c["match_score"]      = info["score"]
        results.append(c)

    return results[0]["condition"], results


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    popular = [
        "fever", "headache", "cough", "bloating", "anxiety",
        "joint pain", "skin rash", "indigestion", "fatigue", "dizziness"
    ]
    all_symptoms = [r["symptom"] for r in
                    query("SELECT DISTINCT symptom FROM symptoms ORDER BY symptom")]
    return render_template("index.html",
                           popular_symptoms=popular,
                           all_symptoms=all_symptoms)


@app.route("/predict", methods=["POST"])
def result():
    raw      = request.form.get("symptoms", "")
    symptoms = [s.strip() for s in raw.lower().split(",") if s.strip()]

    all_symptoms = [r["symptom"] for r in
                    query("SELECT DISTINCT symptom FROM symptoms ORDER BY symptom")]

    if not symptoms:
        return render_template("index.html",
                               popular_symptoms=["fever", "headache", "cough",
                                                 "bloating", "anxiety"],
                               all_symptoms=all_symptoms,
                               error="Please enter at least one symptom.")

    condition, results = predict(symptoms)

    if not results:
        return render_template("result.html",
                               no_match=True,
                               user_symptoms=symptoms,
                               results=[],
                               all_symptoms=all_symptoms)

    if "history" not in session:
        session["history"] = []
    history = session["history"]
    history.insert(0, {
        "symptoms":    symptoms,
        "condition":   condition,
        "body_system": results[0]["body_system"],
    })
    session["history"] = history[:10]

    return render_template("result.html",
                           user_symptoms=symptoms,
                           results=results,
                           no_match=False,
                           all_symptoms=all_symptoms)


@app.route("/dashboard")
def dashboard():
    total_conditions = query("SELECT COUNT(*) AS c FROM conditions", one=True)["c"]
    total_symptoms   = query("SELECT COUNT(DISTINCT symptom) AS c FROM symptoms", one=True)["c"]
    total_remedies   = query("SELECT COUNT(*) AS c FROM remedies", one=True)["c"]

    systems = query("SELECT DISTINCT body_system FROM conditions ORDER BY body_system")
    by_system = {}
    for s in systems:
        sys_name = s["body_system"]
        rows = query("""
            SELECT c.name, c.dosha,
                   COUNT(DISTINCT sym.symptom) AS symptoms_count
            FROM   conditions c
            LEFT JOIN symptoms sym ON sym.condition_id = c.id
            WHERE  c.body_system = ?
            GROUP  BY c.id
        """, (sys_name,))
        by_system[sys_name] = [
            {"name": r["name"], "dosha": r["dosha"],
             "symptoms_count": r["symptoms_count"]}
            for r in rows
        ]

    dosha_rows = query("""
        SELECT dosha, COUNT(*) AS cnt
        FROM   conditions
        GROUP  BY dosha
        ORDER  BY cnt DESC
    """)
    dosha_count = {r["dosha"]: r["cnt"] for r in dosha_rows}

    max_system_count = max((len(v) for v in by_system.values()), default=1)
    max_dosha_count  = max(dosha_count.values(), default=1)

    history = session.get("history", [])

    return render_template("dashboard.html",
                           total_conditions=total_conditions,
                           total_symptoms=total_symptoms,
                           total_remedies=total_remedies,
                           by_system=by_system,
                           dosha_count=dosha_count,
                           max_system_count=max_system_count,
                           max_dosha_count=max_dosha_count,
                           history=history,
                           all_symptoms=[])


@app.route("/autocomplete")
def autocomplete():
    q = request.args.get("q", "").lower()
    if len(q) < 2:
        return jsonify([])
    rows = query(
        "SELECT DISTINCT symptom FROM symptoms WHERE symptom LIKE ? LIMIT 10",
        (f"%{q}%",)
    )
    return jsonify([r["symptom"] for r in rows])


@app.route("/clear-history")
def clear_history():
    session.pop("history", None)
    return ("", 204)


if __name__ == "__main__":
    app.run(debug=True)