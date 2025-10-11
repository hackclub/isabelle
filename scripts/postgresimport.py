import os, csv, uuid
from typing import Optional, List
import psycopg
from datetime import datetime

CSV_PATH = "../ignore/Events-All.csv"
TABLE = '"event"'

TRUE = {"true","t","yes","y","1","on"}
FALSE = {"false","f","no","n","0","off"}

def empty_to_none(s: Optional[str]) -> Optional[str]:
    if s is None: return None
    s = s.strip()
    return s if s else None

def parse_bool(s: Optional[str]) -> Optional[bool]:
    v = empty_to_none(s)
    if v is None: return False
    v = v.lower()
    if v in TRUE: return True
    if v in FALSE: return False
    return True

def parse_smallint(s: Optional[str]) -> Optional[int]:
    v = empty_to_none(s)
    return int(v) if v is not None else 0

def parse_array_text(s: Optional[str]) -> Optional[List[str]]:

    v = empty_to_none(s)
    if v is None: return None
    if v.startswith("[") and v.endswith("]"):
        try:
            import json
            arr = json.loads(v)
            if isinstance(arr, list):
                return [str(x).strip() for x in arr if str(x).strip()]
        except Exception:
            pass
    return [p.strip() for p in v.split(",") if p.strip()] or None

def normalize_ts_for_key(s: Optional[str]) -> str:
    v = empty_to_none(s)
    if not v: return ""
    w = v
    if w.endswith("Z"):
        w = w[:-1] + "+0000"
    if len(w) > 6 and (w[-6] in ["+","-"]) and w[-3] == ":":
        w = w[:-3] + w[-2:]
    fmts = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in fmts:
        try:
            return datetime.strptime(w, fmt).isoformat()
        except ValueError:
            continue
    return v  # fallback raw

cols = [
    "id","Title","Description","StartTime","EndTime","LeaderSlackID","Leader","Avatar",
    "Approved","EventLink","Cancelled","YouTubeURL","Emoji","HasHappened","AMA","AMAName",
    "AMACompany","AMATitle","AMALink","AMAAvatar","CalendarLink","Photos","Calculation",
    "Month","Sent1DayReminder","Sent1HourReminder","SentStartingReminder","RawDescription",
    "RawCancellation","InterestCount","rsvpMsg",
]

parsers = {
    "id": empty_to_none,                 # will auto-fill if missing
    "Title": empty_to_none,
    "Description": empty_to_none,
    "StartTime": empty_to_none,          # Postgres casts
    "EndTime": empty_to_none,
    "LeaderSlackID": empty_to_none,
    "Leader": empty_to_none,
    "Avatar": empty_to_none,
    "Approved": parse_bool,
    "EventLink": empty_to_none,
    "Cancelled": parse_bool,
    "YouTubeURL": empty_to_none,
    "Emoji": empty_to_none,
    "HasHappened": parse_bool,
    "AMA": parse_bool,
    "AMAName": empty_to_none,
    "AMACompany": empty_to_none,
    "AMATitle": empty_to_none,
    "AMALink": empty_to_none,
    "AMAAvatar": empty_to_none,
    "CalendarLink": empty_to_none,
    "Photos": empty_to_none,
    "Calculation": empty_to_none,
    "Month": parse_smallint,
    "Sent1DayReminder": parse_bool,
    "Sent1HourReminder": parse_bool,
    "SentStartingReminder": parse_bool,
    "RawDescription": empty_to_none,
    "RawCancellation": empty_to_none,
    "InterestCount": parse_smallint,
    "rsvpMsg": empty_to_none,
}

NAMESPACE = uuid.NAMESPACE_URL

def make_uuid(row: dict) -> str:
    """
    Create a stable UUIDv5 when possible:
      1) Calculation
      2) Title + normalized StartTime
      3) Title + Month
      else random UUID4
    """
    calc = empty_to_none(row.get("Calculation"))
    if calc:
        return str(uuid.uuid5(NAMESPACE, f"event:{calc}"))
    title = empty_to_none(row.get("Title")) or ""
    start_norm = normalize_ts_for_key(row.get("StartTime"))
    if title and start_norm:
        return str(uuid.uuid5(NAMESPACE, f"event:{title}|{start_norm}"))
    month = empty_to_none(row.get("Month"))
    if title and month:
        return str(uuid.uuid5(NAMESPACE, f"event:{title}|m={month}"))
    return str(uuid.uuid4())

def main():
    dsn = os.environ.get("DATABASE_URL") or "postgresql://postgres:postgres@localhost:5432/isabelle"
    if not dsn:
        raise SystemExit("Set DATABASE_URL, e.g. postgresql://user:pass@host:5432/db")

    quoted_cols = [f'"{c}"' for c in cols]
    placeholders = ", ".join([f"%({c})s" for c in cols])
    set_clause = ", ".join([f'{q} = EXCLUDED."{c}"' for q, c in zip(quoted_cols, cols) if c != "id"])

    sql = f"""
    INSERT INTO {TABLE} ({", ".join(quoted_cols)})
    VALUES ({placeholders})
    ON CONFLICT ("id") DO UPDATE SET
      {set_clause};
    """

    with psycopg.connect(dsn) as conn, conn.cursor() as cur, open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        if "id" not in (reader.fieldnames or []):
            print("CSV has no 'id' column; generating UUIDs.")
        # Explicitly ignore InterestedUsers even if present
        if "InterestedUsers" in (reader.fieldnames or []):
            print("Skipping 'InterestedUsers' column as requested.")

        batch = []
        for i, row in enumerate(reader, start=1):
            rec = {}
            for c in cols:
                raw = row.get(c)
                rec[c] = parsers.get(c, empty_to_none)(raw)
            if not rec.get("id"):
                rec["id"] = make_uuid(row)
            if not rec.get("Title"):
                rec["Title"] = "unknown"
            if not rec.get("Cancelled"):
                rec["Cancelled"] = False

            batch.append(rec)
            if len(batch) >= 500:
                cur.executemany(sql, batch); batch.clear()

        if batch:
            cur.executemany(sql, batch)

        conn.commit()
        print("Done.")

if __name__ == "__main__":
    main()
