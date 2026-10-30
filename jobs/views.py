from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from pathlib import Path

from .forms import ApplicationForm, ApplicationStatusForm, JobForm
from .models import Application, Job


def job_list(request):
    jobs = Job.objects.filter(is_active=True).select_related("employer")
    query = request.GET.get("q", "").strip()[:100]
    location = request.GET.get("location", "").strip()[:100]
    employment_type = request.GET.get("type", "").strip()

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query)
            | Q(company__icontains=query)
            | Q(skills__icontains=query)
            | Q(description__icontains=query)
        )
    if location:
        jobs = jobs.filter(location__icontains=location)
    if employment_type in dict(Job.EMPLOYMENT_TYPES):
        jobs = jobs.filter(employment_type=employment_type)

    page_obj = Paginator(jobs, 9).get_page(request.GET.get("page"))
    return render(
        request,
        "jobs/home.html",
        {
            "page_obj": page_obj,
            "query": query,
            "location": location,
            "selected_type": employment_type,
            "employment_types": Job.EMPLOYMENT_TYPES,
        },
    )


def job_detail(request, pk):
    job = get_object_or_404(
        Job.objects.select_related("employer"),
        pk=pk,
        is_active=True,
    )
    already_applied = False
    is_owner = False
    is_seeker = False
    if request.user.is_authenticated:
        already_applied = Application.objects.filter(
            job=job,
            applicant=request.user,
        ).exists()
        is_owner = job.employer_id == request.user.id
        profile = getattr(request.user, "profile", None)
        is_seeker = bool(profile and profile.role == "seeker")

    return render(
        request,
        "jobs/job_detail.html",
        {
            "job": job,
            "already_applied": already_applied,
            "is_owner": is_owner,
            "is_seeker": is_seeker,
        },
    )


@login_required
def create_job(request):
    profile = getattr(request.user, "profile", None)
    if not request.user.is_staff and (
        profile is None or profile.role != "employer"
    ):
        return HttpResponseForbidden("Only employer accounts can post jobs.")

    form = JobForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        job = form.save(commit=False)
        job.employer = request.user
        job.save()
        messages.success(request, "Job posted successfully.")
        return redirect("job_detail", pk=job.pk)

    return render(request, "jobs/job_form.html", {"form": form})


@login_required
def apply_to_job(request, pk):
    job = get_object_or_404(Job, pk=pk, is_active=True)
    profile = getattr(request.user, "profile", None)
    if profile is None or profile.role != "seeker":
        return HttpResponseForbidden("Only job seeker accounts can apply.")
    if job.employer_id == request.user.id:
        return HttpResponseForbidden("You cannot apply to your own job posting.")
    if Application.objects.filter(job=job, applicant=request.user).exists():
        messages.info(request, "You have already applied for this job.")
        return redirect("job_detail", pk=job.pk)

    form = ApplicationForm(request.POST, request.FILES) if request.method == "POST" else ApplicationForm()
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                application = form.save(commit=False)
                application.job = job
                application.applicant = request.user
                application.save()
        except IntegrityError:
            messages.info(request, "You have already applied for this job.")
            return redirect("job_detail", pk=job.pk)

        messages.success(request, "Your application has been submitted.")
        return redirect("dashboard")

    return render(request, "jobs/application_form.html", {"form": form, "job": job})


@login_required
@require_POST
def update_application_status(request, pk):
    application = get_object_or_404(
        Application.objects.select_related("job"),
        pk=pk,
    )
    profile = getattr(request.user, "profile", None)
    is_authorized = request.user.is_staff or (
        profile is not None
        and profile.role == "employer"
        and application.job.employer_id == request.user.id
    )
    if not is_authorized:
        return HttpResponseForbidden("You cannot update this application.")

    form = ApplicationStatusForm(request.POST, instance=application)
    if form.is_valid():
        form.save()
        messages.success(request, "Application status updated.")
    else:
        messages.error(request, "Choose a valid application status.")
    return redirect("dashboard")


@login_required
def download_resume(request, pk):
    application = get_object_or_404(
        Application.objects.select_related("job", "applicant"),
        pk=pk,
    )
    profile = getattr(request.user, "profile", None)
    is_authorized = (
        request.user.is_staff
        or application.applicant_id == request.user.id
        or (
            profile is not None
            and profile.role == "employer"
            and application.job.employer_id == request.user.id
        )
    )
    if not is_authorized:
        return HttpResponseForbidden("You cannot view this resume.")
    if not application.resume_file:
        raise Http404("No resume is attached to this application.")

    return FileResponse(
        application.resume_file.open("rb"),
        as_attachment=True,
        filename=Path(application.resume_file.name).name,
    )
