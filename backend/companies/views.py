from typing import override

from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Company, Department, Employee
from .permissions import IsCompanyManager, IsMangerOrReadOnly
from .serializers import (
    CompanyCreateSerializer,
    DepartmentCreateSerializer,
    EmployeeCreateSerializer,
    EmployeeUpdateSerializer,
    ReadOnlyAdminCompanySerializer,
    ReadOnlyCompanySerializer,
    ReadOnlyDepartmentSerializer,
    ReadOnlyEmployeeSerializer,
)


class CompanyViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsMangerOrReadOnly]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CompanyCreateSerializer
        if self.request.user.is_superuser:
            return ReadOnlyAdminCompanySerializer
        return ReadOnlyCompanySerializer

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Company.objects.all()
        return Company.objects.filter(manager=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        if request.user.is_superuser:
            stats = Company.objects.aggregate(
                total_companies=Count("id"),
                total_departments=Count("departments"),
                total_employees=Count("departments__employees"),
            )
            serializer = self.get_serializer(queryset, many=True)
            return Response({"statistics": stats, "companies": serializer.data})

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DepartmentViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsCompanyManager]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return DepartmentCreateSerializer
        return ReadOnlyDepartmentSerializer

    def get_queryset(self):
        return Department.objects.filter(company_id=self.kwargs["company_pk"])

    @override
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EmployeeViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsCompanyManager]

    def get_serializer_class(self):
        if self.action == "create":
            return EmployeeCreateSerializer
        if self.action in ["update", "partial_update"]:
            return EmployeeUpdateSerializer
        return ReadOnlyEmployeeSerializer

    def get_queryset(self):
        return Employee.objects.filter(department__company_id=self.kwargs["company_pk"])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def update_status(self, request, company_pk=None, pk=None):
        """Special endpoint for updating employee status."""
        employee = self.get_object()

        if employee.department.company.manager != request.user:
            raise PermissionDenied(
                "You do not have permission to update this employee's status"
            )

        serializer = EmployeeUpdateSerializer(
            employee,
            data={"status": request.data.get("status")},
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
