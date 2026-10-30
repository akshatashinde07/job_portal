from django.contrib import admin
from .models import Application, Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "company",
        "location",
        "employment_type",
        "is_active",
        "created_at",
    )
    list_filter = ("employment_type", "is_active")
    search_fields = ("title", "company", "location", "skills")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "applicant", "status", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = (
        "job__title",
        "job__company",
        "applicant__username",
        "applicant__email",
    )
    autocomplete_fields = ("job", "applicant")
    readonly_fields = ("created_at", "updated_at")
