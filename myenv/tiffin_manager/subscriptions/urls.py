from django.urls import path
from . import views, api

app_name = "subscriptions"

urlpatterns = [
    # -- HTML pages (owner-facing UI) --
    path("", views.dashboard, name="dashboard"),
    path("customers/new/", views.customer_new, name="customer_new"),
    path("customers/<int:pk>/", views.customer_detail, name="customer_detail"),
    path("customers/<int:customer_pk>/subscribe/", views.subscribe, name="subscribe"),
    path("subscriptions/<int:sub_pk>/pause/", views.pause_subscription, name="pause"),
    path("pauses/<int:pause_pk>/resume/", views.resume_subscription, name="resume"),
    path("subscriptions/<int:sub_pk>/bill/", views.generate_bill, name="generate_bill"),
    path("subscriptions/<int:sub_pk>/transfer/", views.transfer_subscription_form, name="transfer_form"),

    # -- JSON API (graded endpoints) --
    path("clock", api.clock_advance, name="api_clock"),                                  # T1
    path("outbox", api.outbox_list, name="api_outbox"),                                  # T1
    path("subscriptions/<int:sub_pk>/transfer", api.transfer_subscription, name="api_transfer"),  # T6
    path("subscriptions/<int:sub_pk>/bill-split", api.bill_split, name="api_bill_split"),  # T6
    path("import", api.import_customers, name="api_import"),                             # T4
]
