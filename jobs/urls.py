from django.urls import path

from . import views

urlpatterns = [
    path("new/", views.create_job, name="job_create"),
    path("<int:pk>/", views.job_detail, name="job_detail"),
    path("<int:pk>/apply/", views.apply_to_job, name="apply_to_job"),
    path(
        "applications/<int:pk>/status/",
        views.update_application_status,
        name="application_status",
    ),
    path(
        "applications/<int:pk>/resume/",
        views.download_resume,
        name="resume_download",
    ),
]
