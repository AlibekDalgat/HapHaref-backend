from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model.

    Authenticated users exist as a first-class entity from day one, but in the
    MVP only administrators get edit privileges. The ``role`` field is the seam
    for future tiers (e.g. contributors who submit suggestions for review).
    """

    class Role(models.TextChoices):
        USER = "user", "Пользователь"
        EDITOR = "editor", "Редактор"
        ADMIN = "admin", "Администратор"

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
    def is_dictionary_admin(self) -> bool:
        return self.is_superuser or self.role == self.Role.ADMIN

    def __str__(self) -> str:
        return self.get_username()
