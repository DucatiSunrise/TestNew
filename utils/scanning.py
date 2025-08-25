# utils/scanning.py
import json
import re
from typing import Dict, Optional

# Normalizers (tweak if you want)
def _norm_phone(p: str) -> str:
    digits = re.sub(r"\D", "", p or "")
    return digits  # store digits-only; format in UI if desired

def _is_json(s: str) -> bool:
    s = (s or "").strip()
    return s.startswith("{") and s.endswith("}")

def parse_scan_payload(raw: str) -> Dict[str, Optional[str]]:
    """
    Accepts:
      - JSON (QR): {"wo":"WO-1042","cf":"Mike","cl":"McClure","dt":"Laptop","dm":"Dell","cp":"555-...","ce":"x@y.com"}
      - Pipe-delimited: WO-1042|Mike|McClure|Laptop|Dell|555-...|x@y.com
      - Simple prefixes: WO-1042  or  CUST-12345
    Returns a dict with keys:
      wo (work order code/number), cf, cl, dt, dm, cp (phone digits), ce (email)
      kind: "work_order" | "customer" | "payload"
    """
    out = {"wo": None, "cf": None, "cl": None, "dt": None, "dm": None, "cp": None, "ce": None, "kind": None}
    s = (raw or "").strip()

    # Prefix routing first (fast)
    if s.upper().startswith("WO-"):
        out["wo"] = s
        out["kind"] = "work_order"
        return out
    if s.upper().startswith("CUST-"):
        # treat as a customer barcode value; caller can look it up
        out["kind"] = "customer"
        # put raw in cf/cl if you want; better to return a marker and let caller query DB by barcode
        return out

    # JSON payload
    if _is_json(s):
        try:
            obj = json.loads(s)
            out["wo"] = obj.get("wo")
            out["cf"] = obj.get("cf")
            out["cl"] = obj.get("cl")
            out["dt"] = obj.get("dt")
            out["dm"] = obj.get("dm")
            out["cp"] = _norm_phone(obj.get("cp") or "")
            out["ce"] = (obj.get("ce") or "").strip() or None
            out["kind"] = "payload"
            return out
        except Exception:
            pass

    # Pipe-delimited fallback
    parts = s.split("|")
    if len(parts) >= 5:
        # WO|First|Last|DevType|Mfr|[Phone]|[Email]
        out["wo"] = parts[0].strip() or None
        out["cf"] = parts[1].strip() or None
        out["cl"] = parts[2].strip() or None
        out["dt"] = parts[3].strip() or None
        out["dm"] = parts[4].strip() or None
        out["cp"] = _norm_phone(parts[5]) if len(parts) > 5 else None
        out["ce"] = (parts[6].strip() if len(parts) > 6 else "") or None
        out["kind"] = "payload"
        return out

    # Unknown; return raw wo guess if it looks like WO-1234 without prefix
    m = re.match(r"^(WO[-\s]?\w+)$", s, re.I)
    if m:
        out["wo"] = m.group(1)
        out["kind"] = "work_order"
        return out

    return out
