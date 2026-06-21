from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Word
from .search import search_words
from .serializers import WordDetailSerializer, WordListSerializer


class WordViewSet(viewsets.ReadOnlyModelViewSet):
    """Public read-only API for dictionary entries.

    - ``GET /api/words/``            list all entries (paginated)
    - ``GET /api/words/{id}/``       full word card
    - ``GET /api/words/search/?q=``  typo-tolerant, cross-script search
    """

    # Public API only exposes published entries; drafts/suggestions stay hidden.
    queryset = (
        Word.objects.filter(is_published=True)
        .select_related("root")
        .prefetch_related("translations", "examples")
    )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return WordDetailSerializer
        return WordListSerializer

    @action(detail=False, methods=["get"])
    def search(self, request):
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response({"query": query, "count": 0, "results": []})

        results = search_words(query)
        page = self.paginate_queryset(results)
        if page is not None:
            serializer = WordListSerializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data["query"] = query
            return response

        serializer = WordListSerializer(results, many=True)
        return Response(
            {"query": query, "count": len(serializer.data), "results": serializer.data}
        )
