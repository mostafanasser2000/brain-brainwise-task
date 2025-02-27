from typing import Optional

from core.models import BaseModel
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Company(BaseModel):
    manager = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="companies",
        help_text=_("User responsible for managing this company"),
    )
    name = models.CharField(
        max_length=255, unique=True, help_text=_("Unique name of the company")
    )

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"

        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["-created_at"]),
        ]

    def get_employees_count(self):
        return sum(
            department.get_employees_count() for department in self.departments.all()
        )

    def get_departments_count(self):
        return self.departments.count()

    def __str__(self):
        return self.name


class Department(BaseModel):
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="departments",
        help_text=_("Company this department belongs to"),
    )
    name = models.CharField(max_length=255, help_text=_("Name of the department"))

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "name"], name="unique_department_name_per_company"
            )
        ]
        indexes = [
            models.Index(fields=["-created_at"]),
        ]

    class Meta:
        verbose_name = "Department"
        verbose_name_plural = "Departments"

        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["-created_at"]),
        ]

    def get_employees_count(self):
        return self.employees.count()

    def __str__(self):
        return f"{self.name} at {self.company}"


class EmployeeStatus(models.TextChoices):
    APPLICATION_RECEIVED = "application received", _("Application Received")
    INTERVIEW_SCHEDULED = "interview scheduled", _("Interview Scheduled")
    NOT_ACCEPTED = "not accepted", _("Not Accepted")
    HIRED = "hired", _("Hired")


class Employee(BaseModel):
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="employees",
        help_text=_("Department this employee belongs to"),
    )
    name = models.CharField(max_length=255, help_text=_("Full name of the employee"))
    status = models.CharField(
        max_length=255,
        choices=EmployeeStatus.choices,
        default=EmployeeStatus.APPLICATION_RECEIVED,
        help_text=_("Current status in the hiring workflow"),
    )
    email = models.EmailField(
        unique=True, validators=[EmailValidator()], help_text=_("Unique email address")
    )
    mobile = models.CharField(
        max_length=255,
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,15}$",
                message=_("Mobile number must be in international format: +1234567890"),
            )
        ],
        help_text=_("Mobile number in international format"),
    )
    address = models.CharField(max_length=255, help_text=_("Physical address"))
    designation = models.CharField(max_length=255, help_text=_("Job title/position"))
    hired_on = models.DateField(
        null=True,
        blank=True,
        help_text=_("Date when employee was hired (only set when status is HIRED)"),
    )

    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"

        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["hired_on"]),
        ]

    def clean(self) -> None:
        """Validate model fields and their relationships."""
        super().clean()

        if self.status == EmployeeStatus.HIRED and not self.hired_on:
            raise ValidationError(
                {"hired_on": _("Hired date is required when status is HIRED")}
            )

        if self.status != EmployeeStatus.HIRED and self.hired_on:
            raise ValidationError(
                {"hired_on": _("Hired date should only be set when status is HIRED")}
            )

    def save(self, *args, **kwargs) -> None:
        self.clean()
        super().save(*args, **kwargs)

    def get_days_employed(self) -> int:
        if self.hired_on is None:
            return 0
        hired_since = timezone.now().date() - self.hired_on
        return hired_since.days

    @property
    def company(self) -> Optional["Company"]:
        return self.department.company if self.department else None

    def __str__(self):
        return f"{self.name} - {self.designation} - {self.status} at {self.department} "
