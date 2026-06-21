"""Text normalization helpers for typo-tolerant, cross-script search.

The dictionary stores each headword in three scripts (Arabic naskh, Latin and
Cyrillic transliteration). To let a user "misspell and still find it", we build
a single normalized search blob per word and compare it against a normalized
query using trigram similarity (pg_trgm).

The Arabic folding below collapses letters that *sound* alike but are written
with different glyphs (e.g. ض/د، ث/س/ص، ظ/ز, the various hamza forms). That is
exactly the "дод и даль" case from the brief: a learner who picks the wrong but
phonetically-close letter should still land on the right entry.
"""
import re
import unicodedata

# Arabic letters that map to the same Turkic phoneme -> folded representative.
_ARABIC_FOLD = {
    # s-group: ث ص س
    "ث": "س",
    "ص": "س",
    # z-group: ذ ض ظ ز
    "ذ": "ز",
    "ض": "ز",
    "ظ": "ز",
    # t-group: ط ت
    "ط": "ت",
    # h-group: ح ه
    "ح": "ه",
    "ة": "ه",  # ta marbuta -> h
    # k/q-group: ق ك
    "ق": "ك",
    # hamza / alef variants -> bare alef
    "أ": "ا",
    "إ": "ا",
    "آ": "ا",
    "ٱ": "ا",
    "ء": "",
    "ئ": "ي",  # ya with hamza -> ya
    "ؤ": "و",  # waw with hamza -> waw
}

# Arabic diacritics (harakat, tatweel) stripped before comparison.
_ARABIC_DIACRITICS = re.compile(r"[ؐ-ًؚ-ٟـٰۖ-ۭ]")

_WHITESPACE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Return a lowercased, accent- and script-quirk-folded form of ``text``."""
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)
    text = text.casefold()

    # Strip Arabic diacritics and tatweel.
    text = _ARABIC_DIACRITICS.sub("", text)

    # Fold phonetically-equivalent Arabic letters.
    text = "".join(_ARABIC_FOLD.get(ch, ch) for ch in text)

    # Strip combining marks left over from Latin/Cyrillic accents.
    text = "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if not unicodedata.combining(ch)
    )

    text = _WHITESPACE.sub(" ", text).strip()
    return text
