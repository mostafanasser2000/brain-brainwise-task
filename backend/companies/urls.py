from rest_framework_nested.routers import DefaultRouter, NestedDefaultRouter

from . import views

router = DefaultRouter()

router.register("companies", views.CompanyViewSet, basename="companies")

companies_router = NestedDefaultRouter(router, "companies", lookup="company")
companies_router.register(
    "departments", views.DepartmentViewSet, basename="company-departments"
)

departments_router = NestedDefaultRouter(
    companies_router, "departments", lookup="department"
)
departments_router.register(
    "employees", views.EmployeeViewSet, basename="department-employees"
)


urlpatterns = router.urls + companies_router.urls + departments_router.urls
