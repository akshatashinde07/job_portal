import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Profile
from .models import Application, Job


class JobPortalFlowTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        self.media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_settings.enable()
        self.addCleanup(self.media_settings.disable)

        self.employer = User.objects.create_user(
            username="demo_employer",
            password="TestPassword!92",
        )
        Profile.objects.create(user=self.employer, role=Profile.EMPLOYER, company="Northstar")
        self.seeker = User.objects.create_user(
            username="demo_seeker",
            password="TestPassword!92",
        )
        Profile.objects.create(user=self.seeker, role=Profile.SEEKER)
        self.job = Job.objects.create(
            title="Python Developer",
            company="Northstar",
            location="Pune",
            employment_type="full_time",
            description="Build useful tools with Python.",
            skills="Python, Django",
            employer=self.employer,
        )

    def test_home_search_and_filters_return_matching_jobs(self):
        response = self.client.get(
            reverse("home"),
            {"q": "Python", "location": "Pune", "type": "full_time"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python Developer")
        self.assertContains(response, "Northstar")

    def test_employer_can_post_a_job_and_job_is_owned_by_them(self):
        self.client.force_login(self.employer)
        response = self.client.post(
            reverse("job_create"),
            {
                "title": "Backend Engineer",
                "company": "Northstar",
                "location": "Pune",
                "employment_type": "full_time",
                "salary_min": "600000",
                "salary_max": "900000",
                "description": "Build and maintain APIs.",
                "skills": "Python, PostgreSQL",
            },
        )
        posted = Job.objects.get(title="Backend Engineer")
        self.assertRedirects(response, reverse("job_detail", args=[posted.pk]))
        self.assertEqual(posted.employer, self.employer)

    def test_seeker_cannot_post_a_job(self):
        self.client.force_login(self.seeker)
        response = self.client.get(reverse("job_create"))
        self.assertEqual(response.status_code, 403)

    def test_resume_is_required_and_valid_application_is_saved(self):
        self.client.force_login(self.seeker)
        url = reverse("apply_to_job", args=[self.job.pk])

        missing_resume = self.client.post(url, {"cover_letter": "I am interested."})
        self.assertEqual(missing_resume.status_code, 200)
        self.assertIn("resume_file", missing_resume.context["form"].errors)
        self.assertEqual(Application.objects.count(), 0)

        resume = SimpleUploadedFile("resume.pdf", b"%PDF-demo resume", content_type="application/pdf")
        response = self.client.post(
            url,
            {"cover_letter": "I am interested.", "resume_file": resume},
        )
        self.assertRedirects(response, reverse("dashboard"))
        application = Application.objects.get(job=self.job, applicant=self.seeker)
        self.assertTrue(application.resume_file.name.endswith("resume.pdf"))

    def test_duplicate_application_is_blocked(self):
        self.client.force_login(self.seeker)
        resume = SimpleUploadedFile("resume.pdf", b"%PDF-demo resume", content_type="application/pdf")
        self.client.post(
            reverse("apply_to_job", args=[self.job.pk]),
            {"resume_file": resume},
        )
        second_resume = SimpleUploadedFile("resume2.pdf", b"%PDF-demo resume", content_type="application/pdf")
        response = self.client.post(
            reverse("apply_to_job", args=[self.job.pk]),
            {"resume_file": second_resume},
        )
        self.assertRedirects(response, reverse("job_detail", args=[self.job.pk]))
        self.assertEqual(Application.objects.filter(job=self.job, applicant=self.seeker).count(), 1)

    def test_only_applicant_employer_or_staff_can_download_resume(self):
        resume = SimpleUploadedFile("resume.pdf", b"%PDF-demo resume", content_type="application/pdf")
        application = Application.objects.create(
            job=self.job,
            applicant=self.seeker,
            resume_file=resume,
        )
        url = reverse("resume_download", args=[application.pk])

        self.client.force_login(self.employer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Disposition"].startswith("attachment;"))
        response.close()

        unrelated = User.objects.create_user(username="other_seeker", password="TestPassword!92")
        Profile.objects.create(user=unrelated, role=Profile.SEEKER)
        self.client.force_login(unrelated)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_employer_can_update_status_but_seeker_cannot(self):
        application = Application.objects.create(job=self.job, applicant=self.seeker)
        url = reverse("application_status", args=[application.pk])

        self.client.force_login(self.employer)
        response = self.client.post(url, {"status": Application.STATUS_INTERVIEW})
        self.assertRedirects(response, reverse("dashboard"))
        application.refresh_from_db()
        self.assertEqual(application.status, Application.STATUS_INTERVIEW)

        self.client.force_login(self.seeker)
        self.assertEqual(
            self.client.post(url, {"status": Application.STATUS_OFFER}).status_code,
            403,
        )
