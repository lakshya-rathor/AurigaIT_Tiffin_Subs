from datetime import date

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    BillMonthForm, CustomerForm, PauseForm, PhoneLookupForm, ResumeForm, SubscribeForm,
)
from .models import Bill, Customer, Pause, Subscription


def dashboard(request):
    """Home screen: everyone at a glance, active vs paused, plus phone search."""
    subscriptions = Subscription.objects.select_related("customer", "plan").exclude(
        status=Subscription.STATUS_CANCELLED
    )

    active, paused = [], []
    for sub in subscriptions:
        (paused if sub.is_currently_paused() else active).append(sub)

    lookup_form = PhoneLookupForm(request.GET or None)
    found_customer = None
    if request.GET.get("phone"):
        if lookup_form.is_valid():
            phone = lookup_form.cleaned_data["phone"].strip()
            found_customer = Customer.objects.filter(phone__icontains=phone).first()
            if not found_customer:
                messages.info(request, f"No customer found with phone containing '{phone}'.")

    return render(request, "subscriptions/dashboard.html", {
        "active": active,
        "paused": paused,
        "lookup_form": lookup_form,
        "found_customer": found_customer,
        "today": timezone.localdate(),
    })


def customer_new(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f"Customer '{customer.name}' added.")
            return redirect("subscriptions:customer_detail", pk=customer.pk)
    else:
        form = CustomerForm()
    return render(request, "subscriptions/customer_form.html", {"form": form, "mode": "new"})


def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    subscriptions = customer.subscriptions.select_related("plan").prefetch_related("pauses", "bills")
    return render(request, "subscriptions/customer_detail.html", {
        "customer": customer,
        "subscriptions": subscriptions,
        "today": timezone.localdate(),
    })


def subscribe(request, customer_pk):
    customer = get_object_or_404(Customer, pk=customer_pk)
    if request.method == "POST":
        form = SubscribeForm(request.POST)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.customer = customer
            sub.save()
            messages.success(request, f"{customer.name} subscribed to {sub.plan.name}.")
            return redirect("subscriptions:customer_detail", pk=customer.pk)
    else:
        form = SubscribeForm()
    return render(request, "subscriptions/subscribe_form.html", {"form": form, "customer": customer})


def pause_subscription(request, sub_pk):
    subscription = get_object_or_404(Subscription, pk=sub_pk)
    if request.method == "POST":
        form = PauseForm(request.POST)
        if form.is_valid():
            pause = form.save(commit=False)
            pause.subscription = subscription
            pause.save()
            messages.success(request, "Pause recorded. These days won't be billed.")
            return redirect("subscriptions:customer_detail", pk=subscription.customer.pk)
    else:
        form = PauseForm(initial={"start_date": timezone.localdate()})
    return render(request, "subscriptions/pause_form.html", {"form": form, "subscription": subscription})


def resume_subscription(request, pause_pk):
    pause = get_object_or_404(Pause, pk=pause_pk)
    if request.method == "POST":
        form = ResumeForm(request.POST)
        if form.is_valid():
            pause.resume(form.cleaned_data.get("resume_date"))
            messages.success(request, "Subscription resumed. Delivery continues.")
            return redirect("subscriptions:customer_detail", pk=pause.subscription.customer.pk)
    else:
        form = ResumeForm()
    return render(request, "subscriptions/resume_form.html", {"form": form, "pause": pause})


def generate_bill(request, sub_pk):
    """Calculate (and store) the pro-rated bill for a chosen month."""
    subscription = get_object_or_404(Subscription, pk=sub_pk)
    result = None
    today = timezone.localdate()

    if request.method == "POST":
        form = BillMonthForm(request.POST)
        if form.is_valid():
            year = form.cleaned_data["year"]
            month = int(form.cleaned_data["month"])
            calc = subscription.calculate_bill(year, month)
            bill, _created = Bill.objects.update_or_create(
                subscription=subscription, year=year, month=month,
                defaults={
                    "total_days": calc["total_days"],
                    "delivered_days": calc["delivered_days"],
                    "per_day_rate": calc["per_day_rate"],
                    "amount": calc["amount"],
                },
            )
            result = bill
            messages.success(request, f"Bill for {month}/{year}: Rs.{bill.amount}")
    else:
        form = BillMonthForm(initial={"month": today.month, "year": today.year})

    return render(request, "subscriptions/generate_bill.html", {
        "form": form, "subscription": subscription, "result": result,
    })
