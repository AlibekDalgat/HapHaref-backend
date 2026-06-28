from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model.

    Roles (conceptual model):
      * Суперпользователь — флаг ``is_superuser``: управление словарём (фронт)
        и техническая Django-админка. Это владелец системы, не значение роли.
      * Редактор (``role=editor``) — только управление словарём (фронт-панель).
      * Пользователь (``role=user``) — обычный пользователь (поиск, предложка).
    """

    class Role(models.TextChoices):
        USER = "user", "Пользователь"
        EDITOR = "editor", "Редактор"

    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.USER,
        verbose_name="Роль",
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    @property
    def can_edit_dictionary(self) -> bool:
        """Доступ к управлению словарём: редакторы и суперпользователи."""
        return self.is_superuser or self.role == self.Role.EDITOR

    def __str__(self) -> str:
        return self.get_username()
