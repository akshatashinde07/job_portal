from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

from .models import Application, Job


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = (
            "title",
            "company",
            "location",
            "employment_type",
            "salary_min",
            "salary_max",
            "description",
            "skills",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
            "skills": forms.TextInput(
                attrs={"placeholder": "Python, SQL, communication"}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        minimum = cleaned_data.get("salary_min")
        maximum = cleaned_data.get("salary_max")

        if minimum is not None and maximum is not None and maximum < minimum:
            self.add_error(
                "salary_max",
                "Maximum salary must be at least the minimum salary.",
            )

        return cleaned_data


class ApplicationForm(forms.ModelForm):
    resume_file = forms.FileField(
        required=True,
        validators=[FileExtensionValidator(["pdf", "doc", "docx"])],
        label="Resume (PDF, DOC, or DOCX; maximum 5 MB)",
    )

    class Meta:
        model = Application
        fields = ("resume_file", "cover_letter")
        widgets = {
            "cover_letter": forms.Textarea(
                attrs={"rows": 6, "placeholder": "Introduce yourself and your interest in this role."}
            ),
        }
        labels = {
            "cover_letter": "Cover letter (optional)",
        }

    def clean_resume_file(self):
        resume = self.cleaned_data["resume_file"]
        if resume.size > 5 * 1024 * 1024:
            raise ValidationError("Resume must be 5 MB or smaller.")
        return resume


class ApplicationStatusForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ("status",)
