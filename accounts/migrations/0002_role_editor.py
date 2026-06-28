from django.db import migrations, models


def admin_role_to_editor(apps, schema_editor):
    # Прежняя роль "admin" (доступ к словарю) теперь называется "editor".
    User = apps.get_model("accounts", "User")
    User.objects.filter(role="admin").update(role="editor")


def editor_role_to_admin(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(role="editor").update(role="admin")


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(admin_role_to_editor, editor_role_to_admin),
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[("user", "Пользователь"), ("editor", "Редактор")],
                default="user",
                max_length=16,
                verbose_name="Роль",
            ),
        ),
    ]
