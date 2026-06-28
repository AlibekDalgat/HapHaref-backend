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
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
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
            "status",
            "status_display",
            "translations",
            "examples",
            "created_at",
            "updated_at",
        ]


class AdminWordListSerializer(serializers.ModelSerializer):
    """Compact word row for the admin/moderation queue."""

    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    created_by = serializers.CharField(
        source="created_by.username", read_only=True, default=None
    )

    class Meta:
        model = Word
        fields = [
            "id",
            "headword_arabic",
            "transliteration_latin",
            "transliteration_cyrillic",
            "status",
            "status_display",
            "created_by",
            "created_at",
            "updated_at",
        ]


class WordWriteSerializer(serializers.ModelSerializer):
    """Create/update a word together with its translations and examples.

    Used by the admin word form and (for status=pending) the public
    "suggest a word" form. ``root`` is referenced by id; translations and
    examples are written as nested arrays and fully replaced on update.
    """

    root = serializers.PrimaryKeyRelatedField(
        queryset=Root.objects.all(), allow_null=True, required=False
    )
    translations = TranslationSerializer(many=True, required=False)
    examples = UsageExampleSerializer(many=True, required=False)

    class Meta:
        model = Word
        fields = [
            "id",
            "headword_arabic",
            "transliteration_latin",
            "transliteration_cyrillic",
            "pronunciation",
            "part_of_speech",
            "root",
            "definition",
            "etymology",
            "notes",
            "status",
            "translations",
            "examples",
        ]

    def create(self, validated_data):
        translations = validated_data.pop("translations", [])
        examples = validated_data.pop("examples", [])
        word = Word.objects.create(**validated_data)
        self._write_children(word, translations, examples)
        return word

    def update(self, instance, validated_data):
        translations = validated_data.pop("translations", None)
        examples = validated_data.pop("examples", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        # Replace nested collections only if provided in the payload.
        if translations is not None:
            instance.translations.all().delete()
            self._write_children(instance, translations, [])
        if examples is not None:
            instance.examples.all().delete()
            self._write_children(instance, [], examples)
        return instance

    @staticmethod
    def _write_children(word, translations, examples):
        Translation.objects.bulk_create(
            [Translation(word=word, **t) for t in translations]
        )
        UsageExample.objects.bulk_create(
            [UsageExample(word=word, **e) for e in examples]
        )

    def to_representation(self, instance):
        return WordDetailSerializer(instance, context=self.context).data


class WordSuggestSerializer(WordWriteSerializer):
    """Public "suggest a word" form.

    Same nested create as the admin form, but without the ``root`` and
    ``status`` fields — the editor assigns the root and publishes during
    moderation; the status is forced to ``pending`` in the view.
    """

    root = None

    class Meta(WordWriteSerializer.Meta):
        fields = [
            "headword_arabic",
            "transliteration_latin",
            "transliteration_cyrillic",
            "pronunciation",
            "part_of_speech",
            "definition",
            "etymology",
            "notes",
            "translations",
            "examples",
        ]
