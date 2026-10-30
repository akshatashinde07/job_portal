from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import redirect, render

from .forms import SignUpForm
from .models import Profile
from jobs.models import Application, Job


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Your account and seeker/employer profile were created.",
            )
            return redirect("login")
        messages.error(
            request,
            "Your account was not created. Review the form errors below and try again.",
        )
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


@login_required
def dashboard(request):
    profile = getattr(request.user, "profile", None)
    if request.user.is_staff:
        user_model = get_user_model()
        context = {
            "profile_count": Profile.objects.count(),
            "user_count": user_model.objects.count(),
            "job_count": Job.objects.count(),
            "application_count": Application.objects.count(),
        }
        return render(request, "jobs/admin_dashboard.html", context)

    if profile is None:
        messages.error(request, "This account has no job portal profile yet.")
        return redirect("home")

    if profile.role == "employer":
        jobs = Job.objects.filter(employer=request.user).annotate(
            application_count=Count("applications")
        )
        applications = (
            Application.objects.filter(job__employer=request.user)
            .select_related("job", "applicant")
        )
        return render(
            request,
            "jobs/employer_dashboard.html",
            {
                "jobs": jobs,
                "applications": applications[:20],
                "job_count": jobs.count(),
                "application_count": applications.count(),
                "open_job_count": jobs.filter(is_active=True).count(),
                "status_choices": Application.STATUS_CHOICES,
            },
        )

    applications = (
        Application.objects.filter(applicant=request.user)
        .select_related("job", "job__employer")
    )
    return render(
        request,
        "jobs/seeker_dashboard.html",
        {
            "applications": applications,
            "application_count": applications.count(),
            "reviewing_count": applications.filter(
                status=Application.STATUS_REVIEWING
            ).count(),
            "interview_count": applications.filter(
                status=Application.STATUS_INTERVIEW
            ).count(),
        },
    )
