"""
Integration Test for AuditDesk HTTP Server Endpoints
Starts an in-process local server and queries every single REST endpoint with proxy bypass.
"""

import os
import sys
import json
import urllib.request
import threading
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from server import HTTPServer, AuditDeskHandler, load_demo_data

TEST_PORT = 8099
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"

# Create opener bypassing any local environment proxies
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def run_test_server():
    load_demo_data()
    server = HTTPServer(("127.0.0.1", TEST_PORT), AuditDeskHandler)
    server.serve_forever()


def http_get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}", headers={"User-Agent": "Mozilla/5.0"})
    with OPENER.open(req, timeout=5) as resp:
        return resp.read().decode("utf-8")


def http_post(path, payload):
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data_bytes,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    )
    with OPENER.open(req, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_endpoints():
    print("[INTEGRATION] Starting test server thread on port 8099...")
    t = threading.Thread(target=run_test_server, daemon=True)
    t.start()
    time.sleep(1)

    print(f"[INTEGRATION] Testing endpoints against {BASE_URL}")

    # 1. Health check
    raw = http_get("/api/health")
    data = json.loads(raw)
    assert data["status"] == "healthy"
    print("  ✓ GET /api/health passed")

    # 2. Get current dataset
    raw = http_get("/api/dataset/current")
    data = json.loads(raw)
    assert data["total_rows"] == 30
    print(f"  ✓ GET /api/dataset/current passed ({data['total_rows']} rows)")

    # 3. Static files
    html = http_get("/")
    assert "AuditDesk" in html
    print("  ✓ GET / (HTML frontend) passed")

    # 4. Forensic analysis
    data = http_post("/api/forensics/analyze", {"threshold": 5000, "buffer_pct": 0.15})
    assert data["success"] is True
    print(f"  ✓ POST /api/forensics/analyze passed ({data['summary']['total_exceptions']} total exceptions flagged)")

    # 5. Statistical Sampling
    data = http_post("/api/sampling/draw", {"method": "attribute", "confidence": 0.95, "tdr": 0.05, "epdr": 0.01, "seed": 42})
    assert data["success"] is True
    print(f"  ✓ POST /api/sampling/draw passed ({data['result']['sample_size']} items sampled)")

    # 6. AI 5C Finding Draft
    data = http_post("/api/ai/draft-5c", {"provider": "offline", "title": "DOA Threshold Circumvention"})
    assert data["success"] is True
    print("  ✓ POST /api/ai/draft-5c passed")

    # 6b. AI Full Executive Audit Report Draft
    data = http_post("/api/ai/draft-full-report", {"provider": "offline", "engagement_title": "AP Audit"})
    assert data["success"] is True
    assert "overall_opinion" in data["report"]
    print(f"  ✓ POST /api/ai/draft-full-report passed (Opinion: {data['report']['overall_opinion']})")

    # 7. Workpaper Signoff
    data = http_post("/api/workpaper/signoff", {"action": "prepare", "user_name": "Lead Auditor"})
    assert data["workpaper"]["status"] == "Prepared"
    print(f"  ✓ POST /api/workpaper/signoff passed (Status: {data['workpaper']['status']})")

    # 8. Export HTML Memo
    data = http_post("/api/export/html-memo", {})
    assert "Audit Observation Memo" in data["html"]
    print("  ✓ POST /api/export/html-memo passed")

    # 9. Export Excel XML
    data = http_post("/api/export/excel-xml", {})
    assert "Workbook" in data["xml"]
    print("  ✓ POST /api/export/excel-xml passed")

    # 10. Export ICAEW DOCX Report
    req = urllib.request.Request(
        f"{BASE_URL}/api/export/icaew-docx",
        data=json.dumps({}).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    )
    with OPENER.open(req, timeout=5) as resp:
        docx_bytes = resp.read()
        assert len(docx_bytes) > 1000
        # Check ZIP magic header for DOCX (PK\x03\x04)
        assert docx_bytes.startswith(b"PK\x03\x04")
        print(f"  ✓ POST /api/export/icaew-docx passed ({len(docx_bytes):,} bytes valid DOCX)")

    # 11. Single Button Solution (1-Click Auto-Pilot Audit Pipeline)
    data = http_post("/api/autopilot/run", {
        "threshold": 5000.0,
        "buffer_pct": 0.15,
        "provider": "offline",
        "engagement_title": "Automated AP Fieldwork"
    })
    assert data["success"] is True
    assert data["summary"]["total_exceptions"] > 0
    assert len(data["sample"]["sample"]) > 0
    assert "overall_opinion" in data["report"]
    print(f"  ✓ POST /api/autopilot/run (Single Button Solution) passed ({data['summary']['total_exceptions']} exceptions, {len(data['sample']['sample'])} sampled, Opinion: {data['report']['overall_opinion']})")

    print("\n========================================================")
    print("  ALL SESSION-BASED REST ENDPOINTS VALIDATED & PASSING! ")
    print("========================================================")


if __name__ == "__main__":
    test_endpoints()

