"""
SQLHawk Crawler
================
Walks a target site (within the same domain) and collects every
injectable surface it can find:

  - <form> elements (action, method, input names)
  - URL query-string parameters found in <a href="...">

This is intentionally conservative: it will NOT follow links to other
domains, and it respects a max-page / max-depth limit so it can't be
used to accidentally hammer a huge site.

Legal note: only ever point this at a target you own or that has
explicitly authorized testing (bug bounty scope, signed pentest
agreement, or your own local lab like DVWA/bWAPP/Metasploitable).
"""

from __future__ import annotations

import urllib.parse as urlparse
from dataclasses import dataclass, field
from typing import Optional

import requests
from bs4 import BeautifulSoup


@dataclass
class FormTarget:
    url: str
    method: str
    inputs: list[str]
    action: str


@dataclass
class ParamTarget:
    url: str
    param: str


@dataclass
class CrawlResult:
    forms: list[FormTarget] = field(default_factory=list)
    params: list[ParamTarget] = field(default_factory=list)
    visited: set[str] = field(default_factory=set)


class Crawler:
    def __init__(
        self,
        base_url: str,
        max_pages: int = 40,
        timeout: int = 10,
        session: Optional[requests.Session] = None,
        user_agent: str = "SQLHawk/0.1 (+authorized-security-testing)",
    ):
        self.base_url = base_url.rstrip("/")
        self.domain = urlparse.urlparse(base_url).netloc
        self.max_pages = max_pages
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def _same_domain(self, url: str) -> bool:
        return urlparse.urlparse(url).netloc in ("", self.domain)

    def _extract_forms(self, html: str, page_url: str) -> list[FormTarget]:
        soup = BeautifulSoup(html, "html.parser")
        forms = []
        for form in soup.find_all("form"):
            action = form.get("action") or page_url
            full_action = urlparse.urljoin(page_url, action)
            method = (form.get("method") or "get").lower()
            inputs = []
            for tag in form.find_all(["input", "textarea", "select"]):
                name = tag.get("name")
                if name:
                    inputs.append(name)
            if inputs:
                forms.append(FormTarget(url=page_url, method=method,
                                         inputs=inputs, action=full_action))
        return forms

    def _extract_link_params(self, html: str, page_url: str) -> list[ParamTarget]:
        soup = BeautifulSoup(html, "html.parser")
        results = []
        for a in soup.find_all("a", href=True):
            full = urlparse.urljoin(page_url, a["href"])
            parsed = urlparse.urlparse(full)
            qs = urlparse.parse_qs(parsed.query)
            for param in qs:
                results.append(ParamTarget(url=full, param=param))
        return results

    def _extract_links(self, html: str, page_url: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for a in soup.find_all("a", href=True):
            full = urlparse.urljoin(page_url, a["href"])
            full = full.split("#")[0]
            if self._same_domain(full):
                links.append(full)
        return links

    def crawl(self) -> CrawlResult:
        result = CrawlResult()
        queue = [self.base_url]

        while queue and len(result.visited) < self.max_pages:
            url = queue.pop(0)
            if url in result.visited:
                continue
            result.visited.add(url)

            try:
                resp = self.session.get(url, timeout=self.timeout)
            except requests.RequestException:
                continue

            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                continue

            result.forms.extend(self._extract_forms(resp.text, url))
            result.params.extend(self._extract_link_params(resp.text, url))

            for link in self._extract_links(resp.text, url):
                if link not in result.visited:
                    queue.append(link)

        return result
