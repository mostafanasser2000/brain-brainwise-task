from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Company, Department, Employee


class DepartmentInline(admin.TabularInline):
    model = Department
    extra = 1
    fields = ['name', 'get_employees_count']
    readonly_fields = ['get_employees_count']

    def get_employees_count(self, obj):
        if obj.id:
            return obj.get_employees_count()
        return 0
    get_employees_count.short_description = 'Employees'


class EmployeeInline(admin.TabularInline):
    model = Employee
    extra = 1
    fields = ['first_name', 'last_name', 'email', 'status', 'designation']
    readonly_fields = ['status']


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'manager', 'departments_count', 'employees_count', 'created_at']
    list_filter = ['created_at', 'updated_at', 'manager']
    search_fields = ['name', 'manager__username', 'manager__email']
    readonly_fields = ['created_at', 'updated_at', 'departments_count', 'employees_count']
    inlines = [DepartmentInline]
    fieldsets = [
        ('Company Information', {
            'fields': ['name', 'manager']
        }),
        ('Statistics', {
            'fields': ['departments_count', 'employees_count']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]

    def departments_count(self, obj):
        return obj.departments.count()
    departments_count.short_description = 'Departments'

    def employees_count(self, obj):
        return obj.get_employees_count()
    employees_count.short_description = 'Total Employees'


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'company_link', 'employees_count', 'created_at']
    list_filter = ['created_at', 'company']
    search_fields = ['name', 'company__name']
    readonly_fields = ['created_at', 'updated_at', 'employees_count']
    inlines = [EmployeeInline]
    fieldsets = [
        ('Department Information', {
            'fields': ['name', 'company']
        }),
        ('Statistics', {
            'fields': ['employees_count']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]

    def company_link(self, obj):
        url = reverse('admin:companies_company_change', args=[obj.company.id])
        return format_html('<a href="{}">{}</a>', url, obj.company.name)
    company_link.short_description = 'Company'

    def employees_count(self, obj):
        return obj.get_employees_count()
    employees_count.short_description = 'Employees'


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'email', 'department_link', 'company_name', 'status', 'hired_on']
    list_filter = ['status', 'hired_on', 'department__company', 'department']
    search_fields = ['first_name', 'last_name', 'email', 'department__name', 'department__company__name']
    readonly_fields = ['created_at', 'updated_at', 'company_name']
    fieldsets = [
        ('Personal Information', {
            'fields': ['first_name', 'last_name', 'email', 'phone_number']
        }),
        ('Employment Details', {
            'fields': ['department', 'designation', 'status', 'hired_on', 'company_name']
        }),
        ('Address', {
            'fields': ['address'],
            'classes': ['collapse']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    def full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'
    full_name.short_description = 'Name'

    def department_link(self, obj):
        url = reverse('admin:companies_department_change', args=[obj.department.id])
        return format_html('<a href="{}">{}</a>', url, obj.department.name)
    department_link.short_description = 'Department'

    def company_name(self, obj):
        return obj.department.company.name
    company_name.short_description = 'Company'