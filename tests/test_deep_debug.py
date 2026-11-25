"""
AuditDesk Exhaustive Deep Debug & Boundary Stress Test Suite
Tests dirty data handling, boundary conditions, extreme inputs, unicode safety, 
and CAATs analytical edge cases across all engine modules.
"""

import os
import sys
import json
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from engine.forensics import ForensicEngine, parse_date_fast
from engine.sampling import SamplingEngine
from engine.ai_client import AIClient
from engine.workpaper_export import WorkpaperExporter


def test_dirty_data_resilience():
    print("\n--- 1. TESTING DIRTY DATA & CORRUPTED INPUT RESILIENCE ---")

    dirty_records = [
        {},  # Empty dictionary
        {"invoice_no": "INV-001", "amount": "", "vendor": None, "date": ""},
        {"invoice_no": "INV-002", "amount": "$ 14,500.50", "vendor": "ACME Supplies LLC", "date": "2026-03-14"},
        {"invoice_no": "INV-003", "amount": "(2,500.00)", "vendor": "ACME Supplies", "date": "14/03/2026"},
        {"invoice_no": "INV-004", "amount": "1 234.56", "vendor": "Global Tech Corp.", "date": "Mar 15 2026"},
        {"invoice_no": "INV-005", "amount": "N/A", "vendor": "Global Tech", "date": "INVALID_DATE_STRING"},
        {"invoice_no": "INV-006", "amount": 4950.00, "vendor": "Delta Logistics", "date": "2026-03-21T14:30:00Z"},
        {"invoice_no": "INV-007", "amount": "4950", "vendor": "Delta Logistics Inc", "date": "2026-03-22"},
        {"invoice_no": "INV-008", "amount": 0.0, "vendor": "", "date": None},
        {"invoice_no": "INV-009", "amount": -100.50, "vendor": "Refund Vendor", "date": "2026-03-01"},
        {"invoice_no": "INV-010", "amount": 999999999.99, "vendor": "Mega Corp", "date": "2026-03-02"}
    ]

    # Test Split Transactions on Dirty Data
    splits = ForensicEngine.detect_split_transactions(dirty_records, threshold=5000.0, buffer_pct=0.15)
    print(f"  ✓ Split POs on dirty dataset: {len(splits)} flagged safely (Zero Crashes)")

    # Test Duplicate Payments on Dirty Data
    dupes = ForensicEngine.detect_duplicate_payments(dirty_records)
    print(f"  ✓ Duplicate Matching on dirty dataset: {len(dupes)} flagged safely (Zero Crashes)")

    # Test Benford's Law on Dirty Data
    benford = ForensicEngine.calculate_benfords_law(dirty_records)
    print(f"  ✓ Benford's Law on dirty dataset: Chi-Sq {benford.get('chi_square')} ({benford.get('conformity')})")
    assert isinstance(benford, dict) and "status" in benford

    # Test Weekend Postings on Dirty Data
    weekends = ForensicEngine.detect_out_of_hours(dirty_records)
    print(f"  ✓ Weekend scan on dirty dates: {len(weekends)} flagged safely")


