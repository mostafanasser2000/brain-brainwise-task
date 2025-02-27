from rest_framework.permissions import BasePermission

from .models import Company


class IsMangerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        return request.user.role == "manager"

    def has_object_permission(self, request, view, obj):
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return True
        return obj.manager == request.user


class IsCompanyManager(BasePermission):
    def has_permission(self, request, view):
        try:
            company_id = int(view.kwargs["company_pk"])
            return Company.objects.filter(pk=company_id, manager=request.user).exists()
        except (ValueError, Company.DoesNotExist):
            return False
