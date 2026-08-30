"""
AuditDesk Workpaper Exporter Engine
Generates standardized, professional internal audit workpaper packages (HTML, CSV, formatted Excel-compatible XML)
including Scope, Population Reconciliation, Sample Testing Sheets, 5C Findings, and Dual Sign-off trails.
"""

import html
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional


class WorkpaperExporter:
    @staticmethod
    def generate_html_memo(
        finding: Dict[str, Any],
        engagement_title: str = "Annual Internal Audit Engagement",
        prepared_by: str = "Staff Auditor",
        reviewed_by: str = "Audit Manager",
        status: str = "Reviewed",
        timestamp: Optional[str] = None
    ) -> str:
        """Generates a clean, executive-ready HTML Audit Finding Memo."""
        ts = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        rating = finding.get("risk_rating", "Medium")
        rating_color = {
            "Critical": "#dc2626",
            "High": "#ea580c",
            "Medium": "#d97706",
            "Low": "#16a34a"
        }.get(rating, "#2563eb")

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Audit Observation Memo - {html.escape(finding.get('title', 'Observation'))}</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 900px; margin: 40px auto; padding: 0 20px; background: #f8fafc; }}
    .memo-card {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 40px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    .memo-header {{ border-bottom: 2px solid #0f172a; padding-bottom: 20px; margin-bottom: 30px; }}
    .memo-title {{ font-size: 24px; font-weight: 800; color: #0f172a; margin: 0 0 10px 0; }}
    .badge {{ display: inline-block; padding: 4px 12px; border-radius: 9999px; font-weight: 700; font-size: 13px; color: #fff; background: {rating_color}; }}
    .status-badge {{ display: inline-block; padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 12px; background: #e0f2fe; color: #0369a1; margin-left: 10px; }}
    .meta-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 20px 0; font-size: 14px; background: #f1f5f9; padding: 15px; border-radius: 8px; }}
    .meta-item strong {{ color: #475569; }}
    .section {{ margin-bottom: 25px; }}
    .section-title {{ font-size: 16px; font-weight: 700; color: #0f172a; border-left: 4px solid #2563eb; padding-left: 10px; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }}
    .section-body {{ font-size: 15px; color: #334155; background: #ffffff; padding: 12px 16px; border: 1px solid #f1f5f9; border-radius: 6px; }}
    .signoff-box {{ margin-top: 40px; border-top: 1px dashed #cbd5e1; padding-top: 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
    .signoff-card {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 15px; border-radius: 8px; font-size: 13px; }}
    .footer-note {{ margin-top: 30px; font-size: 12px; color: #94a3b8; text-align: center; }}
</style>
</head>
<body>
<div class="memo-card">
    <div class="memo-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div class="memo-title">{html.escape(finding.get('title', 'Internal Audit Observation'))}</div>
            <div>
                <span class="badge">{rating} Risk</span>
                <span class="status-badge">{status}</span>
            </div>
        </div>
        <div style="color: #64748b; font-size: 14px;">Engagement: {html.escape(engagement_title)}</div>
    </div>

    <div class="meta-grid">
        <div class="meta-item"><strong>Audit Area:</strong> {html.escape(finding.get('area', 'Procurement & AP'))}</div>
        <div class="meta-item"><strong>Date Documented:</strong> {ts}</div>
        <div class="meta-item"><strong>Likelihood Score:</strong> {finding.get('likelihood_score', 3)} / 5</div>
        <div class="meta-item"><strong>Impact Score:</strong> {finding.get('impact_score', 4)} / 5</div>
    </div>

    <div class="section">
        <div class="section-title">1. Condition (What was observed)</div>
        <div class="section-body">{html.escape(finding.get('condition', 'N/A')).replace(chr(10), '<br>')}</div>
    </div>

    <div class="section">
        <div class="section-title">2. Criteria (What should be / Policy Standard)</div>
        <div class="section-body">{html.escape(finding.get('criteria', 'N/A')).replace(chr(10), '<br>')}</div>
    </div>

    <div class="section">
        <div class="section-title">3. Cause (Root Cause)</div>
        <div class="section-body">{html.escape(finding.get('cause', 'N/A')).replace(chr(10), '<br>')}</div>
    </div>

    <div class="section">
        <div class="section-title">4. Consequence (Risk & Impact)</div>
        <div class="section-body">{html.escape(finding.get('consequence', 'N/A')).replace(chr(10), '<br>')}</div>
    </div>

    <div class="section">
        <div class="section-title">5. Corrective Action (Recommendation)</div>
        <div class="section-body">{html.escape(finding.get('corrective_action', 'N/A')).replace(chr(10), '<br>')}</div>
    </div>

    <div class="signoff-box">
        <div class="signoff-card">
            <strong>Prepared By:</strong> {html.escape(prepared_by)}<br>
            <strong>Role:</strong> Internal Auditor<br>
            <strong>Status:</strong> Completed & Documented
        </div>
        <div class="signoff-card">
            <strong>Reviewed By:</strong> {html.escape(reviewed_by or 'Pending Review')}<br>
            <strong>Role:</strong> Audit Senior / Manager<br>
            <strong>Status:</strong> {status}
        </div>
    </div>

    <div class="footer-note">
        Generated by AuditDesk Intelligent Workbench • Confidential Internal Audit Workpaper
    </div>
</div>
</body>
</html>
"""
        return html_content

    @staticmethod
    def generate_excel_xml(
        engagement_title: str,
        sample_data: List[Dict[str, Any]],
        anomalies: List[Dict[str, Any]],
        finding: Optional[Dict[str, Any]] = None,
        prepared_by: str = "Staff Auditor",
        reviewed_by: str = "Audit Manager"
    ) -> str:
        """
        Generates an Excel XML Spreadsheet (.xml) that opens natively in Microsoft Excel with full styling.
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Build Sample Rows
        sample_rows_xml = ""
        if sample_data:
            # Get headers from first item
            headers = [k for k in sample_data[0].keys() if not k.startswith("_raw")]
            header_cells = "".join([f'<Cell ss:StyleID="HeaderStyle"><Data ss:Type="String">{html.escape(h)}</Data></Cell>' for h in headers])
            sample_rows_xml += f"<Row>{header_cells}</Row>\n"

            for item in sample_data:
                cells = ""
                for h in headers:
                    val = item.get(h, "")
                    try:
                        fval = float(val)
                        cells += f'<Cell ss:StyleID="DataStyle"><Data ss:Type="Number">{fval}</Data></Cell>'
                    except (ValueError, TypeError):
                        cells += f'<Cell ss:StyleID="DataStyle"><Data ss:Type="String">{html.escape(str(val))}</Data></Cell>'
                sample_rows_xml += f"<Row>{cells}</Row>\n"
        else:
            sample_rows_xml = '<Row><Cell><Data ss:Type="String">No sample drawn.</Data></Cell></Row>'

        # Build Anomaly Rows
        anomaly_rows_xml = ""
        anomaly_headers = ["ID/Invoice", "Type / Reason", "Vendor", "Amount ($)", "Severity", "Date"]
        anomaly_rows_xml += "<Row>" + "".join([f'<Cell ss:StyleID="HeaderStyle"><Data ss:Type="String">{h}</Data></Cell>' for h in anomaly_headers]) + "</Row>\n"
        for a in anomalies:
            amt = a.get("amount", a.get("item_1", {}).get("amount", 0.0))
            vendor = a.get("vendor", a.get("item_1", {}).get("vendor", "N/A"))
            inv = a.get("id", a.get("invoice_no", a.get("item_1", {}).get("invoice_no", "N/A")))
            date_val = a.get("date", a.get("item_1", {}).get("date", "N/A"))
            reason = a.get("reason", a.get("match_type", "Anomaly"))
            sev = a.get("severity", "Medium")

            anomaly_rows_xml += f"""<Row>
                <Cell ss:StyleID="DataStyle"><Data ss:Type="String">{html.escape(str(inv))}</Data></Cell>
                <Cell ss:StyleID="DataStyle"><Data ss:Type="String">{html.escape(str(reason))}</Data></Cell>
                <Cell ss:StyleID="DataStyle"><Data ss:Type="String">{html.escape(str(vendor))}</Data></Cell>
                <Cell ss:StyleID="CurrencyStyle"><Data ss:Type="Number">{float(amt)}</Data></Cell>
                <Cell ss:StyleID="DataStyle"><Data ss:Type="String">{html.escape(str(sev))}</Data></Cell>
                <Cell ss:StyleID="DataStyle"><Data ss:Type="String">{html.escape(str(date_val))}</Data></Cell>
            </Row>\n"""

        xml = f"""<?xml version="1.0"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:o="urn:schemas-microsoft-com:office:office"
 xmlns:x="urn:schemas-microsoft-com:office:excel"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:html="http://www.w3.org/TR/REC-html40">
 <Styles>
  <Style ss:ID="Default" ss:Name="Normal">
   <Alignment ss:Vertical="Bottom"/>
   <Font ss:FontName="Calibri" x:Family="Swiss" ss:Size="11" ss:Color="#000000"/>
  </Style>
  <Style ss:ID="HeaderStyle">
   <Alignment ss:Horizontal="Center" ss:Vertical="Center"/>
   <Borders>
    <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="2"/>
   </Borders>
   <Font ss:FontName="Calibri" ss:Size="11" ss:Color="#FFFFFF" ss:Bold="1"/>
   <Interior ss:Color="#1E3A8A" ss:Pattern="Solid"/>
  </Style>
  <Style ss:ID="TitleStyle">
   <Font ss:FontName="Calibri" ss:Size="16" ss:Color="#1E3A8A" ss:Bold="1"/>
  </Style>
  <Style ss:ID="DataStyle">
   <Borders>
    <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#E2E8F0"/>
   </Borders>
  </Style>
  <Style ss:ID="CurrencyStyle">
   <NumberFormat ss:Format="$#,##0.00"/>
   <Borders>
    <Border ss:Position="Bottom" ss:LineStyle="Continuous" ss:Weight="1" ss:Color="#E2E8F0"/>
   </Borders>
  </Style>
 </Styles>

 <Worksheet ss:Name="Audit Summary &amp; Scope">
  <Table>
   <Column ss:Width="200"/>
   <Column ss:Width="350"/>
   <Row><Cell ss:StyleID="TitleStyle"><Data ss:Type="String">INTERNAL AUDIT WORKPAPER PACKAGE</Data></Cell></Row>
   <Row><Cell><Data ss:Type="String">Engagement Title:</Data></Cell><Cell><Data ss:Type="String">{html.escape(engagement_title)}</Data></Cell></Row>
   <Row><Cell><Data ss:Type="String">Date Generated:</Data></Cell><Cell><Data ss:Type="String">{now_str}</Data></Cell></Row>
   <Row><Cell><Data ss:Type="String">Prepared By:</Data></Cell><Cell><Data ss:Type="String">{html.escape(prepared_by)}</Data></Cell></Row>
   <Row><Cell><Data ss:Type="String">Reviewed By:</Data></Cell><Cell><Data ss:Type="String">{html.escape(reviewed_by)}</Data></Cell></Row>
   <Row><Cell><Data ss:Type="String">Sample Items Extracted:</Data></Cell><Cell><Data ss:Type="Number">{len(sample_data)}</Data></Cell></Row>
   <Row><Cell><Data ss:Type="String">Red-Flag Exceptions Found:</Data></Cell><Cell><Data ss:Type="Number">{len(anomalies)}</Data></Cell></Row>
  </Table>
 </Worksheet>

 <Worksheet ss:Name="Sample Testing Sheet">
  <Table>
   {sample_rows_xml}
  </Table>
 </Worksheet>

 <Worksheet ss:Name="Red-Flag Exceptions">
  <Table>
   {anomaly_rows_xml}
  </Table>
 </Worksheet>
</Workbook>"""
        return xml

    @staticmethod
    def generate_icaew_docx(
        report_data: Dict[str, Any],
        engagement_title: str = "Accounts Payable & Procurement Fieldwork Audit",
        audited_unit: str = "Finance & Procurement Operations",
        lead_auditor: str = "Lead Internal Auditor (CIA / ACA)",
        audit_period: str = "Q1 - Q3",
        sample_info: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Generates a professional, IIA-compliant Internal Audit Report (.docx)
        aligned with the Institute of Internal Auditors (IIA) Global Internal Audit Standards.
        """
        import io
        import docx
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml import OxmlElement, parse_xml
        from docx.oxml.ns import nsdecls, qn

        doc = docx.Document()

        # Set 1-inch margins
        for section in doc.sections:
            section.top_margin = Inches(1.0)
            section.bottom_margin = Inches(1.0)
            section.left_margin = Inches(1.0)
            section.right_margin = Inches(1.0)

        # Helper function for cell background color
        def set_cell_background(cell, fill_hex):
            shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
            cell._tc.get_or_add_tcPr().append(shading_elm)

        # Helper function for cell borders
        def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
            tcPr = cell._tc.get_or_add_tcPr()
            tcMar = OxmlElement('w:tcMar')
            for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
                node = OxmlElement(f'w:{m}')
                node.set(qn('w:w'), str(val))
                node.set(qn('w:type'), 'dxa')
                tcMar.append(node)
            tcPr.append(tcMar)

        # -------------------------------------------------------------
        # 1. REPORT HEADER / COVER BLOCK (IIA Standards Layout)
        # -------------------------------------------------------------
        title_p = doc.add_paragraph()
        title_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run_label = title_p.add_run("CONFIDENTIAL INTERNAL AUDIT REPORT\n")
        run_label.font.name = "Arial"
        run_label.font.size = Pt(10)
        run_label.font.bold = True
        run_label.font.color.rgb = RGBColor(100, 116, 139) # Slate

        run_title = title_p.add_run(engagement_title.upper())
        run_title.font.name = "Arial"
        run_title.font.size = Pt(20)
        run_title.font.bold = True
        run_title.font.color.rgb = RGBColor(30, 58, 138) # Navy Blue

        # Metadata Table
        meta_table = doc.add_table(rows=4, cols=2)
        meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        meta_table.autofit = False

        meta_rows = [
            ("Audited Entity / Business Unit:", audited_unit),
            ("Audit Period Covered:", audit_period),
            ("Report Date:", datetime.now().strftime("%d %B %Y")),
            ("Lead Auditor / Engagement Lead:", lead_auditor)
        ]

        for i, (k, v) in enumerate(meta_rows):
            cell_k = meta_table.cell(i, 0)
            cell_v = meta_table.cell(i, 1)
            cell_k.width = Inches(2.5)
            cell_v.width = Inches(4.0)
            
            p_k = cell_k.paragraphs[0]
            p_k.add_run(k).bold = True
            p_k.runs[0].font.size = Pt(9.5)
            p_k.runs[0].font.color.rgb = RGBColor(51, 65, 85)

            p_v = cell_v.paragraphs[0]
            p_v.add_run(v)
            p_v.runs[0].font.size = Pt(9.5)
            p_v.runs[0].font.color.rgb = RGBColor(15, 23, 42)

            set_cell_background(cell_k, "F8FAFC")
            set_cell_background(cell_v, "FFFFFF")

        doc.add_paragraph() # Spacer

        # -------------------------------------------------------------
        # 2. SECTION 1: EXECUTIVE SUMMARY & OVERALL OPINION
        # -------------------------------------------------------------
        h1 = doc.add_heading("1. Executive Summary & Overall Audit Opinion", level=1)
        h1.runs[0].font.color.rgb = RGBColor(30, 58, 138)

        opinion = report_data.get("overall_opinion", "Limited Assurance")
        # Map opinion to IIA standard wording
        if opinion in ("Unsatisfactory", "Limited"):
            icaew_opinion = "Limited Assurance"
            opinion_bg = "FEF2F2"
            opinion_color = RGBColor(185, 28, 28) # Red
            opinion_desc = "Significant control weaknesses identified. Immediate management corrective action required to avoid material financial loss or compliance breach."
        elif opinion in ("Needs Improvement", "Reasonable"):
            icaew_opinion = "Reasonable Assurance"
            opinion_bg = "FFFBEB"
            opinion_color = RGBColor(180, 83, 9) # Amber
            opinion_desc = "Internal controls are largely sound but key improvements are required in specific operational processes."
        else:
            icaew_opinion = "Substantial Assurance"
            opinion_bg = "F0FDF4"
            opinion_color = RGBColor(22, 101, 52) # Green
            opinion_desc = "A sound system of internal control is in place and operating effectively to achieve operational objectives."

        # Opinion Box Table
        op_table = doc.add_table(rows=1, cols=1)
        op_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        op_cell = op_table.cell(0, 0)
        op_cell.width = Inches(6.5)
        set_cell_background(op_cell, opinion_bg)
        set_cell_margins(op_cell, top=150, bottom=150, left=200, right=200)

        op_p = op_cell.paragraphs[0]
        r1 = op_p.add_run(f"OVERALL AUDIT OPINION: {icaew_opinion.upper()}\n")
        r1.bold = True
        r1.font.size = Pt(12)
        r1.font.color.rgb = opinion_color

        r2 = op_p.add_run(opinion_desc)
        r2.font.size = Pt(9.5)
        r2.font.italic = True
        r2.font.color.rgb = RGBColor(51, 65, 85)

        doc.add_paragraph() # Spacer

        # Executive Summary Narrative
        exec_summary_text = report_data.get("executive_summary", "")
        if exec_summary_text:
            p_summary = doc.add_paragraph()
            p_summary.add_run("Executive Context & Findings:\n").bold = True
            p_summary.runs[0].font.size = Pt(10)
            run_sum = p_summary.add_run(exec_summary_text)
            run_sum.font.size = Pt(10)
            run_sum.font.color.rgb = RGBColor(30, 41, 59)

        # Root Cause Summary
        root_cause = report_data.get("root_cause_summary", "")
        if root_cause:
            p_root = doc.add_paragraph()
            p_root.add_run("Systemic Root Cause Assessment:\n").bold = True
            p_root.runs[0].font.size = Pt(10)
            p_root.runs[0].font.color.rgb = RGBColor(180, 83, 9)
            run_rc = p_root.add_run(root_cause)
            run_rc.font.size = Pt(9.5)
            run_rc.font.color.rgb = RGBColor(51, 65, 85)

        # -------------------------------------------------------------
        # 3. SECTION 2: SUMMARY OF AUDIT FINDINGS MATRIX
        # -------------------------------------------------------------
        h2 = doc.add_heading("2. Summary of Findings by Priority", level=1)
        h2.runs[0].font.color.rgb = RGBColor(30, 58, 138)

        findings_list = report_data.get("key_findings", [])
        high_count = sum(1 for f in findings_list if f.get("risk_rating") in ("High", "Critical"))
        med_count = sum(1 for f in findings_list if f.get("risk_rating") == "Medium")
        low_count = sum(1 for f in findings_list if f.get("risk_rating") == "Low")

        sum_table = doc.add_table(rows=2, cols=4)
        sum_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        headers = ["High Priority", "Medium Priority", "Low Priority", "Total Findings"]
        counts = [str(high_count), str(med_count), str(low_count), str(len(findings_list))]
        header_colors = ["B91C1C", "B45309", "15803D", "1E3A8A"]

        for col_idx in range(4):
            c_head = sum_table.cell(0, col_idx)
            c_val = sum_table.cell(1, col_idx)
            c_head.width = Inches(1.6)
            c_val.width = Inches(1.6)
            
            p_h = c_head.paragraphs[0]
            p_h.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r_h = p_h.add_run(headers[col_idx])
            r_h.bold = True
            r_h.font.size = Pt(9.5)
            r_h.font.color.rgb = RGBColor(255, 255, 255)
            set_cell_background(c_head, header_colors[col_idx])

            p_v = c_val.paragraphs[0]
            p_v.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r_v = p_v.add_run(counts[col_idx])
            r_v.bold = True
            r_v.font.size = Pt(14)
            set_cell_background(c_val, "F8FAFC")

        doc.add_paragraph() # Spacer

        # -------------------------------------------------------------
        # 4. SECTION 3: DETAILED AUDIT FINDINGS (IIA Standard 5C)
        # -------------------------------------------------------------
        h3 = doc.add_heading("3. Detailed Findings & Agreed Action Plans", level=1)
        h3.runs[0].font.color.rgb = RGBColor(30, 58, 138)

        for idx, f in enumerate(findings_list):
            f_title = f.get("title", f"Finding {idx + 1}")
            f_rating = f.get("risk_rating", "High")
            
            p_ftitle = doc.add_paragraph()
            p_ftitle.add_run(f"Observation {idx + 1}: {f_title} ").bold = True
            p_ftitle.runs[0].font.size = Pt(11)
            p_ftitle.runs[0].font.color.rgb = RGBColor(30, 58, 138)

            badge_run = p_ftitle.add_run(f"[{f_rating.upper()} PRIORITY]")
            badge_run.bold = True
            badge_run.font.size = Pt(9.5)
            badge_run.font.color.rgb = RGBColor(185, 28, 28) if f_rating in ("High", "Critical") else RGBColor(180, 83, 9)

            # Finding Detail Table (IIA Standard Block)
            f_table = doc.add_table(rows=4, cols=2)
            f_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            
            f_rows = [
                ("Control Objective / Criteria", f.get("criteria", "Applicable corporate policies & DOA limits")),
                ("Observation & Factual Condition", f.get("condition", "N/A")),
                ("Root Cause & Underlying Factors", f.get("cause", "Inadequate automated validation gates")),
                ("Risk & Business Implication", f.get("consequence", "Financial leakage and unauthorized commitments"))
            ]

            for r_i, (lbl, text_val) in enumerate(f_rows):
                c_lbl = f_table.cell(r_i, 0)
                c_val = f_table.cell(r_i, 1)
                c_lbl.width = Inches(2.2)
                c_val.width = Inches(4.3)

                p_l = c_lbl.paragraphs[0]
                p_l.add_run(lbl).bold = True
                p_l.runs[0].font.size = Pt(9)
                p_l.runs[0].font.color.rgb = RGBColor(71, 85, 105)

                p_txt = c_val.paragraphs[0]
                p_txt.add_run(text_val)
                p_txt.runs[0].font.size = Pt(9)
                p_txt.runs[0].font.color.rgb = RGBColor(15, 23, 42)

                set_cell_background(c_lbl, "F1F5F9")
                set_cell_background(c_val, "FFFFFF")

            # Agreed Management Action Box
            rec_p = doc.add_paragraph()
            rec_p.paragraph_format.left_indent = Inches(0.2)
            rec_p.add_run("Agreed Management Action / Recommendation:\n").bold = True
            rec_p.runs[0].font.size = Pt(9.5)
            rec_p.runs[0].font.color.rgb = RGBColor(21, 128, 61)
            
            r_act = rec_p.add_run(f.get("corrective_action", "Management to review and remediate identified gaps."))
            r_act.font.size = Pt(9)
            r_act.font.color.rgb = RGBColor(30, 41, 59)

            doc.add_paragraph() # Spacer between findings

        # -------------------------------------------------------------
        # 5. SECTION 4: MANAGEMENT ACTION PLAN SUMMARY (CAPA)
        # -------------------------------------------------------------
        h4 = doc.add_heading("4. Prioritized Management Action Plan (CAPA)", level=1)
        h4.runs[0].font.color.rgb = RGBColor(30, 58, 138)

        actions = report_data.get("management_action_plan", [])
        if actions:
            act_table = doc.add_table(rows=len(actions) + 1, cols=4)
            act_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            
            act_headers = ["Action Required", "Responsible Owner", "Priority", "Target Date"]
            for col_i, h in enumerate(act_headers):
                cell_h = act_table.cell(0, col_i)
                p_ah = cell_h.paragraphs[0]
                p_ah.add_run(h).bold = True
                p_ah.runs[0].font.size = Pt(9)
                p_ah.runs[0].font.color.rgb = RGBColor(255, 255, 255)
                set_cell_background(cell_h, "1E3A8A")

            for r_idx, act in enumerate(actions):
                c0 = act_table.cell(r_idx + 1, 0)
                c1 = act_table.cell(r_idx + 1, 1)
                c2 = act_table.cell(r_idx + 1, 2)
                c3 = act_table.cell(r_idx + 1, 3)

                c0.width = Inches(3.2)
                c1.width = Inches(1.5)
                c2.width = Inches(0.9)
                c3.width = Inches(0.9)

                c0.paragraphs[0].add_run(act.get("action_item", "")).font.size = Pt(8.5)
                c1.paragraphs[0].add_run(act.get("owner", "")).font.size = Pt(8.5)
                
                p_prio = c2.paragraphs[0]
                p_prio.add_run(act.get("priority", "High")).bold = True
                p_prio.runs[0].font.size = Pt(8.5)
                p_prio.runs[0].font.color.rgb = RGBColor(185, 28, 28) if act.get("priority") == "High" else RGBColor(180, 83, 9)

                c3.paragraphs[0].add_run(act.get("target_days", "30 Days")).font.size = Pt(8.5)

                set_cell_background(c0, "FFFFFF" if r_idx % 2 == 0 else "F8FAFC")
                set_cell_background(c1, "FFFFFF" if r_idx % 2 == 0 else "F8FAFC")
                set_cell_background(c2, "FFFFFF" if r_idx % 2 == 0 else "F8FAFC")
                set_cell_background(c3, "FFFFFF" if r_idx % 2 == 0 else "F8FAFC")

        doc.add_paragraph() # Spacer

        # -------------------------------------------------------------
        # 6. APPENDIX: SCOPE & STATISTICAL SAMPLING METHODOLOGY
        # -------------------------------------------------------------
        h_app = doc.add_heading("Appendix: Scope & Testing Methodology", level=1)
        h_app.runs[0].font.color.rgb = RGBColor(71, 85, 105)

        p_app = doc.add_paragraph()
        p_app.add_run(
            "This engagement was conducted in conformance with the Global Internal Audit Standards (GIAS) "
            "and International Professional Practices Framework (IPPF) issued by the Institute of Internal Auditors (IIA).\n\n"
            "Testing utilized computer-assisted audit techniques (CAATs) including Benford's Law distribution analysis, "
            "sliding-window delegation of authority split limit detection, and AICPA-compliant statistical attribute sampling. "
            "Sample selections are seed-reproducible and reconciled to the underlying general ledger population."
        ).font.size = Pt(8.5)
        p_app.runs[0].font.italic = True
        p_app.runs[0].font.color.rgb = RGBColor(100, 116, 139)

        # Save to buffer
        doc_stream = io.BytesIO()
        doc.save(doc_stream)
        return doc_stream.getvalue()