def test_sampling_boundary_conditions():
    print("\n--- 2. TESTING STATISTICAL SAMPLING BOUNDARY CONDITIONS ---")

    # Edge Case: 0 Population
    res_zero = SamplingEngine.calculate_attribute_sample_size(0)
    assert res_zero["computed_sample_size"] == 0
    print("  ✓ Zero population attribute calculation: handled safely (Size: 0)")

    # Edge Case: 1 Item Population
    res_one = SamplingEngine.calculate_attribute_sample_size(1)
    assert res_one["computed_sample_size"] == 1
    print("  ✓ 1-item population attribute calculation: handled safely (Size: 1)")

    # Edge Case: Extreme Confidence (99%) and Strict TDR (2%)
    res_strict = SamplingEngine.calculate_attribute_sample_size(
        population_size=50000,
        confidence_level=0.99,
        tolerable_deviation_rate=0.02,
        expected_deviation_rate=0.005
    )
    assert res_strict["computed_sample_size"] > 50
    print(f"  ✓ Strict AICPA parameter calculation (99% Conf, 2% TDR): {res_strict['computed_sample_size']} items")

    # Monetary Unit Sampling (MUS) on small population
    small_records = [
        {"invoice_no": f"INV-{i}", "amount": float(i * 100), "vendor": f"Vendor {i}"}
        for i in range(1, 15)
    ]
    mus_calc = SamplingEngine.calculate_mus_sample_size(small_records, tolerable_misstatement=500.0)
    print(f"  ✓ MUS calculation on small dataset: {mus_calc['estimated_sample_size']} items")

    # MUS Draw
    mus_draw = SamplingEngine.draw_sample(small_records, sample_size=5, sampling_method="mus")
    assert len(mus_draw["sample"]) == 5
    print("  ✓ MUS cumulative sample extraction: 5 items extracted successfully")

    # Systematic Draw
    sys_draw = SamplingEngine.draw_sample(small_records, sample_size=4, sampling_method="systematic")
    assert len(sys_draw["sample"]) == 4
    print("  ✓ Systematic interval sample extraction: 4 items extracted successfully")


def test_unicode_and_extreme_reporting():
    print("\n--- 3. TESTING UNICODE & EXTREME REPORT EXPORTING ---")

    extreme_findings = [
        {
            "id": f"FIND-{i:03d}",
            "title": f"Finding #{i}: Complex Unicode & Symbols • Café & Co. • €1,250.00 < 50% & 'Quotes' / \"Double Quotes\"",
            "condition": "During our detailed testing of 5,000 transactions, we identified 42 instances where purchase orders were split into amounts of $4,950.00, $4,990.00, and $4,850.00 to bypass Section 4.2 of the Delegation of Authority Policy. " * 3,
            "criteria": "Corporate Delegation of Authority Policy Section 4.2 states that all procurement commitments exceeding $5,000.00 require Vice President approval.",
            "cause": "Absence of automated transaction aggregation controls within the ERP system.",
            "consequence": "Operational exposure and circumvention of internal budgetary governance.",
            "corrective_action": "Implement automated ERP hard-stops to consolidate multiple purchase orders to the same vendor within a 48-hour rolling window.",
            "risk_rating": "High" if i % 2 == 0 else "Medium"
        }
        for i in range(1, 8)
    ]

    report_payload = {
        "engagement_title": "Exhaustive Multi-Finding Fieldwork Audit • FY 2026",
        "overall_opinion": "Limited Assurance",
        "executive_summary": "Extensive testing of accounts payable and procurement ledgers revealed high-risk control deficiencies surrounding Delegation of Authority adherence.",
        "key_findings": extreme_findings,
        "root_cause_summary": "ERP configuration gaps and inadequate supervisory spot-checks.",
        "management_action_plan": [
            {
                "finding_ref": f"FIND-{i:03d}",
                "action_item": f"Enforce ERP hard-stop for finding #{i} across all operating entities.",
                "owner": "Head of Procurement Operations",
                "priority": "High" if i % 2 == 0 else "Medium",
                "target_days": "30 Days" if i % 2 == 0 else "60 Days"
            }
            for i in range(1, 8)
        ]
    }

    # 1. Test ICAEW DOCX Export
    docx_bytes = WorkpaperExporter.generate_icaew_docx(
        report_data=report_payload,
        engagement_title="Exhaustive Multi-Finding Fieldwork Audit",
        audited_unit="Global Procurement & Finance Operations",
        lead_auditor="Lead Internal Auditor (CIA / ACA)"
    )
    assert len(docx_bytes) > 5000
    assert docx_bytes.startswith(b"PK\x03\x04")
    print(f"  ✓ ICAEW DOCX report generated with 7 complex findings: {len(docx_bytes):,} bytes valid DOCX")

    # 2. Test Multi-Tab Excel XML Package
    sample_records = [
        {"invoice_no": f"INV-{i}", "amount": float(i * 125.50), "vendor": f"Vendor #{i} & Co.", "date": "2026-03-15"}
        for i in range(1, 20)
    ]
    xml_str = WorkpaperExporter.generate_excel_xml(
        engagement_title="Exhaustive Multi-Finding Fieldwork Audit",
        sample_data=sample_records[:10],
        anomalies=[{"type": "Split PO", "amount": 4950.0, "vendor": "Vendor #1", "reason": "Threshold split"}],
        finding=extreme_findings[0],
        prepared_by="Lead Auditor",
        reviewed_by="Audit Director"
    )
    assert "Workbook" in xml_str
    assert "Worksheet" in xml_str
    print(f"  ✓ Multi-Tab Master Excel XML package generated: {len(xml_str):,} characters")

    # 3. Test HTML Memo Export
    html_memo = WorkpaperExporter.generate_html_memo(extreme_findings[0])
    assert "Audit Observation Memo" in html_memo
    print(f"  ✓ Executive HTML Memo generated: {len(html_memo):,} characters")


