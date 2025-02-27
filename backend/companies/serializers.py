from typing import Any, Dict

from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import Company, Department, Employee, EmployeeStatus


class ReadOnlyEmployeeSerializer(serializers.ModelSerializer):
    days_employed = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            "id",
            "name",
            "status",
            "email",
            "mobile",
            "address",
            "designation",
            "hired_on",
            "days_employed",
            "company",
            "department",
            "company_name",
            "department_name",
        ]

    def get_days_employed(self, obj: Employee) -> int:
        return obj.get_days_employed()

    def get_company_name(self, obj: Employee) -> str:
        return obj.department.company.name

    def get_department_name(self, obj: Employee) -> str:
        return obj.department.name

    def get_company(self, obj: Employee) -> Company:
        return obj.department.company


class EmployeeCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new employees."""

    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())

    class Meta:
        model = Employee
        fields = [
            "company",
            "department",
            "name",
            "email",
            "mobile",
            "address",
            "designation",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        if attrs["status"] not in [
            EmployeeStatus.APPLICATION_RECEIVED,
            EmployeeStatus.INTERVIEW_SCHEDULED,
            EmployeeStatus.HIRED,
            EmployeeStatus.NOT_ACCEPTED,
        ]:
            raise ValidationError(
                {
                    "status": _(
                        "Invalid status. Status must be one of: "
                        f"{', '.join(settings.EMPLOYEE_STATUS)}"
                    )
                }
            )
        manger = self.context["request"].user
        company = attrs["company"]
        department = attrs["department"]
        if not manger.companies.filter(id=company.id).exists():
            raise ValidationError("Invalid selected company")
        if not company.departments.filter(id=department.id).exists():
            raise ValidationError("invalid selected department")
        return attrs

    def create(self, validated_data):
        validated_data.pop("company")
        employee = Employee.objects.create(**validated_data)
        return employee


class EmployeeUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating employee information and status."""

    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())

    class Meta:
        model = Employee
        fields = [
            "department",
            "name",
            "email",
            "mobile",
            "address",
            "designation",
            "status",
            "department",
        ]
        read_only_fields = ["id", "hired_on"]

    def validate_email(self, value: str) -> str:
        """Validate email is unique and in correct format."""
        if Employee.objects.filter(email=value).exclude(id=self.instance.id).exists():
            raise ValidationError(_("Email address must be unique"))
        return value.lower()

    def validate_department(self, value: Department) -> Department:
        if value.company != self.instance.department.company:
            raise ValidationError(
                _("Cannot transfer employee to a department in a different company")
            )
        return value

    def validate_status(self, value: str) -> str:
        """Validate status transitions."""
        if value not in [
            EmployeeStatus.APPLICATION_RECEIVED,
            EmployeeStatus.INTERVIEW_SCHEDULED,
            EmployeeStatus.HIRED,
            EmployeeStatus.NOT_ACCEPTED,
        ]:
            raise ValidationError(
                {
                    "status": _(
                        "Invalid status. Status must be one of: "
                        f"{', '.join(settings.EMPLOYEE_STATUS)}"
                    )
                }
            )
        instance = self.instance
        if not instance:
            return value

        # If status hasn't changed, return as is
        if value == instance.status:
            return value

        if instance.status in [EmployeeStatus.HIRED, EmployeeStatus.NOT_ACCEPTED]:
            raise ValidationError(
                _("Cannot update status of already hired or not accepted employees")
            )

        valid_transitions = {
            EmployeeStatus.APPLICATION_RECEIVED: [
                EmployeeStatus.INTERVIEW_SCHEDULED,
                EmployeeStatus.NOT_ACCEPTED,
            ],
            EmployeeStatus.INTERVIEW_SCHEDULED: [
                EmployeeStatus.HIRED,
                EmployeeStatus.NOT_ACCEPTED,
            ],
        }

        allowed_statuses = valid_transitions.get(instance.status, [])
        if value not in allowed_statuses:
            raise ValidationError(
                _(f"Cannot transition from {instance.status} to {value}")
            )

        return value

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Additional validation for the entire update operation."""
        manager = self.context["request"].user
        if not manager.companies.filter(
            id=self.instance.department.company.id
        ).exists():
            raise ValidationError(
                _("You do not have permission to update this employee")
            )

        return attrs

    def update(self, instance: Employee, validated_data: Dict[str, Any]) -> Employee:
        if validated_data.get("status") == EmployeeStatus.HIRED:
            validated_data["hired_on"] = timezone.now().date()

        employee = super().update(instance, validated_data)
        return employee


class ReadOnlyDepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model with nested employees."""

    employees = ReadOnlyEmployeeSerializer(many=True, read_only=True)
    employees_count = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            "id",
            "name",
            "company",
            "company_name",
            "employees",
            "employees_count",
            "created_at",
        ]

    def get_employees_count(self, obj):
        return obj.get_employees_count()

    def get_company_name(self, obj):
        return obj.company.name


class DepartmentCreateSerializer(serializers.ModelSerializer):
    company = serializers.PrimaryKeyRelatedField(queryset=Company.objects.all())

    class Meta:
        model = Department
        fields = ["id", "name", "company", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        company = attrs["company"]
        if not company.manager == self.context["request"].user:
            raise ValidationError(
                "You do not have permission to create a department in this company"
            )
        if Department.objects.filter(company=company, name=attrs["name"]).exists():
            raise ValidationError("Department name must be unique within company")
        return attrs

    def create(self, validated_data):
        department = Department.objects.create(**validated_data)
        return department

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.save()
        return instance


class ReadOnlyCompanySerializer(serializers.ModelSerializer):
    """Serializer for Company model with nested departments and statistics."""

    departments = ReadOnlyDepartmentSerializer(many=True, read_only=True)
    employees_count = serializers.SerializerMethodField()
    departments_count = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "departments",
            "employees_count",
            "departments_count",
            "created_at",
        ]

    def get_employees_count(self, obj):
        return obj.get_employees_count()

    def get_departments_count(self, obj):
        return obj.get_departments_count()


class ReadOnlyAdminCompanySerializer(serializers.ModelSerializer):
    departments_count = serializers.SerializerMethodField()
    employees_count = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "employees_count",
            "departments_count",
            "created_at",
        ]

        extra_kwargs = {
            "name": {"read_only": True},
            "created_at": {"read_only": True},
        }

    def get_employees_count(self, obj):
        return obj.get_employees_count()

    def get_departments_count(self, obj):
        return obj.get_departments_count()


class CompanyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        name = attrs.get("name")
        manager = self.context["request"].user
        if Company.objects.filter(manager=manager, name=name).exists():
            raise ValidationError("Company name must be unique")
        attrs["manager"] = manager
        return attrs

    def create(self, validated_data):
        company = Company.objects.create(**validated_data)
        return company

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.save()
        return instance
