"""
Automated Verification & Unit Tests for AuditDesk
Tests deterministic forensic rules, statistical sampling calculations, BYOK AI fallback, and workpaper exports.
"""

import os
import sys
import csv

# Add auditdesk to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from engine.forensics import ForensicEngine
from engine.sampling import SamplingEngine
from engine.ai_client import AIClient
from engine.workpaper_export import WorkpaperExporter


def test_forensics():
    csv_file = os.path.join(parent_dir, "data", "sample_ap_invoices.csv")
    with open(csv_file, "r", encoding="utf-8") as f:
        records = list(csv.DictReader(f))

    print(f"[TEST 1] Loaded {len(records)} test invoice records.")

    # 1. Split transactions test
    splits = ForensicEngine.detect_split_transactions(records, threshold=5000.0, buffer_pct=0.15)
    print(f" -> Split transactions flagged: {len(splits)}")
    assert len(splits) >= 4, f"Expected at least 4 split items, got {len(splits)}"

    # 2. Duplicate payments test
    dupes = ForensicEngine.detect_duplicate_payments(records)
    print(f" -> Duplicate payments flagged: {len(dupes)}")
    assert len(dupes) >= 1, f"Expected at least 1 duplicate match, got {len(dupes)}"

    # 3. Benford's Law test
    benford = ForensicEngine.calculate_benfords_law(records)
    print(f" -> Benford's Law Chi-Square: {benford.get('chi_square')} ({benford.get('conformity')})")
    assert benford["status"] == "success"
    assert len(benford["digits"]) == 9

    # 4. Weekend test
    weekends = ForensicEngine.detect_out_of_hours(records)
    print(f" -> Weekend entries flagged: {len(weekends)}")
    assert len(weekends) >= 2


def test_sampling():
    csv_file = os.path.join(parent_dir, "data", "sample_ap_invoices.csv")
    with open(csv_file, "r", encoding="utf-8") as f:
        records = list(csv.DictReader(f))

    # AICPA Attribute Sampling
    attr_res = SamplingEngine.calculate_attribute_sample_size(
        population_size=len(records),
        confidence_level=0.95,
        tolerable_deviation_rate=0.05,
        expected_deviation_rate=0.01
    )
    print(f"[TEST 2] Attribute Sample Size: {attr_res['computed_sample_size']} items")
    assert attr_res["computed_sample_size"] > 0

    # Seed-reproducible draw
    sample_draw = SamplingEngine.draw_sample(records, sample_size=10, random_seed=42)
    assert len(sample_draw["sample"]) == 10
    assert sample_draw["seed"] == 42
    print(f" -> Successfully drew reproducible sample with seed 42.")


def test_ai_fallback():
    client = AIClient(provider="offline")
    finding = client.draft_5c_finding(
        finding_title="Circumvention of DOA Limits",
        exceptions_data={"count": 14, "total_amount": 68400.0}
    )
    print(f"[TEST 3] AI 5C Finding Generated:")
    print(f" -> Title: {finding.get('title')}")
    print(f" -> Risk Rating: {finding.get('risk_rating')}")
    assert "condition" in finding
    assert "criteria" in finding
    assert "cause" in finding
    assert "consequence" in finding
    assert "corrective_action" in finding


def test_exports():
    finding = {
        "title": "Unapproved Split Orders",
        "condition": "14 invoices split below $5k limit.",
        "criteria": "DOA Policy Sec 4.1",
        "cause": "ERP gap",
        "consequence": "Spend leakage",
        "corrective_action": "Fix ERP limits",
        "risk_rating": "High"
    }
    html_memo = WorkpaperExporter.generate_html_memo(finding)
    assert "Audit Observation Memo" in html_memo or "Unapproved Split Orders" in html_memo

    excel_xml = WorkpaperExporter.generate_excel_xml(
        engagement_title="AP Fieldwork Test",
        sample_data=[{"invoice": "INV-101", "amount": 1000}],
        anomalies=[{"id": "INV-102", "amount": 4980, "reason": "Split"}]
    )
    assert "Worksheet ss:Name=" in excel_xml
    print("[TEST 4] Formatted HTML memo and Excel XML export verified successfully.")


if __name__ == "__main__":
    print("========================================")
    print("RUNNING AUDITDESK VERIFICATION SUITE")
    print("========================================")
    test_forensics()
    test_sampling()
    test_ai_fallback()
    test_exports()
    print("========================================")
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("========================================")
