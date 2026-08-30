"""
AuditDesk Application Server
Lightweight, zero-dependency HTTP server with full REST API for internal audit fieldwork:
- Data Ingestion & Demo dataset loader
- Deterministic Forensic Anomaly Engine
- Statistical Sampling Studio
- BYOK AI 5C Narrative & RCM Synthesizer
- Multi-Tab Excel & HTML Workpaper Exporter
"""

import os
import sys
import csv
import json
import io
import mimetypes
from datetime import datetime
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Any, Dict, List, Optional

# Import Engine Modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from engine.forensics import ForensicEngine
from engine.sampling import SamplingEngine
from engine.ai_client import AIClient
from engine.workpaper_export import WorkpaperExporter

PORT = 8090
STATIC_DIR = os.path.join(current_dir, "static")
DATA_DIR = os.path.join(current_dir, "data")

# Ephemeral in-memory store for active session (zero DB footprint)
APP_STATE = {
    "current_dataset": [],
    "dataset_meta": {"name": "No dataset loaded", "rows": 0, "total_amount": 0.0},
    "anomalies": {},
    "current_sample": {},
    "workpaper": {
        "title": "Procurement & Accounts Payable Fieldwork Audit",
        "status": "In Testing",
        "prepared_by": "Lead Auditor",
        "prepared_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "reviewed_by": "",
        "reviewed_at": "",
        "review_notes": ""
    },
    "findings": [],
    "full_report": None
}


