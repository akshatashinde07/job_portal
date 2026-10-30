from django.conf import settings
from django.db import models
from django.core.validators import FileExtensionValidator


class Job(models.Model):
    EMPLOYMENT_TYPES = [
        ("full_time", "Full-time"),
        ("part_time", "Part-time"),
        ("contract", "Contract"),
        ("internship", "Internship"),
    ]

    title = models.CharField(max_length=180)
    company = models.CharField(max_length=150)
    location = models.CharField(max_length=120)
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPES,
    )
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField()
    skills = models.CharField(
        max_length=300,
        blank=True,
        help_text="Enter skills separated by commas.",
    )
    employer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posted_jobs",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["is_active", "-created_at"],
                name="job_active_recent_idx",
            ),
        ]

    def __str__(self):
        return f"{self.title} at {self.company}"


class Application(models.Model):
    STATUS_APPLIED = "applied"
    STATUS_REVIEWING = "reviewing"
    STATUS_INTERVIEW = "interview"
    STATUS_REJECTED = "rejected"
    STATUS_OFFER = "offer"

    STATUS_CHOICES = [
        (STATUS_APPLIED, "Applied"),
        (STATUS_REVIEWING, "Reviewing"),
        (STATUS_INTERVIEW, "Interview"),
        (STATUS_REJECTED, "Not selected"),
        (STATUS_OFFER, "Offer"),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_applications",
    )
    cover_letter = models.TextField(blank=True)
    resume_url = models.URLField(blank=True)
    resume_file = models.FileField(
        upload_to="resumes/%Y/%m/",
        blank=True,
        validators=[FileExtensionValidator(["pdf", "doc", "docx"])],
    )
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default=STATUS_APPLIED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["job", "applicant"],
                name="unique_application_per_job",
            ),
        ]
        indexes = [
            models.Index(
                fields=["status", "-created_at"],
                name="application_status_recent_idx",
            ),
        ]

    def __str__(self):
        return f"{self.applicant.username} — {self.job.title}"
