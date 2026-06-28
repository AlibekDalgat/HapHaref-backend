from django.db.models import Q
from rest_framework import status as http_status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from accounts.permissions import CanEditDictionary

from .models import Root, Word
from .search import search_words
from .serializers import (
    AdminWordListSerializer,
    RootSerializer,
    WordDetailSerializer,
    WordListSerializer,
    WordSuggestSerializer,
    WordWriteSerializer,
)


class WordViewSet(viewsets.ReadOnlyModelViewSet):
    """Public read-only API for dictionary entries.

    - ``GET /api/words/``            list all entries (paginated)
    - ``GET /api/words/{id}/``       full word card
    - ``GET /api/words/search/?q=``  typo-tolerant, cross-script search
    """

    # Public API only exposes published entries; drafts/suggestions stay hidden.
    queryset = (
        Word.objects.filter(status=Word.Status.PUBLISHED)
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

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def suggest(self, request):
        """Public submission of a new word — lands in the moderation queue."""
        serializer = WordSuggestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user if request.user.is_authenticated else None
        serializer.save(status=Word.Status.PENDING, created_by=user)
        return Response(
            {"detail": "Спасибо! Слово отправлено на модерацию."},
            status=http_status.HTTP_201_CREATED,
        )


class AdminWordViewSet(viewsets.ModelViewSet):
    """Authenticated CRUD + moderation for dictionary entries.

    - ``GET /api/admin/words/?status=pending``  очередь предложений
    - ``POST /api/admin/words/``                 создать слово
    - ``PUT/PATCH /api/admin/words/{id}/``       редактировать (в т.ч. предложение)
    - ``POST /api/admin/words/{id}/accept/``     опубликовать предложение
    - ``POST /api/admin/words/{id}/reject/``     отклонить предложение
    """

    permission_classes = [CanEditDictionary]

    def get_queryset(self):
        qs = (
            Word.objects.all()
            .select_related("root", "created_by")
            .prefetch_related("translations", "examples")
            .order_by("-created_at")
        )
        status_param = self.request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)
        q = self.request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(headword_arabic__icontains=q)
                | Q(transliteration_latin__icontains=q)
                | Q(transliteration_cyrillic__icontains=q)
            )
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return AdminWordListSerializer
        if self.action in ("create", "update", "partial_update"):
            return WordWriteSerializer
        return WordDetailSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def _set_status(self, request, pk, new_status):
        word = self.get_object()
        word.status = new_status
        word.save(update_fields=["status", "updated_at"])
        return Response(WordDetailSerializer(word, context={"request": request}).data)

    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        return self._set_status(request, pk, Word.Status.PUBLISHED)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._set_status(request, pk, Word.Status.REJECTED)


class AdminRootViewSet(viewsets.ModelViewSet):
    """Search and create roots for the word form (admins only).

    ``GET /api/admin/roots/?q=`` — поиск корня; ``POST`` — создать новый.
    """

    permission_classes = [CanEditDictionary]
    serializer_class = RootSerializer

    def get_queryset(self):
        qs = Root.objects.all().order_by("morpheme")
        q = self.request.query_params.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(morpheme__icontains=q) | Q(transliteration__icontains=q)
            )
        return qs
