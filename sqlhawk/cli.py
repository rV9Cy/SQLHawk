# -*- coding: utf-8 -*-
"""
SQLHawk CLI
===========
Interactive usage (recommended):
    python -m sqlhawk.cli
    (starts, asks Farsi/English, then asks for the target link)

Non-interactive / scripted usage:
    python -m sqlhawk.cli --url https://target.example --output report.html -y --lang en
"""

from __future__ import annotations

import argparse
import os
import sys
import urllib.parse as urlparse

from sqlhawk import __version__
from sqlhawk.crawler.crawler import Crawler
from sqlhawk.i18n import t, set_rtl_fix
from sqlhawk.injector.injector import Injector
from sqlhawk.report.report import save_report

CREATOR = "rV8Cy"

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    _C = True
except ImportError:  # colorama is optional - tool still works without color
    _C = False

    class _NoColor:
        def __getattr__(self, _):
            return ""
    Fore = Style = _NoColor()

# Only two colors are used anywhere in this tool: cyan for information,
# green for success. No red/yellow anywhere, on purpose.
INFO = Fore.CYAN
OK = Fore.GREEN


def _c(text: str, color: str) -> str:
    return f"{color}{text}{Style.RESET_ALL}" if _C else text


def clear_screen():
    """Clear the terminal so only the SQLHawk screen is visible."""
    os.system("cls" if os.name == "nt" else "clear")


ASCII_BANNER = r"""
   _____  ____  _      _   _                _
  / ____|/ __ \| |    | | | |              | |
 | (___ | |  | | |    | |_| | __ ___      _| | __
  \___ \| |  | | |    |  _  |/ _` \ \ /\ / / |/ /
  ____) | |__| | |____| | | | (_| |\ V  V /|   <
 |_____/ \___\_\______|_| |_|\__,_| \_/\_/ |_|\_\
"""


def ask_language() -> str:
    """Language choice is asked in English, before anything else."""
    while True:
        choice = input("Farsi | English ? (F/E): ").strip().lower()
        if choice in ("f", "farsi"):
            return "fa"
        if choice in ("e", "english"):
            return "en"
        print("Please type F or E.")


def print_banner(lang: str):
    print(_c(ASCII_BANNER, INFO))
    print(_c("        " + t("banner_subtitle", lang, version=__version__), INFO))
    print(_c("        " + t("banner_creator", lang, creator=CREATOR), INFO))
    print(_c("        github.com/yourusername/sqlhawk\n", INFO))


def ask_for_url(lang: str) -> str:
    while True:
        raw = input(t("ask_url", lang)).strip()
        if not raw:
            print(t("url_empty", lang))
            continue
        if not raw.startswith(("http://", "https://")):
            raw = "https://" + raw
        parsed = urlparse.urlparse(raw)
        if parsed.scheme and parsed.netloc:
            return raw
        print(t("url_invalid", lang))


def run_scan(lang: str, url: str, output: str, max_pages: int, delay: int):
    print(_c(t("crawling", lang, url=url, max_pages=max_pages), INFO))
    crawler = Crawler(url, max_pages=max_pages)
    result = crawler.crawl()
    print(_c(t("crawl_summary", lang, forms=len(result.forms),
                params=len(result.params), pages=len(result.visited)), INFO))

    injector = Injector(delay_seconds=delay)
    findings = []

    for i, form in enumerate(result.forms, 1):
        print(t("testing_form", lang, i=i, total=len(result.forms), action=form.action))
        findings.extend(injector.scan_form(form))

    for i, param in enumerate(result.params, 1):
        print(t("testing_param", lang, i=i, total=len(result.params),
                 param=param.param, url=param.url))
        findings.extend(injector.scan_param(param))

    print(_c(t("scan_complete", lang, count=len(findings)), OK))
    save_report(url, findings, output, lang=lang)
    print(_c(t("report_saved", lang, path=output), OK))


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="sqlhawk",
        description="Multi-language SQL injection detection scanner "
                    "for authorized security testing.",
    )
    parser.add_argument("--url", default=None, help="Target base URL (optional - if omitted, the tool asks for it interactively)")
    parser.add_argument("--output", default="sqlhawk_report.html", help="Path to write the HTML report")
    parser.add_argument("--max-pages", type=int, default=25, help="Max pages to crawl")
    parser.add_argument("--delay", type=int, default=5, help="Seconds used for time-based SQLi probes")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip the interactive authorization prompt")
    parser.add_argument("--no-banner", action="store_true", help="Suppress the ASCII banner / screen clear")
    parser.add_argument("--no-loop", action="store_true", help="Exit after one scan instead of asking for another link")
    parser.add_argument("--lang", choices=["fa", "en"], default=None, help="UI language (skips the Farsi/English prompt)")
    parser.add_argument("--no-rtl-fix", action="store_true",
                         help="Disable manual RTL shaping/reordering (use on terminals that already render Persian correctly, e.g. most desktop terminals)")
    args = parser.parse_args(argv)

    if args.no_rtl_fix:
        set_rtl_fix(False)

    if not args.no_banner:
        clear_screen()

    lang = args.lang or ask_language()

    if not args.no_banner:
        clear_screen()
    print_banner(lang)
    print(t("legal_banner", lang))
    if not args.yes:
        confirm = input(t("confirm_prompt", lang))
        if confirm.strip().upper() != "YES":
            print(_c(t("cancelled", lang), INFO))
            sys.exit(1)
    print()

    # Non-interactive / scripted path: --url was passed on the command line.
    if args.url:
        parsed = urlparse.urlparse(args.url)
        if not parsed.scheme or not parsed.netloc:
            print(t("url_missing_cli", lang))
            sys.exit(1)
        run_scan(lang, args.url, args.output, args.max_pages, args.delay)
        return

    # Interactive path (default): ask for the link, scan, then offer to
    # scan another one (loops by default; --no-loop exits after one run).
    while True:
        url = ask_for_url(lang)
        print()
        run_scan(lang, url, args.output, args.max_pages, args.delay)
        if args.no_loop:
            break
        print()
        again = input(_c(t("ask_again", lang), INFO)).strip().lower()
        if again != "y":
            break
        print()


if __name__ == "__main__":
    main()
