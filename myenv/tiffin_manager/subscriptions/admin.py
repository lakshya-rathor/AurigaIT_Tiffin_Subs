from django.contrib import admin
from .models import Customer, Plan, Subscription, Pause, Bill


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "address", "created_at")
    search_fields = ("name", "phone")


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price_per_month", "delivers_on_weekends")


class PauseInline(admin.TabularInline):
    model = Pause
    extra = 0


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("customer", "plan", "status", "start_date", "end_date")
    list_filter = ("status", "plan")
    search_fields = ("customer__name", "customer__phone")
    inlines = [PauseInline]


@admin.register(Pause)
class PauseAdmin(admin.ModelAdmin):
    list_display = ("subscription", "start_date", "end_date", "reason")


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ("subscription", "month", "year", "total_days", "delivered_days", "amount")
    list_filter = ("year", "month")