def test_scale_and_speed_benchmark():
    print("\n--- 4. SCALE & SPEED STRESS BENCHMARK (50,000 ROWS) ---")

    # Generate 50,000 synthetic transactions
    large_dataset = []
    vendors = ["Apex Supplies", "Global Logistics", "Alpha Services", "Apex Supplies LLC", "Omega Hardware", "Beta Consulting"]
    for i in range(1, 50001):
        v_idx = i % len(vendors)
        amt = 4950.00 if (i % 25 == 0) else float((i * 17) % 8500 + 10)
        d_str = "2026-03-21" if (i % 7 == 0) else "2026-03-18"  # Saturday vs Wednesday
        large_dataset.append({
            "invoice_no": f"INV-{i:06d}",
            "vendor": vendors[v_idx],
            "amount": amt,
            "date": d_str,
            "cost_center": f"CC-{100 + (i % 10)}"
        })

    t0 = time.perf_counter()
    splits = ForensicEngine.detect_split_transactions(large_dataset, threshold=5000.0, buffer_pct=0.15)
    t_splits = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    dupes = ForensicEngine.detect_duplicate_payments(large_dataset)
    t_dupes = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    benford = ForensicEngine.calculate_benfords_law(large_dataset)
    t_benford = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    weekends = ForensicEngine.detect_out_of_hours(large_dataset)
    t_weekends = (time.perf_counter() - t0) * 1000

    total_time_ms = t_splits + t_dupes + t_benford + t_weekends
    throughput = len(large_dataset) / (total_time_ms / 1000.0)

    print(f"  • Split PO Scan:        {t_splits:.2f} ms ({len(splits):,} anomalies)")
    print(f"  • Duplicate Match Scan: {t_dupes:.2f} ms ({len(dupes):,} duplicates)")
    print(f"  • Benford's Law χ²:     {t_benford:.2f} ms (Chi-Sq: {benford.get('chi_square')})")
    print(f"  • Weekend Postings:     {t_weekends:.2f} ms ({len(weekends):,} entries)")
    print(f"  --------------------------------------------------------")
    print(f"  ✓ Total 50,000 Records Scan Time: {total_time_ms:.2f} ms ({total_time_ms/1000.0:.3f} sec)")
    print(f"  ✓ Analytical Engine Throughput:   {throughput:,.0f} records / second")


if __name__ == "__main__":
    print("=" * 60)
    print("    AUDITDESK EXHAUSTIVE DEEP DEBUG & STRESS TEST HARNESS")
    print("=" * 60)
    
    test_dirty_data_resilience()
    test_sampling_boundary_conditions()
    test_unicode_and_extreme_reporting()
    test_scale_and_speed_benchmark()
    
    print("\n" + "=" * 60)
    print("  >>> ALL FUNCTIONS & BOUNDARY CONDITIONS PASSED 100% <<<")
    print("=" * 60)
