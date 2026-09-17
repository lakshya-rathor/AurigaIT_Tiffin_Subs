import calendar
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


phone_validator = RegexValidator(
    regex=r"^\+?\d{7,15}$",
    message="Enter a valid phone number (7-15 digits, optional leading +)."
)


class Customer(models.Model):
    name = models.CharField(max_length=120)
    phone = models.CharField(
        max_length=16, unique=True, validators=[phone_validator],
        help_text="Used to look up the customer. Must be unique."
    )
    address = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.phone})"


class Plan(models.Model):
    name = models.CharField(max_length=80)
    price_per_month = models.DecimalField(max_digits=8, decimal_places=2)
    delivers_on_weekends = models.BooleanField(
        default=False,
        help_text="If unchecked (typical), tiffin is delivered Mon-Fri only."
    )

    def __str__(self):
        return f"{self.name} - Rs.{self.price_per_month}/month"


class Subscription(models.Model):
    STATUS_ACTIVE = "active"
    STATUS_PAUSED = "paused"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_PAUSED, "Paused"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(null=True, blank=True, help_text="Set when cancelled.")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer.name} - {self.plan.name} [{self.status}]"

    # ---------- core scheduling helpers ----------

    def _is_delivery_day(self, d: date) -> bool:
        if self.plan.delivers_on_weekends:
            return True
        return d.weekday() < 5  # Mon=0 ... Fri=4

    def delivery_days_in_month(self, year: int, month: int):
        """All calendar days in the month on which this plan delivers,
        restricted to the subscription's active window."""
        first_day = date(year, month, 1)
        last_day_num = calendar.monthrange(year, month)[1]
        last_day = date(year, month, last_day_num)

        window_start = max(first_day, self.start_date)
        window_end = min(last_day, self.end_date) if self.end_date else last_day
        if window_start > window_end:
            return []

        days = []
        d = window_start
        while d <= window_end:
            if self._is_delivery_day(d):
                days.append(d)
            d += timedelta(days=1)
        return days

    def paused_dates_in_month(self, year: int, month: int):
        """Set of dates covered by any Pause record that overlap this month."""
        first_day = date(year, month, 1)
        last_day_num = calendar.monthrange(year, month)[1]
        last_day = date(year, month, last_day_num)

        paused = set()
        for pause in self.pauses.all():
            p_start = pause.start_date
            p_end = pause.end_date or timezone.localdate()  # open pause counts up to today
            overlap_start = max(p_start, first_day)
            overlap_end = min(p_end, last_day)
            d = overlap_start
            while d <= overlap_end:
                paused.add(d)
                d += timedelta(days=1)
        return paused

    def delivered_days_in_month(self, year: int, month: int):
        all_days = self.delivery_days_in_month(year, month)
        paused = self.paused_dates_in_month(year, month)
        return [d for d in all_days if d not in paused]

    def is_currently_paused(self) -> bool:
        today = timezone.localdate()
        return self.pauses.filter(
            start_date__lte=today
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)
        ).exists()

    def current_display_status(self):
        if self.status == self.STATUS_CANCELLED:
            return "cancelled"
        if self.is_currently_paused():
            return "paused"
        return "active"

    # ---------- billing ----------

    def calculate_bill(self, year: int, month: int):
        """Pro-rate plan price by (delivered days / total possible delivery days)."""
        total_days = self.delivery_days_in_month(year, month)
        delivered_days = self.delivered_days_in_month(year, month)

        total_count = len(total_days)
        delivered_count = len(delivered_days)

        if total_count == 0:
            per_day = Decimal("0.00")
            amount = Decimal("0.00")
        else:
            per_day = (self.plan.price_per_month / Decimal(total_count)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            amount = (per_day * delivered_count).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        return {
            "total_days": total_count,
            "delivered_days": delivered_count,
            "per_day_rate": per_day,
            "amount": amount,
        }


class Pause(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="pauses")
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(null=True, blank=True, help_text="Leave blank for an open-ended pause; fill in on resume.")
    reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        end = self.end_date or "ongoing"
        return f"{self.subscription.customer.name}: {self.start_date} -> {end}"

    def resume(self, resume_date=None):
        self.end_date = (resume_date or timezone.localdate()) - timedelta(days=1)
        if self.end_date < self.start_date:
            self.end_date = self.start_date
        self.save()


class Bill(models.Model):
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="bills")
    year = models.IntegerField()
    month = models.IntegerField()
    total_days = models.IntegerField()
    delivered_days = models.IntegerField()
    per_day_rate = models.DecimalField(max_digits=8, decimal_places=2)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("subscription", "year", "month")
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"{self.subscription.customer.name} - {self.month}/{self.year}: Rs.{self.amount}"
