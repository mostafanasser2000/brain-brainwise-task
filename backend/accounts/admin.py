# In admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("username", "email", "role", "first_name", "last_name")

    def save(self, commit=True):
        user = super().save(commit=False)
        if user.role == "admin":
            user.is_superuser = True
            user.is_staff = True
        elif user.role == "manager":
            user.is_staff = True

        if commit:
            user.save()
        return user


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = UserChangeForm
    model = CustomUser
    list_display = (
        "username",
        "email",
        "role_display",
        "first_name",
        "last_name",
        "is_active",
    )
    list_filter = ("role", "is_active")
    fieldsets = (
        (None, {"fields": ("username", "email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("role", "is_active", "is_staff", "is_superuser")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "first_name",
                    "last_name",
                    "role",
                ),
            },
        ),
    )
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)


admin.site.register(CustomUser, CustomUserAdmin)
