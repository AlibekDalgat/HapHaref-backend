from rest_framework import serializers

from .models import Root, Translation, UsageExample, Word


class RootSerializer(serializers.ModelSerializer):
    origin_display = serializers.CharField(
        source="get_origin_display", read_only=True
    )

    class Meta:
        model = Root
        fields = [
            "id",
            "morpheme",
            "transliteration",
            "origin",
            "origin_display",
            "description",
        ]


class TranslationSerializer(serializers.ModelSerializer):
    language_display = serializers.CharField(
        source="get_language_display", read_only=True
    )

    class Meta:
        model = Translation
        fields = ["id", "language", "language_display", "text", "order"]


class UsageExampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageExample
        fields = [
            "id",
            "text_arabic",
            "text_cyrillic",
            "translation",
            "source",
            "order",
        ]


class WordListSerializer(serializers.ModelSerializer):
    """Compact representation for search results."""

    part_of_speech_display = serializers.CharField(
        source="get_part_of_speech_display", read_only=True
    )
    translations = TranslationSerializer(many=True, read_only=True)

    class Meta:
        model = Word
        fields = [
            "id",
            "headword_arabic",
            "transliteration_latin",
            "transliteration_cyrillic",
            "part_of_speech",
            "part_of_speech_display",
            "translations",
        ]


class WordDetailSerializer(serializers.ModelSerializer):
    """Full word card with all encyclopedic information."""

    part_of_speech_display = serializers.CharField(
        source="get_part_of_speech_display", read_only=True
    )
    root = RootSerializer(read_only=True)
    translations = TranslationSerializer(many=True, read_only=True)
    examples = UsageExampleSerializer(many=True, read_only=True)

    class Meta:
        model = Word
        fields = [
            "id",
            "headword_arabic",
            "transliteration_latin",
            "transliteration_cyrillic",
            "pronunciation",
            "part_of_speech",
            "part_of_speech_display",
            "root",
            "definition",
            "etymology",
            "notes",
            "translations",
            "examples",
            "created_at",
            "updated_at",
        ]
