from django import forms
from .models import Comment, Patient, Report

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["name",  "text"]

class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ["name", "phone", "age", "gender"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Full Name"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone Number"}),
            "age": forms.NumberInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-control"}),
        }
        
class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["title", "description", "notes", "content"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Short description of findings"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Additional notes for patient/records"}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 6, "placeholder": "Detailed report content"}),
        }
