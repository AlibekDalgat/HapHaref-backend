"""Seed a handful of sample Old Tatar entries for local development/demo."""
from django.core.management.base import BaseCommand

from dictionary.models import Root, Translation, UsageExample, Word

# roots: morpheme -> (transliteration, origin, description)
ROOTS = {
    "ك‌ت‌ب": ("k-t-b", "arabic", "Арабский корень со значением «писать»."),
    "ی‌ا‌ز": ("yaz", "turkic", "Тюркский корень со значением «писать»."),
}

SAMPLE = [
    {
        "headword_arabic": "كیتاب",
        "transliteration_latin": "kitap",
        "transliteration_cyrillic": "китап",
        "pronunciation": "kʲiˈtap",
        "part_of_speech": "noun",
        "root": "ك‌ت‌ب",
        "definition": "Сшитые листы бумаги с текстом; рукопись или печатное издание.",
        "etymology": "Из арабского كِتَاب (kitāb) «книга, писание», от корня k-t-b «писать».",
        "notes": "Одно из самых частотных заимствований в старотатарском.",
        "translations": [("ru", "книга"), ("en", "book"), ("tt", "китап")],
        "examples": [("بو كیتاب ییخشی", "бу китап йихши", "Эта книга хорошая", "Учебный пример")],
    },
    {
        "headword_arabic": "سو",
        "transliteration_latin": "su",
        "transliteration_cyrillic": "су",
        "pronunciation": "sɯw",
        "part_of_speech": "noun",
        "root": None,
        "definition": "Прозрачная жидкость без вкуса и запаха.",
        "etymology": "Общетюркское *sub «вода».",
        "notes": "",
        "translations": [("ru", "вода"), ("en", "water")],
        "examples": [("سو ایچتم", "су ичтем", "Я выпил воды", "")],
    },
    {
        "headword_arabic": "یاز",
        "transliteration_latin": "yaz",
        "transliteration_cyrillic": "яз",
        "pronunciation": "jaz",
        "part_of_speech": "verb",
        "root": "ی‌ا‌ز",
        "definition": "Наносить письменные знаки на поверхность.",
        "etymology": "Общетюркское *jaz- «писать».",
        "notes": "Омонимично с «яз» (лето/весна).",
        "translations": [("ru", "писать"), ("en", "to write")],
        "examples": [("مكتوب یاز", "мәктүб яз", "Напиши письмо", "")],
    },
    {
        "headword_arabic": "كون",
        "transliteration_latin": "kön",
        "transliteration_cyrillic": "көн",
        "pronunciation": "køn",
        "part_of_speech": "noun",
        "root": None,
        "definition": "Светлая часть суток; сутки.",
        "etymology": "Общетюркское *kün «солнце, день».",
        "notes": "",
        "translations": [("ru", "день"), ("ru", "солнце"), ("en", "day")],
        "examples": [("یاخشی كون", "яхшы көн", "Хороший день", "")],
    },
]


class Command(BaseCommand):
    help = "Создаёт несколько демонстрационных записей словаря."

    def handle(self, *args, **options):
        roots = {}
        for morpheme, (translit, origin, desc) in ROOTS.items():
            root, _ = Root.objects.get_or_create(
                morpheme=morpheme,
                defaults={"transliteration": translit, "origin": origin, "description": desc},
            )
            roots[morpheme] = root

        created = 0
        for item in SAMPLE:
            word, made = Word.objects.get_or_create(
                headword_arabic=item["headword_arabic"],
                defaults={
                    "transliteration_latin": item["transliteration_latin"],
                    "transliteration_cyrillic": item["transliteration_cyrillic"],
                    "pronunciation": item["pronunciation"],
                    "part_of_speech": item["part_of_speech"],
                    "root": roots.get(item["root"]) if item["root"] else None,
                    "definition": item["definition"],
                    "etymology": item["etymology"],
                    "notes": item["notes"],
                    "is_published": True,
                },
            )
            if not made:
                self.stdout.write(f"= уже существует: {word.headword_arabic}")
                continue
            created += 1
            for order, (lang, text) in enumerate(item["translations"]):
                Translation.objects.create(
                    word=word, language=lang, text=text, order=order
                )
            for order, (ar, cyr, tr, src) in enumerate(item["examples"]):
                UsageExample.objects.create(
                    word=word, text_arabic=ar, text_cyrillic=cyr,
                    translation=tr, source=src, order=order,
                )
            self.stdout.write(self.style.SUCCESS(f"+ создано: {word.headword_arabic}"))

        self.stdout.write(self.style.SUCCESS(f"Готово. Новых записей: {created}."))
