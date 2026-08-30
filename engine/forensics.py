"""
AuditDesk Forensic Analytics Engine
Deterministic anomaly detection for internal audit fieldwork:
- Split transactions / DOA threshold structuring
- Fuzzy duplicate payments
- Benford's Law leading digit analysis
- Non-business hours and weekend posting analysis
"""

import math
from datetime import datetime
from collections import Counter
from typing import List, Dict, Any, Tuple, Optional


def calculate_levenshtein(s1: str, s2: str) -> int:
    """Computes Levenshtein edit distance between two strings."""
    s1, s2 = str(s1).strip().lower(), str(s2).strip().lower()
    if s1 == s2:
        return 0
    if len(s1) == 0:
        return len(s2)
    if len(s2) == 0:
        return len(s1)

    v0 = list(range(len(s2) + 1))
    v1 = [0] * (len(s2) + 1)

    for i in range(len(s1)):
        v1[0] = i + 1
        for j in range(len(s2)):
            cost = 0 if s1[i] == s2[j] else 1
            v1[j + 1] = min(v1[j] + 1, v0[j + 1] + 1, v0[j] + cost)
        v0 = v1[:]

    return v1[len(s2)]


def string_similarity(s1: str, s2: str, min_threshold: float = 0.85) -> float:
    """Returns normalized similarity between 0.0 and 1.0 with early exit optimization."""
    if s1 == s2:
        return 1.0
    s1_clean, s2_clean = str(s1).strip().lower(), str(s2).strip().lower()
    if s1_clean == s2_clean:
        return 1.0
    if not s1_clean or not s2_clean:
        return 0.0
    max_len = max(len(s1_clean), len(s2_clean))
    len_diff = abs(len(s1_clean) - len(s2_clean))
    if (len_diff / max_len) > (1.0 - min_threshold):
        return 0.0
    dist = calculate_levenshtein(s1_clean, s2_clean)
    return 1.0 - (dist / max_len)


