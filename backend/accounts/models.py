from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    ADMIN = "admin", _("Admin")
    MANAGER = "manager", _("Manager")
    EMPLOYEE = "employee", _("Employee")


class CustomUser(AbstractUser):
    email = models.EmailField(
        _("email address"),
        unique=True,
        error_messages={
            "unique": _("A user with that email already exists."),
        },
    )
    role = models.CharField(
        max_length=25,
        choices=UserRole.choices,
        blank=True,
        verbose_name=_("user role"),
        help_text=_("Designates the role this user belongs to"),
    )

    def __str__(self):
        return f"{self.get_full_name()} ({self.email}) - {self.get_role_display()}"

    def save(self, *args, **kwargs):
        if not self.role:
            self.role = UserRole.ADMIN if self.is_superuser else UserRole.MANAGER

        super().save(*args, **kwargs)

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def is_manager(self):
        return self.role == UserRole.MANAGER

    @property
    def is_employee(self):
        return self.role == UserRole.EMPLOYEE

    @property
    def role_display(self):
        return self.get_role_display()
