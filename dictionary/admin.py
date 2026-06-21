from django.contrib import admin
from django.contrib.admin.models import LogEntry

from .models import Root, Translation, UsageExample, Word


@admin.register(Root)
class RootAdmin(admin.ModelAdmin):
    list_display = ("morpheme", "transliteration", "origin")
    list_filter = ("origin",)
    search_fields = ("morpheme", "transliteration", "description")


class TranslationInline(admin.TabularInline):
    model = Translation
    extra = 1


class UsageExampleInline(admin.StackedInline):
    model = UsageExample
    extra = 1


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = (
        "headword_arabic",
        "transliteration_latin",
        "transliteration_cyrillic",
        "part_of_speech",
        "is_published",
        "updated_at",
    )
    list_filter = ("part_of_speech", "is_published", "root__origin")
    search_fields = (
        "headword_arabic",
        "transliteration_latin",
        "transliteration_cyrillic",
        "norm_arabic",
        "norm_latin",
        "norm_cyrillic",
    )
    autocomplete_fields = ("root",)
    inlines = [TranslationInline, UsageExampleInline]
    readonly_fields = ("created_at", "updated_at", "created_by")
    fieldsets = (
        (None, {
            "fields": (
                "headword_arabic",
                ("transliteration_latin", "transliteration_cyrillic"),
                "pronunciation",
                "part_of_speech",
                "root",
                "is_published",
            )
        }),
        ("Энциклопедическая информация", {
            "fields": ("definition", "etymology", "notes"),
        }),
        ("Служебное", {
            "fields": ("created_by", "created_at", "updated_at"),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change and obj.created_by_id is None:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# --- Audit log ---------------------------------------------------------------
# Django records every add/change/delete made through the admin in LogEntry.
# We surface it read-only so admins can review who changed what and when.

ACTION_LABELS = {1: "Создание", 2: "Изменение", 3: "Удаление"}


@admin.register(LogEntry)
class AuditLogAdmin(admin.ModelAdmin):
    date_hierarchy = "action_time"
    list_display = (
        "action_time",
        "user",
        "content_type",
        "object_repr",
        "action_label",
        "change_message",
    )
    list_filter = ("action_flag", "content_type", "user")
    search_fields = ("object_repr", "change_message")

    @admin.display(description="Действие")
    def action_label(self, obj):
        return ACTION_LABELS.get(obj.action_flag, obj.action_flag)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
