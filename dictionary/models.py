from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.db import models

from .normalization import normalize


class PartOfSpeech(models.TextChoices):
    NOUN = "noun", "Существительное"
    VERB = "verb", "Глагол"
    ADJECTIVE = "adjective", "Прилагательное"
    ADVERB = "adverb", "Наречие"
    PRONOUN = "pronoun", "Местоимение"
    NUMERAL = "numeral", "Числительное"
    PARTICLE = "particle", "Частица"
    CONJUNCTION = "conjunction", "Союз"
    POSTPOSITION = "postposition", "Послелог"
    INTERJECTION = "interjection", "Междометие"
    PHRASE = "phrase", "Устойчивое выражение"
    OTHER = "other", "Другое"


class Root(models.Model):
    """A morphological root shared by one or more words.

    Old Tatar entries draw on roots of different origins (Turkic, Arabic,
    Persian), so the origin is tracked explicitly. This is the foundation for
    the future "search by root" feature.
    """

    class Origin(models.TextChoices):
        TURKIC = "turkic", "Тюркский"
        ARABIC = "arabic", "Арабский"
        PERSIAN = "persian", "Персидский"
        OTHER = "other", "Другое"

    morpheme = models.CharField(
        "Корень (арабица)", max_length=64,
        help_text="Корневая морфема, напр. ك‌ت‌ب.",
    )
    transliteration = models.CharField(
        "Транслитерация корня", max_length=64, blank=True,
        help_text="Напр. k-t-b.",
    )
    origin = models.CharField(
        "Происхождение", max_length=16, choices=Origin.choices,
        default=Origin.TURKIC,
    )
    description = models.TextField("Описание", blank=True)

    class Meta:
        verbose_name = "Корень"
        verbose_name_plural = "Корни"
        ordering = ["morpheme"]

    def __str__(self) -> str:
        label = self.transliteration or self.morpheme
        return f"{self.morpheme} ({self.get_origin_display()}, {label})"


class Word(models.Model):
    """A single dictionary entry for an Old Tatar word."""

    class Status(models.TextChoices):
        PENDING = "pending", "На модерации"
        PUBLISHED = "published", "Опубликовано"
        REJECTED = "rejected", "Отклонено"

    headword_arabic = models.CharField(
        "Слово (арабица, насх)",
        max_length=255,
        help_text="Аутентичное написание на арабской графике (насх).",
    )
    transliteration_latin = models.CharField(
        "Транслитерация (латиница)", max_length=255, blank=True
    )
    transliteration_cyrillic = models.CharField(
        "Транслитерация (кириллица)", max_length=255, blank=True
    )
    pronunciation = models.CharField(
        "Произношение (IPA / фонетика)", max_length=255, blank=True
    )
    part_of_speech = models.CharField(
        "Часть речи",
        max_length=20,
        choices=PartOfSpeech.choices,
        default=PartOfSpeech.OTHER,
    )
    root = models.ForeignKey(
        Root,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="words",
        verbose_name="Корень",
    )
    definition = models.TextField(
        "Толкование", blank=True,
        help_text="Развёрнутое определение слова (в отличие от краткого перевода).",
    )
    etymology = models.TextField("Этимология", blank=True)
    notes = models.TextField("Примечания", blank=True)

    status = models.CharField(
        "Статус", max_length=12,
        choices=Status.choices, default=Status.PUBLISHED,
        help_text="Опубликовано — видно в публичном поиске; на модерации — "
        "предложение пользователя, ожидающее проверки.",
    )

    # Denormalized, normalized per-script forms used for typo-tolerant trigram
    # search. Kept separate (not one blob) so similarity is scored against a
    # single script at a time instead of being diluted across all three.
    norm_arabic = models.CharField(max_length=255, editable=False, default="")
    norm_latin = models.CharField(max_length=255, editable=False, default="")
    norm_cyrillic = models.CharField(max_length=255, editable=False, default="")

    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_words",
        verbose_name="Автор записи",
    )

    class Meta:
        verbose_name = "Слово"
        verbose_name_plural = "Слова"
        ordering = ["headword_arabic"]
        indexes = [
            # Trigram GIN indexes power fuzzy / typo-tolerant search per script.
            GinIndex(
                name="word_norm_arabic_trgm",
                fields=["norm_arabic"],
                opclasses=["gin_trgm_ops"],
            ),
            GinIndex(
                name="word_norm_latin_trgm",
                fields=["norm_latin"],
                opclasses=["gin_trgm_ops"],
            ),
            GinIndex(
                name="word_norm_cyrillic_trgm",
                fields=["norm_cyrillic"],
                opclasses=["gin_trgm_ops"],
            ),
        ]

    def save(self, *args, **kwargs):
        self.norm_arabic = normalize(self.headword_arabic)
        self.norm_latin = normalize(self.transliteration_latin)
        self.norm_cyrillic = normalize(self.transliteration_cyrillic)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        label = self.transliteration_latin or self.transliteration_cyrillic
        return f"{self.headword_arabic} ({label})" if label else self.headword_arabic


class Translation(models.Model):
    """A translation of a word into a target language."""

    class Language(models.TextChoices):
        RUSSIAN = "ru", "Русский"
        ENGLISH = "en", "Английский"
        TATAR = "tt", "Татарский (совр.)"
        TURKISH = "tr", "Турецкий"

    word = models.ForeignKey(
        Word, on_delete=models.CASCADE, related_name="translations",
        verbose_name="Слово",
    )
    language = models.CharField(
        "Язык", max_length=8, choices=Language.choices, default=Language.RUSSIAN
    )
    text = models.CharField("Перевод", max_length=500)
    order = models.PositiveSmallIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Перевод"
        verbose_name_plural = "Переводы"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"[{self.get_language_display()}] {self.text}"


class UsageExample(models.Model):
    """An example sentence illustrating the word in context."""

    word = models.ForeignKey(
        Word, on_delete=models.CASCADE, related_name="examples",
        verbose_name="Слово",
    )
    text_arabic = models.TextField("Пример (арабица)")
    text_cyrillic = models.TextField("Пример (кириллица)", blank=True)
    translation = models.TextField("Перевод примера", blank=True)
    source = models.CharField(
        "Источник", max_length=255, blank=True,
        help_text="Произведение, автор или ссылка на источник.",
    )
    order = models.PositiveSmallIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Пример использования"
        verbose_name_plural = "Примеры использования"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.text_arabic[:60]
