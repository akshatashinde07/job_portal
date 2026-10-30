from django.conf import settings
from django.db import models


class Profile(models.Model):
    SEEKER = "seeker"
    EMPLOYER = "employer"

    ROLE_CHOICES = [
        (SEEKER, "Job seeker"),
        (EMPLOYER, "Employer"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=SEEKER,
    )
    company = models.CharField(max_length=150, blank=True)
    location = models.CharField(max_length=120, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"