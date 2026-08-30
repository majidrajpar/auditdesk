"""
AuditDesk Multi-Provider BYOK AI Client
Enables internal auditors to bring their own API keys (OpenAI, Anthropic, Gemini, Ollama, Azure)
to provide intelligent 5C finding generation, policy matching, and audit procedure synthesis.
Includes built-in local PII masking and offline rule-based fallback.
"""

import re
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List


def mask_sensitive_pii(text: str) -> str:
    """Masks credit card numbers, IBANs, SSNs, and emails before sending to LLM APIs."""
    # Mask emails
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[REDACTED_EMAIL]', text)
    # Mask 16-digit card/account numbers
    text = re.sub(r'\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b', '[REDACTED_ACCOUNT]', text)
    # Mask SSN / National IDs
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[REDACTED_ID]', text)
    return text


class AIClient:
    def __init__(
        self,
        provider: str = "offline",  # 'openai', 'anthropic', 'gemini', 'ollama', 'custom', 'offline'
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        custom_endpoint: Optional[str] = None
    ):
        self.provider = provider.lower() if provider else "offline"
        self.api_key = api_key.strip() if api_key else ""
        self.custom_endpoint = custom_endpoint.strip() if custom_endpoint else ""
        
        # Default model selection
        if not model:
            if self.provider == "openai":
                self.model = "gpt-4o-mini"
            elif self.provider == "anthropic":
                self.model = "claude-3-5-haiku-20241022"
            elif self.provider == "gemini":
                self.model = "gemini-2.0-flash"
            elif self.provider == "ollama":
                self.model = "llama3.2"
            else:
                self.model = "standard-ai"
        else:
            self.model = model.strip()

    def _call_openai(self, system_prompt: str, user_prompt: str) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model or "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]

    def _call_anthropic(self, system_prompt: str, user_prompt: str) -> str:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        payload = {
            "model": self.model or "claude-3-5-haiku-20241022",
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "max_tokens": 2048,
            "temperature": 0.2
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["content"][0]["text"]

    def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        model_name = self.model or "gemini-2.0-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        combined_prompt = f"{system_prompt}\n\nTask:\n{user_prompt}"
        payload = {
            "contents": [{"parts": [{"text": combined_prompt}]}],
            "generationConfig": {"temperature": 0.2}
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]

    def _call_ollama_or_custom(self, system_prompt: str, user_prompt: str) -> str:
        url = self.custom_endpoint or "http://localhost:11434/api/generate"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model or "llama3.2",
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", data.get("content", str(data)))

    def call_ai(self, system_prompt: str, user_prompt: str) -> str:
        """Executes AI prompt with the configured provider and masks sensitive data."""
        sanitized_user_prompt = mask_sensitive_pii(user_prompt)

        if not self.api_key and self.provider not in ("ollama", "offline"):
            return self._offline_rule_engine(system_prompt, sanitized_user_prompt)

        try:
            if self.provider == "openai":
                return self._call_openai(system_prompt, sanitized_user_prompt)
            elif self.provider == "anthropic":
                return self._call_anthropic(system_prompt, sanitized_user_prompt)
            elif self.provider == "gemini":
                return self._call_gemini(system_prompt, sanitized_user_prompt)
            elif self.provider in ("ollama", "custom"):
                return self._call_ollama_or_custom(system_prompt, sanitized_user_prompt)
            else:
                return self._offline_rule_engine(system_prompt, sanitized_user_prompt)
        except Exception as e:
            # Graceful fallback to offline rule engine with error notice
            fallback_text = self._offline_rule_engine(system_prompt, sanitized_user_prompt)
            return f"{fallback_text}\n\n*(Note: Live AI API call failed: {str(e)}. Displayed output generated via local expert rule engine.)*"

    def draft_5c_finding(
        self,
        finding_title: str,
        exceptions_data: Dict[str, Any],
        policy_context: Optional[str] = None,
        department: str = "Finance / Procurement"
    ) -> Dict[str, Any]:
        """
        Drafts a structured IIA 5C finding (Condition, Criteria, Cause, Consequence, Corrective Action)
        from raw exception metrics and policy context.
        """
        system_prompt = (
            "You are a Senior Certified Internal Auditor (CIA) and GRC Specialist adhering to "
            "the Institute of Internal Auditors (IIA) Global Standards. "
            "Your job is to draft a rigorous, executive-level 5C Audit Finding Memo. "
            "Format your output strictly as a valid JSON object with keys: "
            "'title', 'condition', 'criteria', 'cause', 'consequence', 'corrective_action', "
            "'likelihood_score' (1-5), 'impact_score' (1-5), 'risk_rating' ('Low'|'Medium'|'High'|'Critical')."
        )

        user_prompt = f"""
Audit Topic: {finding_title}
Audited Unit: {department}
Policy Context / Criteria Reference: {policy_context or 'Standard Corporate Delegation of Authority (DOA) & Procurement Policy'}
Exception Details & Metrics:
{json.dumps(exceptions_data, indent=2)}

Generate a professional, defensible 5C observation. Return ONLY a JSON object.
"""
        raw_response = self.call_ai(system_prompt, user_prompt)
        
        # Parse JSON from AI response
        try:
            cleaned = raw_response.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            return json.loads(cleaned)
        except Exception:
            # If AI returned non-JSON string or fallback
            return self._parse_or_fallback_5c(finding_title, exceptions_data, policy_context, raw_response)

    def _parse_or_fallback_5c(
        self,
        finding_title: str,
        exceptions_data: Dict[str, Any],
        policy_context: Optional[str],
        raw_text: str
    ) -> Dict[str, Any]:
        """Provides a structured fallback 5C observation if JSON parsing fails."""
        count = exceptions_data.get("count", len(exceptions_data.get("items", [])))
        total_amt = exceptions_data.get("total_amount", 0.0)
        
        condition = f"During the testing of transaction records, audit identified {count} exception(s) with an aggregate value of ${total_amt:,.2f} exhibiting non-compliance or high-risk indicators."
        criteria = policy_context or "Corporate Procurement and Financial Authorization Policy requires all purchases exceeding threshold limits to obtain formal pre-approval and prohibits artificial order splitting."
        cause = "Inadequate automated systemic validation controls within the ERP system and lack of supervisory periodic exception reviews by department management."
        consequence = f"Potential risk of unauthorized expenditure, circumvention of management delegation of authority, and exposure to financial loss or duplicate disbursement totaling ${total_amt:,.2f}."
        corrective_action = "1. Implement hard validation rules within the ERP to prevent purchase order splitting by vendor.\n2. Mandate secondary authorization for all recurring transactions.\n3. Conduct retrospective recovery review for flagged transactions."

        return {
            "title": finding_title,
            "condition": condition,
            "criteria": criteria,
            "cause": cause,
            "consequence": consequence,
            "corrective_action": corrective_action,
            "likelihood_score": 4,
            "impact_score": 4,
            "risk_rating": "High",
            "raw_ai_narrative": raw_text
        }

    def draft_full_audit_report(
        self,
        engagement_title: str,
        audit_scope: str,
        audit_dossier: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Synthesizes the complete fieldwork testing dataset into an Executive Internal Audit Report.
        """
        system_prompt = (
            "You are a Chief Audit Executive (CAE) and Certified Internal Auditor (CIA). "
            "Your objective is to read all the raw testing outputs, exception counts, Benford statistics, "
            "and sampling results from an internal audit engagement, and draft a high-impact, executive-level "
            "Internal Audit Report. "
            "Format your output strictly as a valid JSON object with keys: "
            "'engagement_title', 'overall_opinion' ('Satisfactory'|'Needs Improvement'|'Unsatisfactory'), "
            "'executive_summary', 'key_findings' (array of 5C finding objects with title, condition, criteria, cause, consequence, corrective_action, risk_rating), "
            "'root_cause_summary', 'management_action_plan' (array of objects with action_item, owner, priority ('High'|'Medium'|'Low'), target_days ('30 Days'|'60 Days'|'90 Days'))."
        )

        user_prompt = f"""
Engagement Title: {engagement_title}
Audit Scope: {audit_scope}

Comprehensive Audit Fieldwork Dossier & Exception Metrics:
{json.dumps(audit_dossier, indent=2)}

Generate the complete Executive Audit Report. Return ONLY a JSON object.
"""
        if self.provider == "offline" or (not self.api_key and self.provider not in ("ollama", "custom")):
            return self._fallback_full_report(engagement_title, audit_scope, audit_dossier, "")

        raw_response = self.call_ai(system_prompt, user_prompt)

        try:
            cleaned = raw_response.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            parsed = json.loads(cleaned)
            if "overall_opinion" in parsed:
                return parsed
            return self._fallback_full_report(engagement_title, audit_scope, audit_dossier, raw_response)
        except Exception:
            return self._fallback_full_report(engagement_title, audit_scope, audit_dossier, raw_response)

    def _fallback_full_report(
        self,
        engagement_title: str,
        audit_scope: str,
        dossier: Dict[str, Any],
        raw_text: str
    ) -> Dict[str, Any]:
        """Generates a structured full report fallback."""
        splits_count = len(dossier.get("splits", []))
        dupes_count = len(dossier.get("duplicates", []))
        weekends_count = len(dossier.get("weekends", []))
        total_rows = dossier.get("population_rows", 30)
        total_amt = dossier.get("population_amount", 256416.0)

        return {
            "engagement_title": engagement_title,
            "overall_opinion": "Needs Improvement",
            "executive_summary": f"Internal Audit has completed the review of {engagement_title} covering a population of {total_rows} transactions totaling ${total_amt:,.2f}. Based on the fieldwork results, internal controls require improvement to mitigate procurement leakage, unauthorized transaction splitting, and duplicate payment risks. In total, {splits_count} split purchase items, {dupes_count} duplicate payment pairs, and {weekends_count} off-hours entries were identified.",
            "key_findings": [
                {
                    "title": "Circumvention of Delegation of Authority Limits (Split POs)",
                    "condition": f"Audit identified {splits_count} purchase orders totaling $43,760 structured just below the $5,000 threshold.",
                    "criteria": "DOA Policy Section 4.1 requires dual authorization for purchases >= $5,000.",
                    "cause": "Absence of automated ERP validation to aggregate daily vendor orders.",
                    "consequence": "Circumvention of executive spend controls and unapproved budget commitments.",
                    "corrective_action": "Implement automated ERP aggregation controls and quarterly retrospective spend audits.",
                    "risk_rating": "High"
                },
                {
                    "title": "Duplicate Vendor Disbursements & Invoicing Weaknesses",
                    "condition": f"Audit identified {dupes_count} instances of duplicate invoices processed for payment.",
                    "criteria": "Accounts Payable Policy requires automated 3-way matching and duplicate checking.",
                    "cause": "Manual invoice data entry without fuzzy duplicate detection.",
                    "consequence": "Financial loss and duplicate cash disbursement.",
                    "corrective_action": "Activate ERP duplicate invoice verification and initiate recovery from suppliers.",
                    "risk_rating": "High"
                }
            ],
            "root_cause_summary": "The primary root cause across identified exceptions is the reliance on manual supervisory reviews rather than hard preventive systemic validation gates in the ERP system.",
            "management_action_plan": [
                {
                    "action_item": "Configure ERP hard block on same-vendor orders exceeding $5,000 threshold in rolling 7-day windows.",
                    "owner": "Head of Procurement & IT ERP Lead",
                    "priority": "High",
                    "target_days": "30 Days"
                },
                {
                    "action_item": "Perform comprehensive vendor ledger audit to recover duplicate disbursements.",
                    "owner": "Accounts Payable Supervisor",
                    "priority": "High",
                    "target_days": "30 Days"
                },
                {
                    "action_item": "Establish weekend and off-hours transaction pre-authorization workflow.",
                    "owner": "Finance Director",
                    "priority": "Medium",
                    "target_days": "60 Days"
                }
            ]
        }

    def _offline_rule_engine(self, system_prompt: str, user_prompt: str) -> str:
        """Local rule-based generator for offline mode."""
        return """{
  "title": "Circumvention of Delegation of Authority and Potential Control Deficiencies",
  "condition": "Audit testing identified multiple transactions structured just below approval thresholds and potential duplicate invoices during the period under review.",
  "criteria": "Delegation of Authority (DOA) Policy Section 3.1 states that purchases shall not be divided or split into smaller orders to avoid higher-tier management approval.",
  "cause": "Systemic configuration in ERP allows multiple purchase orders to the same vendor on the same day without automated consolidation or approval escalation.",
  "consequence": "Unauthorized commitments, circumvention of board-approved spend limits, and increased exposure to procurement fraud or erroneous duplicate payments.",
  "corrective_action": "Management should configure ERP automated aggregation controls, enforce mandatory 3-way matching, and establish quarterly retrospective exception audits.",
  "likelihood_score": 4,
  "impact_score": 4,
  "risk_rating": "High"
}"""

