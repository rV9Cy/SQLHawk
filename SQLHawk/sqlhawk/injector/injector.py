"""
SQLHawk Injector
================
Takes crawl targets (forms + URL params) and tests each injectable
field with three detection techniques:

  1. Error-based   -> look for a DB error signature in the response
  2. Boolean-based  -> compare response for a TRUE vs FALSE condition
  3. Time-based     -> compare response time for a delayed payload
                        vs a baseline request

Each finding is returned as a Finding object consumed by report.py.
"""

from __future__ import annotations

import time
import urllib.parse as urlparse
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Optional

import requests

from sqlhawk.analyzer.signatures import identify_database
from sqlhawk.crawler.crawler import FormTarget, ParamTarget
from sqlhawk.injector.payloads import (
    BOOLEAN_FALSE_PAYLOAD,
    BOOLEAN_TRUE_PAYLOAD,
    ERROR_BASED_PAYLOADS,
    TIME_BASED_PAYLOADS,
)

SEVERITY_ORDER = {"Critical": 3, "High": 2, "Medium": 1, "Low": 0}


@dataclass
class Finding:
    url: str
    parameter: str
    method: str
    technique: str          # error-based / boolean-based / time-based
    payload: str
    db_engine: Optional[str]
    severity: str            # Critical / High / Medium / Low
    evidence: str
    remediation: str = field(default="")

    def __post_init__(self):
        if not self.remediation:
            self.remediation = (
                "Use parameterized queries / prepared statements instead of "
                "concatenating user input into SQL. Apply least-privilege "
                "DB accounts and validate/allow-list input server-side."
            )


class Injector:
    def __init__(
        self,
        session: Optional[requests.Session] = None,
        timeout: int = 10,
        delay_seconds: int = 5,
        similarity_threshold: float = 0.92,
    ):
        self.session = session or requests.Session()
        self.timeout = timeout
        self.delay_seconds = delay_seconds
        self.similarity_threshold = similarity_threshold

    # ---------- shared helpers ----------

    def _similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    def _send_form(self, form: FormTarget, field_name: str, value: str):
        data = {name: (value if name == field_name else "test")
                 for name in form.inputs}
        if form.method == "post":
            return self.session.post(form.action, data=data, timeout=self.timeout)
        return self.session.get(form.action, params=data, timeout=self.timeout)

    def _send_param(self, target: ParamTarget, value: str):
        parsed = urlparse.urlparse(target.url)
        qs = urlparse.parse_qs(parsed.query)
        qs[target.param] = value
        new_query = urlparse.urlencode(qs, doseq=True)
        new_url = urlparse.urlunparse(parsed._replace(query=new_query))
        return self.session.get(new_url, timeout=self.timeout)

    # ---------- detection techniques ----------

    def test_error_based(self, url: str, method: str, field_name: str,
                          sender) -> Optional[Finding]:
        for payload in ERROR_BASED_PAYLOADS:
            try:
                resp = sender(payload)
            except requests.RequestException:
                continue
            db = identify_database(resp.text)
            if db:
                return Finding(
                    url=url, parameter=field_name, method=method,
                    technique="Error-based SQL Injection", payload=payload,
                    db_engine=db, severity="Critical",
                    evidence=f"Database error signature for {db} found in response.",
                )
        return None

    def test_boolean_based(self, url: str, method: str, field_name: str,
                            sender) -> Optional[Finding]:
        try:
            baseline = sender("test")
            true_resp = sender(BOOLEAN_TRUE_PAYLOAD)
            false_resp = sender(BOOLEAN_FALSE_PAYLOAD)
        except requests.RequestException:
            return None

        true_vs_base = self._similarity(true_resp.text, baseline.text)
        false_vs_base = self._similarity(false_resp.text, baseline.text)

        # If TRUE payload looks like baseline but FALSE payload differs
        # meaningfully, the page is behaving differently based on the
        # injected boolean condition -> likely blind SQLi.
        if true_vs_base > self.similarity_threshold and \
           false_vs_base < self.similarity_threshold - 0.05:
            return Finding(
                url=url, parameter=field_name, method=method,
                technique="Boolean-based Blind SQL Injection",
                payload=f"{BOOLEAN_TRUE_PAYLOAD}  /  {BOOLEAN_FALSE_PAYLOAD}",
                db_engine=None, severity="High",
                evidence=(
                    f"TRUE payload similarity to baseline: {true_vs_base:.2f}, "
                    f"FALSE payload similarity: {false_vs_base:.2f}."
                ),
            )
        return None

    def test_time_based(self, url: str, method: str, field_name: str,
                         sender) -> Optional[Finding]:
        for engine, template in TIME_BASED_PAYLOADS.items():
            payload = template % self.delay_seconds
            try:
                start = time.monotonic()
                sender(payload)
                elapsed = time.monotonic() - start
            except requests.RequestException:
                continue

            if elapsed >= self.delay_seconds - 1:
                return Finding(
                    url=url, parameter=field_name, method=method,
                    technique="Time-based Blind SQL Injection",
                    payload=payload,
                    db_engine=None if engine == "Generic" else engine,
                    severity="High",
                    evidence=f"Response delayed by ~{elapsed:.1f}s for a "
                              f"{self.delay_seconds}s sleep payload.",
                )
        return None

    # ---------- orchestration ----------

    def scan_form(self, form: FormTarget) -> list[Finding]:
        findings = []
        for field_name in form.inputs:
            def sender(value, f=field_name):
                return self._send_form(form, f, value)

            for test in (self.test_error_based, self.test_boolean_based,
                         self.test_time_based):
                result = test(form.action, form.method, field_name, sender)
                if result:
                    findings.append(result)
                    break  # one confirmed technique per field is enough
        return findings

    def scan_param(self, target: ParamTarget) -> list[Finding]:
        def sender(value):
            return self._send_param(target, value)

        for test in (self.test_error_based, self.test_boolean_based,
                     self.test_time_based):
            result = test(target.url, "get", target.param, sender)
            if result:
                return [result]
        return []
