import json


READING_SELECT = """SELECT r.id, r.session_id, s.code, s.band, r.reference, r.hvac,
                    r.position, CAST(r.noise AS DOUBLE) AS noise, r.traffic, r.note
                    FROM readings r JOIN sessions s ON s.id=r.session_id"""
METHOD_COLUMNS = 'id, version, title, predictor, controls, note'
RUN_COLUMNS = """d.id, d.title, d.method_id, m.version, m.predictor, d.state, d.fingerprint,
                 d.result, d.decision, d.created_at, d.finished_at, d.reviewed_at,
                 a.email AS owner, reviewer.email AS reviewer"""
RUN_FROM = """FROM diagnostics d JOIN methods m ON d.method_id=m.id
              JOIN accounts a ON d.owner_id=a.id LEFT JOIN accounts reviewer ON d.reviewer_id=reviewer.id"""


def decode_json(row, *keys):
    if row is not None:
        for key in keys:
            if row[key] is not None:
                row[key] = json.loads(row[key])
    return row


def audit(cursor, actor, action, subject):
    cursor.execute('INSERT INTO audit(actor_id, action, subject) VALUES (%s,%s,%s)', (actor, action, subject))
