# -*- coding: utf-8 -*-
"""
Minimal, dependency-free Arabic/Persian letter shaping + visual reordering.

Why this exists
----------------
Some terminals (notably the default Termux terminal app on Android) do not
implement the Unicode Bidirectional Algorithm or Arabic letter shaping. When
you print Persian text there, you get the raw, unconnected, logical-order
characters, which show up jumbled/disconnected/reversed on screen.

Desktop terminals that DO implement bidi+shaping correctly (most Linux
terminal emulators, iTerm2, Windows Terminal, etc.) will already render
Persian correctly on their own. Running this "fix" there would double-flip
the text and make it look wrong. That's why the CLI exposes
`--no-rtl-fix` to turn this off on a terminal that already handles it.

Approach (the same trick used by classic console Farsi/Arabic tools like
`bidiv` before real bidi terminal support existed):
  1. Shape each Arabic/Persian letter into its correct isolated / initial /
     medial / final presentation form based on its logical neighbors.
  2. Split the line into whitespace-separated words.
  3. Reverse the ORDER of the words (RTL word order).
  4. Reverse the CHARACTER order within each word that is Persian/Arabic
     script (so a naive left-to-right-only renderer draws it correctly).
     Words that are Latin/digits (URLs, "YES", version numbers, etc.) are
     left untouched internally - only their position in the line changes.

Letter shaping table sourced from the standard Unicode Arabic Presentation
Forms-A/B blocks (the same data used by the widely-used python-arabic-reshaper
project), covering the Persian alphabet plus the extra Persian letters
(pe, che, zhe, gaf) not present in standard Arabic.
"""

from __future__ import annotations

ISOLATED, INITIAL, MEDIAL, FINAL = 0, 1, 2, 3

# '<letter>': (isolated, initial, medial, final) - '' means the letter
# does not take that form (e.g. alef/dal/reh/waw/zhe never connect forward).
LETTERS: dict[str, tuple[str, str, str, str]] = {
    "\u0621": ("\uFE80", "", "", ""),                              # ء hamza
    "\u0622": ("\uFE81", "", "", "\uFE82"),                        # آ
    "\u0623": ("\uFE83", "", "", "\uFE84"),                        # أ
    "\u0624": ("\uFE85", "", "", "\uFE86"),                        # ؤ
    "\u0625": ("\uFE87", "", "", "\uFE88"),                        # إ
    "\u0626": ("\uFE89", "\uFE8B", "\uFE8C", "\uFE8A"),            # ئ
    "\u0627": ("\uFE8D", "", "", "\uFE8E"),                        # ا
    "\u0628": ("\uFE8F", "\uFE91", "\uFE92", "\uFE90"),            # ب
    "\u0629": ("\uFE93", "", "", "\uFE94"),                        # ة
    "\u062A": ("\uFE95", "\uFE97", "\uFE98", "\uFE96"),            # ت
    "\u062B": ("\uFE99", "\uFE9B", "\uFE9C", "\uFE9A"),            # ث
    "\u062C": ("\uFE9D", "\uFE9F", "\uFEA0", "\uFE9E"),            # ج
    "\u062D": ("\uFEA1", "\uFEA3", "\uFEA4", "\uFEA2"),            # ح
    "\u062E": ("\uFEA5", "\uFEA7", "\uFEA8", "\uFEA6"),            # خ
    "\u062F": ("\uFEA9", "", "", "\uFEAA"),                        # د
    "\u0630": ("\uFEAB", "", "", "\uFEAC"),                        # ذ
    "\u0631": ("\uFEAD", "", "", "\uFEAE"),                        # ر
    "\u0632": ("\uFEAF", "", "", "\uFEB0"),                        # ز
    "\u0633": ("\uFEB1", "\uFEB3", "\uFEB4", "\uFEB2"),            # س
    "\u0634": ("\uFEB5", "\uFEB7", "\uFEB8", "\uFEB6"),            # ش
    "\u0635": ("\uFEB9", "\uFEBB", "\uFEBC", "\uFEBA"),            # ص
    "\u0636": ("\uFEBD", "\uFEBF", "\uFEC0", "\uFEBE"),            # ض
    "\u0637": ("\uFEC1", "\uFEC3", "\uFEC4", "\uFEC2"),            # ط
    "\u0638": ("\uFEC5", "\uFEC7", "\uFEC8", "\uFEC6"),            # ظ
    "\u0639": ("\uFEC9", "\uFECB", "\uFECC", "\uFECA"),            # ع
    "\u063A": ("\uFECD", "\uFECF", "\uFED0", "\uFECE"),            # غ
    "\u0640": ("\u0640", "\u0640", "\u0640", "\u0640"),            # tatweel
    "\u0641": ("\uFED1", "\uFED3", "\uFED4", "\uFED2"),            # ف
    "\u0642": ("\uFED5", "\uFED7", "\uFED8", "\uFED6"),            # ق
    "\u0643": ("\uFED9", "\uFEDB", "\uFEDC", "\uFEDA"),            # ك
    "\u0644": ("\uFEDD", "\uFEDF", "\uFEE0", "\uFEDE"),            # ل
    "\u0645": ("\uFEE1", "\uFEE3", "\uFEE4", "\uFEE2"),            # م
    "\u0646": ("\uFEE5", "\uFEE7", "\uFEE8", "\uFEE6"),            # ن
    "\u0647": ("\uFEE9", "\uFEEB", "\uFEEC", "\uFEEA"),            # ه
    "\u0648": ("\uFEED", "", "", "\uFEEE"),                        # و
    "\u0649": ("\uFEEF", "", "", "\uFEF0"),                        # ی (alef maksura)
    "\u064A": ("\uFEF1", "\uFEF3", "\uFEF4", "\uFEF2"),            # ي (arabic yeh)
    "\u067E": ("\uFB56", "\uFB58", "\uFB59", "\uFB57"),            # پ peh
    "\u0686": ("\uFB7A", "\uFB7C", "\uFB7D", "\uFB7B"),            # چ tcheh
    "\u0698": ("\uFB8A", "", "", "\uFB8B"),                        # ژ jeh
    "\u06A9": ("\uFB8E", "\uFB90", "\uFB91", "\uFB8F"),            # ک keheh
    "\u06AF": ("\uFB92", "\uFB94", "\uFB95", "\uFB93"),            # گ gaf
    "\u06CC": ("\uFBFC", "\uFBFE", "\uFBFF", "\uFBFD"),            # ی farsi yeh
}