def clean_amount(val: Any) -> float:
    """Safely converts dirty currency strings, floats, accounting brackets to float."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val) if not (math.isnan(val) or math.isinf(val)) else 0.0
    s = str(val).strip().replace("$", "").replace("€", "").replace("£", "").replace("¥", "").replace(" ", "").replace(",", "")
    if s.startswith("(") and s.endswith(")"):
        s = "-" + s[1:-1]
    try:
        return float(s)
    except Exception:
        return 0.0


def parse_date_fast(raw: str) -> Optional[datetime]:
    """High-speed date parsing for large enterprise populations."""
    if not raw:
        return None
    s = str(raw).strip()
    # YYYY-MM-DD format (standard ISO)
    if len(s) >= 10 and s[4] == '-' and s[7] == '-':
        try:
            return datetime(int(s[0:4]), int(s[5:7]), int(s[8:10]))
        except ValueError:
            pass
        except Exception:
            pass

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d", "%d-%m-%Y", "%b %d %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(s.split("T")[0].split(" ")[0], fmt)
        except Exception:
            continue
    return None


class ForensicEngine:
    @staticmethod
    def detect_split_transactions(
        records: List[Dict[str, Any]],
        threshold: float = 5000.0,
        buffer_pct: float = 0.15,
        vendor_field: str = "vendor",
        amount_field: str = "amount",
        date_field: str = "date",
        window_days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Detects transactions grouped by vendor within a time window that fall
        just below the approval threshold (e.g. $4,250 to $4,999.99 for a $5,000 threshold),
        or where multiple items collectively exceed the threshold.
        """
        lower_bound = threshold * (1.0 - buffer_pct)
        upper_bound = threshold - 0.01

        flagged_items = []
        vendor_groups: Dict[str, List[Dict[str, Any]]] = {}

        for rec in records:
            v = str(rec.get(vendor_field, "UNKNOWN")).strip().upper()
            if not v or v == "NONE":
                v = "UNKNOWN"
            if v not in vendor_groups:
                vendor_groups[v] = []
            vendor_groups[v].append(rec)

        for vendor, items in vendor_groups.items():
            # Check individual items in proximity band
            proximity_items = []
            for item in items:
                amt = clean_amount(item.get(amount_field, 0.0))
                if lower_bound <= amt <= upper_bound:
                    proximity_items.append(item)

            if len(proximity_items) >= 2 or (len(proximity_items) >= 1 and len(items) >= 2):
                for item in proximity_items:
                    amt = clean_amount(item.get(amount_field, 0.0))
                    flagged_items.append({
                        "id": item.get("id", item.get("invoice_no", str(id(item)))),
                        "vendor": vendor,
                        "amount": amt,
                        "date": str(item.get(date_field, "")),
                        "invoice_no": str(item.get("invoice_no", "")),
                        "description": str(item.get("description", "")),
                        "reason": f"Split Risk: Amount ${amt:,.2f} is within {buffer_pct*100:.0f}% below the ${threshold:,.2f} DOA authorization threshold for {vendor}.",
                        "severity": "High" if amt >= (threshold * 0.95) else "Medium",
                        "raw": item
                    })

        return flagged_items

    @staticmethod
    def detect_duplicate_payments(
        records: List[Dict[str, Any]],
        vendor_field: str = "vendor",
        amount_field: str = "amount",
        invoice_field: str = "invoice_no",
        date_field: str = "date"
    ) -> List[Dict[str, Any]]:
        """
        Detects exact and fuzzy duplicate payments using O(N) amount and vendor hash buckets.
        """
        duplicates = []
        amount_buckets: Dict[float, List[Dict[str, Any]]] = {}

        # 1. Bucket by exact rounded amount
        for rec in records:
            amt = round(clean_amount(rec.get(amount_field, 0.0)), 2)
            if amt <= 0.0:
                continue
            if amt not in amount_buckets:
                amount_buckets[amt] = []
            amount_buckets[amt].append(rec)

        # 2. Compare within same amount buckets
        for amt, bucket in amount_buckets.items():
            if len(bucket) < 2:
                continue

            # Group by exact vendor upper first (eliminates string comparisons)
            by_vendor: Dict[str, List[Dict[str, Any]]] = {}
            for item in bucket:
                vu = str(item.get(vendor_field, "")).strip().upper()
                if vu not in by_vendor:
                    by_vendor[vu] = []
                by_vendor[vu].append(item)

            # A. Exact vendor duplicates
            for vu, v_items in by_vendor.items():
                if len(v_items) >= 2:
                    for i in range(len(v_items) - 1):
                        r1 = v_items[i]
                        r2 = v_items[i + 1]
                        inv1 = str(r1.get(invoice_field, "")).strip()
                        inv2 = str(r2.get(invoice_field, "")).strip()
                        match_type = "Exact Duplicate" if (inv1 and inv1.upper() == inv2.upper()) else "Duplicate Payment"
                        duplicates.append({
                            "item_1": {
                                "id": r1.get("id", inv1),
                                "vendor": r1.get(vendor_field, ""),
                                "amount": amt,
                                "date": str(r1.get(date_field, "")),
                                "invoice_no": inv1
                            },
                            "item_2": {
                                "id": r2.get("id", inv2),
                                "vendor": r2.get(vendor_field, ""),
                                "amount": amt,
                                "date": str(r2.get(date_field, "")),
                                "invoice_no": inv2
                            },
                            "match_type": match_type,
                            "vendor_similarity": 100.0,
                            "invoice_similarity": 100.0 if (inv1 and inv1.upper() == inv2.upper()) else 50.0,
                            "severity": "High" if match_type == "Exact Duplicate" else "Medium",
                            "reason": f"{match_type} detected for ${amt:,.2f} on vendor '{r1.get(vendor_field, '')}' ({inv1} vs {inv2})."
                        })

            # B. Fuzzy vendor duplicates across different vendor names
            distinct_vendors = list(by_vendor.keys())
            v_len = len(distinct_vendors)
            if 2 <= v_len <= 15:
                for i in range(v_len):
                    for j in range(i + 1, v_len):
                        v1 = distinct_vendors[i]
                        v2 = distinct_vendors[j]
                        if abs(len(v1) - len(v2)) > 3 or (v1 and v2 and v1[0] != v2[0]):
                            continue
                        v_sim = string_similarity(v1, v2)
                        if v_sim >= 0.85:
                            r1 = by_vendor[v1][0]
                            r2 = by_vendor[v2][0]
                            inv1 = str(r1.get(invoice_field, "")).strip()
                            inv2 = str(r2.get(invoice_field, "")).strip()
                            duplicates.append({
                                "item_1": {"id": r1.get("id", inv1), "vendor": r1.get(vendor_field, ""), "amount": amt, "date": str(r1.get(date_field, "")), "invoice_no": inv1},
                                "item_2": {"id": r2.get("id", inv2), "vendor": r2.get(vendor_field, ""), "amount": amt, "date": str(r2.get(date_field, "")), "invoice_no": inv2},
                                "match_type": "Fuzzy Duplicate",
                                "vendor_similarity": round(v_sim * 100, 1),
                                "invoice_similarity": 50.0,
                                "severity": "Medium",
                                "reason": f"Fuzzy Duplicate detected for ${amt:,.2f} between '{r1.get(vendor_field, '')}' and '{r2.get(vendor_field, '')}'."
                            })

        return duplicates

    @staticmethod
    def calculate_benfords_law(
        records: List[Dict[str, Any]],
        amount_field: str = "amount"
    ) -> Dict[str, Any]:
        """
        Evaluates first-digit distribution against Benford's Law:
        P(d) = log10(1 + 1/d)
        """
        benford_expected = {
            1: 0.301, 2: 0.176, 3: 0.125,
            4: 0.097, 5: 0.079, 6: 0.067,
            7: 0.058, 8: 0.051, 9: 0.046
        }

        first_digits = []
        for rec in records:
            amt = abs(clean_amount(rec.get(amount_field, 0.0)))
            if amt >= 10.0:
                s = f"{amt:.2f}".lstrip("0").replace(".", "")
                if s:
                    d = int(s[0])
                    if 1 <= d <= 9:
                        first_digits.append(d)

        total_count = len(first_digits)
        if total_count < 20:
            return {
                "status": "insufficient_data",
                "message": f"Only {total_count} valid records found. Benford's Law analysis requires at least 20 items.",
                "total_analyzed": total_count,
                "digits": []
            }

        counts = Counter(first_digits)
        digit_analysis = []
        chi_square_stat = 0.0

        for d in range(1, 10):
            observed_cnt = counts.get(d, 0)
            observed_pct = observed_cnt / total_count
            expected_pct = benford_expected[d]
            expected_cnt = expected_pct * total_count

            sd = math.sqrt(expected_pct * (1 - expected_pct) / total_count)
            z_score = (observed_pct - expected_pct) / sd if sd > 0 else 0.0

            chi_sq_component = ((observed_cnt - expected_cnt) ** 2) / expected_cnt if expected_cnt > 0 else 0.0
            chi_square_stat += chi_sq_component

            is_anomaly = abs(z_score) > 2.58

            digit_analysis.append({
                "digit": d,
                "observed_count": observed_cnt,
                "observed_pct": round(observed_pct * 100, 2),
                "expected_pct": round(expected_pct * 100, 2),
                "variance_pct": round((observed_pct - expected_pct) * 100, 2),
                "z_score": round(z_score, 2),
                "is_anomaly": is_anomaly
            })

        conformity = "High Conformity" if chi_square_stat < 15.51 else ("Marginal Non-Conformity" if chi_square_stat < 20.09 else "Severe Non-Conformity (High Risk of Manipulation)")

        return {
            "status": "success",
            "total_analyzed": total_count,
            "chi_square": round(chi_square_stat, 2),
            "conformity": conformity,
            "digits": digit_analysis
        }

    @staticmethod
    def detect_out_of_hours(
        records: List[Dict[str, Any]],
        date_field: str = "date",
        amount_field: str = "amount"
    ) -> List[Dict[str, Any]]:
        """
        Flags entries posted on weekends (Saturday/Sunday) using high-speed date parsing.
        """
        out_of_hours = []

        for rec in records:
            raw_date = str(rec.get(date_field, "")).strip()
            if not raw_date:
                continue

            parsed_dt = parse_date_fast(raw_date)

            if parsed_dt:
                weekday_num = parsed_dt.weekday()
                if weekday_num in (5, 6):
                    day_name = "Saturday" if weekday_num == 5 else "Sunday"
                    amt = clean_amount(rec.get(amount_field, 0.0))
                    out_of_hours.append({
                        "id": rec.get("id", rec.get("invoice_no", "")),
                        "date": raw_date,
                        "day": day_name,
                        "amount": amt,
                        "vendor": rec.get("vendor", rec.get("account", "N/A")),
                        "description": rec.get("description", ""),
                        "reason": f"Weekend Posting: Transaction recorded on {day_name} ({raw_date}).",
                        "severity": "Medium" if amt < 10000 else "High",
                        "raw": rec
                    })

        return out_of_hours
