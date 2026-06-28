from django.db import migrations, models


def is_published_to_status(apps, schema_editor):
    Word = apps.get_model("dictionary", "Word")
    Word.objects.filter(is_published=True).update(status="published")
    Word.objects.filter(is_published=False).update(status="pending")


def status_to_is_published(apps, schema_editor):
    Word = apps.get_model("dictionary", "Word")
    Word.objects.filter(status="published").update(is_published=True)
    Word.objects.exclude(status="published").update(is_published=False)


class Migration(migrations.Migration):

    dependencies = [
        ("dictionary", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="word",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "На модерации"),
                    ("published", "Опубликовано"),
                    ("rejected", "Отклонено"),
                ],
                default="published",
                help_text="Опубликовано — видно в публичном поиске; на модерации — "
                "предложение пользователя, ожидающее проверки.",
                max_length=12,
                verbose_name="Статус",
            ),
        ),
        migrations.RunPython(is_published_to_status, status_to_is_published),
        migrations.RemoveField(model_name="word", name="is_published"),
    ]
