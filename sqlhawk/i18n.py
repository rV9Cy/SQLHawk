# -*- coding: utf-8 -*-
"""
SQLHawk i18n
============
Two things happen here:

1. All user-facing strings live in one place, in English and Persian.

2. Persian/Arabic-script text needs two extra steps before it will
   display correctly in most terminals (including Termux's default
   terminal):

     - "reshaping": Persian letters change visual form depending on
       their position in a word (isolated/initial/medial/final). A
       plain Python string just has the isolated form of each letter,
       which is why it shows up as disconnected, wrong-looking glyphs.
     - "bidi reordering": terminals that don't implement the Unicode
       Bidirectional Algorithm print RTL text in logical (storage)
       order instead of visual order, which is why it can look
       reversed.

   `arabic_reshaper` + `python-bidi` would normally fix both, but they
   require extra pip packages that may not always be installable
   (e.g. offline, or a restricted mirror). Instead, SQLHawk ships its
   own tiny dependency-free implementation (see `sqlhawk/rtl.py`) that
   does the same two steps for the fixed set of UI strings below, so
   it always works out of the box - including on Termux.
"""

from __future__ import annotations

from sqlhawk.rtl import fix_rtl

_RTL_FIX_ENABLED = True


def set_rtl_fix(enabled: bool) -> None:
    """Call with False on terminals that already render Persian/Arabic
    bidi + shaping correctly on their own (most desktop terminals) -
    otherwise this module's own fix would double-flip the text."""
    global _RTL_FIX_ENABLED
    _RTL_FIX_ENABLED = enabled


def to_display(text: str) -> str:
    return fix_rtl(text) if _RTL_FIX_ENABLED else text


STRINGS = {
    "banner_subtitle": {
        "en": "Multi-language Database Vulnerability Scanner  |  v{version}",
        "fa": "اسکنر شناسایی آسیب‌پذیری دیتابیس (چندزبانه)  |  نسخه {version}",
    },
    "banner_creator": {
        "en": "Creator: {creator}",
        "fa": "سازنده: {creator}",
    },
    "lang_prompt": {
        "en": "Farsi | English ? (F/E): ",
        "fa": "Farsi | English ? (F/E): ",  # asked before language is chosen, always English
    },
    "lang_invalid": {
        "en": "Please type F or E.",
        "fa": "Please type F or E.",
    },
    "legal_banner": {
        "en": (
            "==============================================================\n"
            " This tool actively sends test payloads to the target and is\n"
            " intended ONLY for:\n"
            "\n"
            "   - systems or sites you own\n"
            "   - authorized penetration tests (signed agreement)\n"
            "   - official bug bounty programs (HackerOne / Bugcrowd) where\n"
            "     the target is explicitly in scope\n"
            "\n"
            " Scanning systems without permission is a crime in most\n"
            " countries. By continuing, you confirm you are authorized to\n"
            " test this target.\n"
            "=============================================================="
        ),
        "fa": (
            "==============================================================\n"
            " این ابزار به صورت فعال برای هدف موردنظر درخواست های تستی\n"
            " ارسال می کند و فقط برای موارد زیر مجاز است:\n"
            "\n"
            "   - سیستم ها یا سایت هایی که خودتان مالک آن ها هستید\n"
            "   - تست نفوذ مجاز (با قرارداد و توافق کتبی)\n"
            "   - برنامه های رسمی باگ بانتی (HackerOne / Bugcrowd) که هدف\n"
            "     به صراحت در محدوده ی مجاز آن قرار دارد\n"
            "\n"
            " اسکن سیستم ها بدون اجازه در اکثر کشورها جرم محسوب می شود.\n"
            " با ادامه دادن، تایید می کنید که مجوز لازم برای تست این هدف\n"
            " را دارید.\n"
            "=============================================================="
        ),
    },
    "confirm_prompt": {
        "en": "Type YES to confirm you are authorized to test: ",
        "fa": "برای تایید مجوز تست، عبارت YES را تایپ کنید: ",
    },
    "cancelled": {
        "en": "Cancelled.",
        "fa": "لغو شد.",
    },
    "ask_url": {
        "en": "Enter the target link to analyze: ",
        "fa": "لینک سایت مورد نظر برای آنالیز را وارد کنید: ",
    },
    "url_empty": {
        "en": "The link cannot be empty.",
        "fa": "لینک نمی‌تواند خالی باشد.",
    },
    "url_invalid": {
        "en": "Invalid link, try again (e.g. https://panel.example.com/)",
        "fa": "لینک نامعتبر است، دوباره تلاش کنید (مثل https://panel.example.com/)",
    },
    "url_missing_cli": {
        "en": "Error: --url must be a full URL, e.g. https://panel.example.com/",
        "fa": "خطا: آدرس --url باید کامل باشد، مثل https://panel.example.com/",
    },
    "crawling": {
        "en": "[*] Crawling {url} (max {max_pages} pages)...",
        "fa": "[*] در حال بررسی و خزیدن در {url} (حداکثر {max_pages} صفحه)...",
    },
    "crawl_summary": {
        "en": "[*] Found {forms} form(s) and {params} URL parameter(s) across {pages} page(s).",
        "fa": "[*] {forms} فرم و {params} پارامتر URL در {pages} صفحه پیدا شد.",
    },
    "testing_form": {
        "en": "[*] Testing form {i}/{total}: {action}",
        "fa": "[*] در حال تست فرم {i}/{total}: {action}",
    },
    "testing_param": {
        "en": "[*] Testing parameter {i}/{total}: {param} @ {url}",
        "fa": "[*] در حال تست پارامتر {i}/{total}: {param} @ {url}",
    },
    "scan_complete": {
        "en": "[*] Scan complete. {count} potential issue(s) found.",
        "fa": "[*] اسکن تمام شد. {count} مورد مشکوک پیدا شد.",
    },
    "report_saved": {
        "en": "[+] Report saved to: {path}",
        "fa": "[+] گزارش ذخیره شد در: {path}",
    },
    "ask_again": {
        "en": "Analyze another link? (y/n): ",
        "fa": "می‌خواهید لینک دیگری را آنالیز کنید؟ (y/n): ",
    },
}


def t(key: str, lang: str, **kwargs) -> str:
    """Look up a string by key/lang, format it, and reshape it for
    terminal display if it's Persian."""
    template = STRINGS[key][lang]
    text = template.format(**kwargs) if kwargs else template
    if lang == "fa":
        # Reshape line-by-line so ASCII/URLs mixed into a Persian
        # sentence still line up correctly, and multi-line legal
        # banners keep their line breaks.
        return "\n".join(to_display(line) if line.strip() else line
                          for line in text.split("\n"))
    return text
