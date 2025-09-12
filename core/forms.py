from django import forms
from .models import Comment, Patient

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