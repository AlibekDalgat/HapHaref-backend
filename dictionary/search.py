"""Typo-tolerant, cross-script search over dictionary entries.

Strategy (MVP):
  1. Normalize the query the same way the stored norm_* fields were built
     (lowercase, strip Arabic diacritics, fold phonetically-equal letters).
  2. Score each entry by the *best* trigram similarity across its three
     normalized scripts (Arabic naskh, Latin, Cyrillic) — scoring per script
     rather than against one big blob keeps short-word typos detectable.
  3. Keep anything that contains the query as a substring in any script
     (exact-ish) or clears a lenient similarity threshold (fuzzy).

The per-field GIN trigram indexes keep this fast as the dictionary grows.
"""
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q
from django.db.models.functions import Greatest

from .models import Word
from .normalization import normalize

# Below this trigram score we treat the match as noise. Lowered for short
# queries so a 2-3 letter word still matches despite a typo.
SIMILARITY_THRESHOLD = 0.3
SHORT_QUERY_THRESHOLD = 0.2


def search_words(query: str):
    """Return a ``Word`` queryset ranked by relevance to ``query``."""
    normalized = normalize(query)
    if not normalized:
        return Word.objects.none()

    threshold = SIMILARITY_THRESHOLD if len(normalized) >= 4 else SHORT_QUERY_THRESHOLD

    return (
        Word.objects.filter(status=Word.Status.PUBLISHED)
        .annotate(
            similarity=Greatest(
                TrigramSimilarity("norm_arabic", normalized),
                TrigramSimilarity("norm_latin", normalized),
                TrigramSimilarity("norm_cyrillic", normalized),
            )
        )
        .filter(
            Q(norm_arabic__icontains=normalized)
            | Q(norm_latin__icontains=normalized)
            | Q(norm_cyrillic__icontains=normalized)
            | Q(similarity__gte=threshold)
        )
        .order_by("-similarity", "headword_arabic")
        .prefetch_related("translations")
        .distinct()
    )