def load_demo_data():
    """Loads the pre-packaged sample AP invoices dataset into session memory."""
    csv_path = os.path.join(DATA_DIR, "sample_ap_invoices.csv")
    if os.path.exists(csv_path):
        with open(csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            records = list(reader)
            APP_STATE["current_dataset"] = records
            total_amt = sum(float(r.get("amount", 0.0)) for r in records if r.get("amount"))
            APP_STATE["dataset_meta"] = {
                "name": "sample_ap_invoices.csv",
                "rows": len(records),
                "total_amount": round(total_amt, 2),
                "loaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }


class AuditDeskHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: Any, status_code: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, file_path: str):
        if not os.path.exists(file_path):
            self.send_error(404, "File not found")
            return
        
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or "application/octet-stream"
        
        with open(file_path, "rb") as f:
            content = f.read()

        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_binary(self, data_bytes: bytes, mime_type: str, filename: str = "report.docx"):
        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(data_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data_bytes)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # API Routes
        if path == "/api/health":
            self._send_json({"status": "healthy", "service": "AuditDesk Workbench", "version": "1.0.0"})
            return

        elif path == "/api/dataset/current":
            self._send_json({
                "meta": APP_STATE["dataset_meta"],
                "records": APP_STATE["current_dataset"][:100],  # preview 100
                "total_rows": len(APP_STATE["current_dataset"])
            })
            return

        elif path == "/api/dataset/load-demo":
            load_demo_data()
            self._send_json({
                "success": True,
                "message": "Demo Accounts Payable dataset loaded successfully.",
                "meta": APP_STATE["dataset_meta"],
                "records": APP_STATE["current_dataset"]
            })
            return

        elif path == "/api/workpaper/status":
            self._send_json({
                "workpaper": APP_STATE["workpaper"],
                "findings_count": len(APP_STATE["findings"])
            })
            return

        # Static File Serving
        if path == "/" or path == "/index.html":
            file_path = os.path.join(STATIC_DIR, "index.html")
            self._send_file(file_path)
            return

        # Check in static dir
        clean_path = path.lstrip("/")
        candidate_file = os.path.join(STATIC_DIR, clean_path)
        if os.path.exists(candidate_file) and os.path.isfile(candidate_file):
            self._send_file(candidate_file)
            return

        self.send_error(404, "Page Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        
        try:
            req_data = json.loads(raw_body) if raw_body.strip() else {}
        except Exception:
            req_data = {}

        # 0. 1-Click Auto-Pilot Full Audit Pipeline
        if path == "/api/autopilot/run":
            # If no dataset loaded, auto-load demo data
            if not APP_STATE["current_dataset"]:
                load_demo_data()

            records = APP_STATE["current_dataset"]
            threshold = float(req_data.get("threshold", 5000.0))
            buffer_pct = float(req_data.get("buffer_pct", 0.15))
            api_provider = req_data.get("provider", "offline")
            api_key = req_data.get("api_key", "")
            model_name = req_data.get("model", "")
            custom_endpoint = req_data.get("custom_endpoint", "")
            engagement_title = req_data.get("engagement_title", APP_STATE["workpaper"].get("title", "Accounts Payable & Procurement Audit"))
            audit_scope = req_data.get("audit_scope", "Comprehensive fieldwork review of accounts payable, delegation of authority compliance, duplicate disbursements, and journal entry controls.")

            # Step 1: Forensics
            splits = ForensicEngine.detect_split_transactions(records, threshold=threshold, buffer_pct=buffer_pct)
            duplicates = ForensicEngine.detect_duplicate_payments(records)
            out_of_hours = ForensicEngine.detect_out_of_hours(records)
            benford = ForensicEngine.calculate_benfords_law(records)

            APP_STATE["anomalies"] = {
                "splits": splits,
                "duplicates": duplicates,
                "out_of_hours": out_of_hours,
                "benford": benford,
                "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # Step 2: Sampling
            sample_result = SamplingEngine.draw_sample(
                records=records,
                sample_size=min(25, len(records)),
                random_seed=42,
                sampling_method="random"
            )
            sample_result["rationale"] = "AICPA standard attribute sample extracted for controls verification."
            APP_STATE["current_sample"] = sample_result

            # Step 3: AI Full Report Synthesis
            dossier = {
                "population_rows": len(records),
                "population_amount": APP_STATE["dataset_meta"].get("total_amount", 0.0),
                "splits": splits,
                "duplicates": duplicates,
                "weekends": out_of_hours,
                "benford": benford,
                "sample_info": sample_result
            }

            ai_client = AIClient(provider=api_provider, api_key=api_key, model=model_name, custom_endpoint=custom_endpoint)
            full_report = ai_client.draft_full_audit_report(
                engagement_title=engagement_title,
                audit_scope=audit_scope,
                audit_dossier=dossier
            )
            APP_STATE["full_report"] = full_report
            APP_STATE["findings"] = full_report.get("key_findings", [])
            APP_STATE["workpaper"]["status"] = "Prepared"

            self._send_json({
                "success": True,
                "meta": APP_STATE["dataset_meta"],
                "records": records[:100],
                "summary": {
                    "total_rows": len(records),
                    "split_count": len(splits),
                    "duplicate_count": len(duplicates),
                    "out_of_hours_count": len(out_of_hours),
                    "benford_status": benford.get("conformity", "N/A"),
                    "total_exceptions": len(splits) + len(duplicates) + len(out_of_hours)
                },
                "anomalies": APP_STATE["anomalies"],
                "sample": sample_result,
                "report": full_report,
                "workpaper": APP_STATE["workpaper"]
            })
            return

        # 1. Parse / Upload CSV Data
        elif path == "/api/dataset/upload-csv":
            csv_content = req_data.get("csv_text", "")
            file_name = req_data.get("file_name", "uploaded_dataset.csv")
            try:
                reader = csv.DictReader(io.StringIO(csv_content))
                records = list(reader)
                APP_STATE["current_dataset"] = records
                total_amt = sum(float(r.get("amount", 0.0)) for r in records if r.get("amount"))
                APP_STATE["dataset_meta"] = {
                    "name": file_name,
                    "rows": len(records),
                    "total_amount": round(total_amt, 2),
                    "loaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                self._send_json({"success": True, "meta": APP_STATE["dataset_meta"], "records": records[:50]})
            except Exception as e:
                self._send_json({"success": False, "error": f"Failed to parse CSV: {str(e)}"}, 400)
            return

        # 2. Forensic Anomaly Analysis
        elif path == "/api/forensics/analyze":
            threshold = float(req_data.get("threshold", 5000.0))
            buffer_pct = float(req_data.get("buffer_pct", 0.15))
            records = APP_STATE["current_dataset"]

            if not records:
                self._send_json({"success": False, "error": "No dataset loaded. Please upload a CSV or load demo data first."}, 400)
                return

            splits = ForensicEngine.detect_split_transactions(records, threshold=threshold, buffer_pct=buffer_pct)
            duplicates = ForensicEngine.detect_duplicate_payments(records)
            out_of_hours = ForensicEngine.detect_out_of_hours(records)
            benford = ForensicEngine.calculate_benfords_law(records)

            APP_STATE["anomalies"] = {
                "splits": splits,
                "duplicates": duplicates,
                "out_of_hours": out_of_hours,
                "benford": benford,
                "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            self._send_json({
                "success": True,
                "summary": {
                    "split_count": len(splits),
                    "duplicate_count": len(duplicates),
                    "out_of_hours_count": len(out_of_hours),
                    "benford_status": benford.get("conformity", "N/A"),
                    "total_exceptions": len(splits) + len(duplicates) + len(out_of_hours)
                },
                "details": APP_STATE["anomalies"]
            })
            return

        # 3. Statistical Sampling
        elif path == "/api/sampling/draw":
            method = req_data.get("method", "attribute")
            confidence = float(req_data.get("confidence", 0.95))
            tdr = float(req_data.get("tdr", 0.05))
            epdr = float(req_data.get("epdr", 0.01))
            seed = int(req_data.get("seed", 42))
            custom_size = int(req_data.get("sample_size", 0))

            records = APP_STATE["current_dataset"]
            if not records:
                self._send_json({"success": False, "error": "No dataset loaded."}, 400)
                return

            if custom_size <= 0:
                calc_res = SamplingEngine.calculate_attribute_sample_size(
                    population_size=len(records),
                    confidence_level=confidence,
                    tolerable_deviation_rate=tdr,
                    expected_deviation_rate=epdr
                )
                sample_size = calc_res["computed_sample_size"]
                rationale = calc_res["rationale"]
            else:
                sample_size = custom_size
                rationale = f"User-specified sample size of {sample_size} items with random seed {seed}."

            sample_result = SamplingEngine.draw_sample(
                records=records,
                sample_size=sample_size,
                random_seed=seed,
                sampling_method="random"
            )
            sample_result["rationale"] = rationale
            APP_STATE["current_sample"] = sample_result

            self._send_json({"success": True, "result": sample_result})
            return

        # 4. BYOK AI 5C Finding Generation
        elif path == "/api/ai/draft-5c":
            api_provider = req_data.get("provider", "offline")
            api_key = req_data.get("api_key", "")
            model_name = req_data.get("model", "")
            custom_endpoint = req_data.get("custom_endpoint", "")
            
            finding_title = req_data.get("title", "Circumvention of DOA Approval Thresholds")
            policy_context = req_data.get("policy_context", "Corporate Delegation of Authority Policy (DOA) Section 4.1")
            department = req_data.get("department", "Procurement & Accounts Payable")

            topic = req_data.get("topic", "splits")

            # If anomalies not run yet, auto-evaluate from current dataset
            if not APP_STATE.get("anomalies") and APP_STATE["current_dataset"]:
                records = APP_STATE["current_dataset"]
                APP_STATE["anomalies"] = {
                    "splits": ForensicEngine.detect_split_transactions(records),
                    "duplicates": ForensicEngine.detect_duplicate_payments(records),
                    "out_of_hours": ForensicEngine.detect_out_of_hours(records),
                    "benford": ForensicEngine.calculate_benfords_law(records)
                }

            # Filter exceptions based on topic
            all_anoms = APP_STATE.get("anomalies", {})
            if topic == "splits":
                exceptions_data = {
                    "category": "Split Purchases (DOA Limits)",
                    "exceptions": all_anoms.get("splits", []),
                    "count": len(all_anoms.get("splits", [])),
                    "total_amount": sum(float(x.get("amount", 0.0)) for x in all_anoms.get("splits", []))
                }
            elif topic == "duplicates":
                dupes = all_anoms.get("duplicates", [])
                exceptions_data = {
                    "category": "Duplicate Disbursements",
                    "exceptions": dupes,
                    "count": len(dupes),
                    "total_amount": sum(float(x.get("item_1", {}).get("amount", 0.0)) for x in dupes)
                }
            elif topic == "weekends":
                weekends = all_anoms.get("out_of_hours", [])
                exceptions_data = {
                    "category": "Weekend & Out-of-Hours Postings",
                    "exceptions": weekends,
                    "count": len(weekends),
                    "total_amount": sum(float(x.get("amount", 0.0)) for x in weekends)
                }
            else:
                exceptions_data = {
                    "category": "Comprehensive Exceptions",
                    "splits": all_anoms.get("splits", []),
                    "duplicates": all_anoms.get("duplicates", []),
                    "weekend_postings": all_anoms.get("out_of_hours", []),
                    "benford_status": all_anoms.get("benford", {}).get("conformity", "N/A")
                }

            ai_client = AIClient(provider=api_provider, api_key=api_key, model=model_name, custom_endpoint=custom_endpoint)
            drafted_finding = ai_client.draft_5c_finding(
                finding_title=finding_title,
                exceptions_data=exceptions_data,
                policy_context=policy_context,
                department=department
            )

            # Store in findings list
            APP_STATE["findings"].append(drafted_finding)

            self._send_json({"success": True, "finding": drafted_finding})
            return

        # 4b. AI Full Executive Audit Report Generation
        elif path == "/api/ai/draft-full-report":
            api_provider = req_data.get("provider", "offline")
            api_key = req_data.get("api_key", "")
            model_name = req_data.get("model", "")
            custom_endpoint = req_data.get("custom_endpoint", "")
            engagement_title = req_data.get("engagement_title", APP_STATE["workpaper"].get("title", "Accounts Payable & Procurement Audit"))
            audit_scope = req_data.get("audit_scope", "Review of procurement, vendor payments, approval limits, and journal entries for Q1-Q3.")

            # Ensure anomalies evaluated
            if not APP_STATE.get("anomalies") and APP_STATE["current_dataset"]:
                records = APP_STATE["current_dataset"]
                APP_STATE["anomalies"] = {
                    "splits": ForensicEngine.detect_split_transactions(records),
                    "duplicates": ForensicEngine.detect_duplicate_payments(records),
                    "out_of_hours": ForensicEngine.detect_out_of_hours(records),
                    "benford": ForensicEngine.calculate_benfords_law(records)
                }

            all_anoms = APP_STATE.get("anomalies", {})
            dossier = {
                "population_rows": len(APP_STATE["current_dataset"]),
                "population_amount": APP_STATE["dataset_meta"].get("total_amount", 0.0),
                "splits": all_anoms.get("splits", []),
                "duplicates": all_anoms.get("duplicates", []),
                "weekends": all_anoms.get("out_of_hours", []),
                "benford": all_anoms.get("benford", {}),
                "sample_info": APP_STATE.get("current_sample", {})
            }

            ai_client = AIClient(provider=api_provider, api_key=api_key, model=model_name, custom_endpoint=custom_endpoint)
            full_report = ai_client.draft_full_audit_report(
                engagement_title=engagement_title,
                audit_scope=audit_scope,
                audit_dossier=dossier
            )

            APP_STATE["full_report"] = full_report

            self._send_json({"success": True, "report": full_report})
            return

        # 5. Workpaper Sign-off State Machine
        elif path == "/api/workpaper/signoff":
            action = req_data.get("action", "")  # 'prepare' or 'review'
            user_name = req_data.get("user_name", "Auditor")
            notes = req_data.get("notes", "")

            wp = APP_STATE["workpaper"]
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

            if action == "prepare":
                wp["status"] = "Prepared"
                wp["prepared_by"] = user_name
                wp["prepared_at"] = now_str
            elif action == "review":
                wp["status"] = "Reviewed & Approved"
                wp["reviewed_by"] = user_name
                wp["reviewed_at"] = now_str
                wp["review_notes"] = notes
            elif action == "lock":
                wp["status"] = "Final & Locked"

            self._send_json({"success": True, "workpaper": wp})
            return

        # 6. Export Workpaper (HTML Memo or Excel XML)
        elif path == "/api/export/html-memo":
            finding = req_data.get("finding") or (APP_STATE["findings"][-1] if APP_STATE["findings"] else {
                "title": "Audit Observation Memo",
                "condition": "Sample testing identified control deviations.",
                "criteria": "Standard SOPs",
                "cause": "Manual processing error",
                "consequence": "Operational exposure",
                "corrective_action": "Implement automated validation controls.",
                "risk_rating": "High"
            })
            html_memo = WorkpaperExporter.generate_html_memo(
                finding=finding,
                engagement_title=APP_STATE["workpaper"].get("title", "Annual AP Audit"),
                prepared_by=APP_STATE["workpaper"].get("prepared_by", "Staff Auditor"),
                reviewed_by=APP_STATE["workpaper"].get("reviewed_by", "Audit Manager"),
                status=APP_STATE["workpaper"].get("status", "Reviewed")
            )
            self._send_json({"success": True, "html": html_memo})
            return

        elif path == "/api/export/excel-xml":
            sample_data = APP_STATE.get("current_sample", {}).get("sample", [])
            splits = APP_STATE.get("anomalies", {}).get("splits", [])
            dupes = APP_STATE.get("anomalies", {}).get("duplicates", [])
            all_anomalies = splits + dupes

            xml_data = WorkpaperExporter.generate_excel_xml(
                engagement_title=APP_STATE["workpaper"].get("title", "Annual AP Audit"),
                sample_data=sample_data,
                anomalies=all_anomalies,
                prepared_by=APP_STATE["workpaper"].get("prepared_by", "Staff Auditor"),
                reviewed_by=APP_STATE["workpaper"].get("reviewed_by", "Audit Manager")
            )
            self._send_json({"success": True, "xml": xml_data, "filename": "AuditDesk_Workpaper_Package.xml"})
            return

        elif path in ("/api/export/iia-docx", "/api/export/icaew-docx"):
            report_data = req_data.get("report") or APP_STATE.get("full_report") or {
                "engagement_title": APP_STATE["workpaper"].get("title", "Accounts Payable Fieldwork Audit"),
                "overall_opinion": "Limited Assurance",
                "executive_summary": "Testing revealed multiple instances of transaction splitting and duplicate payments.",
                "key_findings": APP_STATE.get("findings", []),
                "root_cause_summary": "Absence of automated ERP purchase order threshold validation.",
                "management_action_plan": [
                    {"action_item": "Enforce automated ERP vendor order aggregation.", "owner": "Head of Procurement", "priority": "High", "target_days": "30 Days"}
                ]
            }

            docx_bytes = WorkpaperExporter.generate_icaew_docx(
                report_data=report_data,
                engagement_title=report_data.get("engagement_title", "Internal Audit Report"),
                audited_unit="Finance & Procurement Operations",
                lead_auditor=APP_STATE["workpaper"].get("prepared_by", "Lead Internal Auditor (CIA / ACA)")
            )

            self._send_binary(
                data_bytes=docx_bytes,
                mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                filename="IIA_Internal_Audit_Report.docx"
            )
            return

        self.send_error(404, "Endpoint Not Found")


def run_server(port=PORT, auto_open=True):
    import webbrowser
    import threading

    # Preload demo data on start
    load_demo_data()
    server_address = ("", port)
    httpd = ThreadingHTTPServer(server_address, AuditDeskHandler)
    url = f"http://localhost:{port}"
    print("=" * 60)
    print("      🚀 AUDITDESK FIELDWORK WORKBENCH RUNNING")
    print("=" * 60)
    print(f"  URL:           {url}")
    print(f"  Sample Data:   {len(APP_STATE['current_dataset'])} records loaded in session memory")
    print(f"  Stop Server:   Press Ctrl+C in this terminal")
    print("=" * 60)

    if auto_open:
        def _open_browser():
            import time
            time.sleep(0.6)
            try:
                webbrowser.open(url)
            except Exception:
                pass
        threading.Thread(target=_open_browser, daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down AuditDesk server.")
        httpd.server_close()


if __name__ == "__main__":
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    auto_open_flag = "--no-browser" not in sys.argv
    run_server(port_arg, auto_open=auto_open_flag)