# Characters that are part of Persian/Arabic script but aren't in LETTERS
# (punctuation, ZWNJ) - treated as "in-script" for word classification,
# but not shaped/joined themselves.
_PERSIAN_EXTRA = set("\u060C\u061B\u061F\u200C\u200D\u0670")


def _connects_after(ch: str) -> bool:
    forms = LETTERS.get(ch)
    return bool(forms and (forms[INITIAL] or forms[MEDIAL]))


def _connects_before(ch: str) -> bool:
    forms = LETTERS.get(ch)
    return bool(forms and (forms[FINAL] or forms[MEDIAL]))


def _shape_line(text: str) -> str:
    chars = list(text)
    out = []
    for i, ch in enumerate(chars):
        forms = LETTERS.get(ch)
        if not forms:
            out.append(ch)
            continue
        prev_ch = chars[i - 1] if i > 0 else ""
        next_ch = chars[i + 1] if i + 1 < len(chars) else ""
        prev_connects = _connects_after(prev_ch)
        next_connects = _connects_before(next_ch)

        if prev_connects and next_connects and forms[MEDIAL]:
            out.append(forms[MEDIAL])
        elif prev_connects and forms[FINAL]:
            out.append(forms[FINAL])
        elif next_connects and forms[INITIAL]:
            out.append(forms[INITIAL])
        else:
            out.append(forms[ISOLATED])
    return "".join(out)


def _is_rtl_word(word: str) -> bool:
    return any((ch in LETTERS or ch in _PERSIAN_EXTRA) for ch in word)


def fix_rtl(text: str) -> str:
    """Shape + reorder Persian/Arabic text for naive LTR-only terminals.

    Safe to call on mixed Persian/English/number strings - only words
    containing Persian/Arabic script are affected internally; Latin/digit
    words (URLs, version numbers, "YES", etc.) are preserved as-is and
    just moved to their mirrored position in the line.
    """
    lines = text.split("\n")
    fixed_lines = []
    for line in lines:
        words = line.split(" ")
        rendered = []
        for word in words:
            if _is_rtl_word(word):
                shaped = _shape_line(word)
                rendered.append(shaped[::-1])
            else:
                rendered.append(word)
        rendered.reverse()
        fixed_lines.append(" ".join(rendered))
    return "\n".join(fixed_lines)
