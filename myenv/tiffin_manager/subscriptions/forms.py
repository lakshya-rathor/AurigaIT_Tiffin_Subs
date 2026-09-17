from django import forms
from .models import Customer, Plan, Subscription, Pause


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ["name", "phone", "address"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Full name"}),
            "phone": forms.TextInput(attrs={"placeholder": "e.g. 9876543210"}),
            "address": forms.TextInput(attrs={"placeholder": "Delivery address"}),
        }


class SubscribeForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ["plan", "start_date"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
        }


class PauseForm(forms.ModelForm):
    class Meta:
        model = Pause
        fields = ["start_date", "end_date", "reason"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "reason": forms.TextInput(attrs={"placeholder": "e.g. travelling, festival"}),
        }
        help_texts = {
            "end_date": "Leave blank if you don't know the return date yet — resume later to close it.",
        }


class ResumeForm(forms.Form):
    resume_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"}),
        required=False,
        help_text="Defaults to today if left blank.",
    )


class PhoneLookupForm(forms.Form):
    phone = forms.CharField(
        max_length=16,
        widget=forms.TextInput(attrs={"placeholder": "Search by phone number", "autofocus": True}),
    )


class BillMonthForm(forms.Form):
    MONTH_CHOICES = [(i, m) for i, m in enumerate(
        ["January", "February", "March", "April", "May", "June",
         "July", "August", "September", "October", "November", "December"], start=1
    )]
    month = forms.ChoiceField(choices=MONTH_CHOICES)
    year = forms.IntegerField(min_value=2000, max_value=2100)
