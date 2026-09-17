from django.urls import path
from . import views

app_name = "subscriptions"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("customers/new/", views.customer_new, name="customer_new"),
    path("customers/<int:pk>/", views.customer_detail, name="customer_detail"),
    path("customers/<int:customer_pk>/subscribe/", views.subscribe, name="subscribe"),
    path("subscriptions/<int:sub_pk>/pause/", views.pause_subscription, name="pause"),
    path("pauses/<int:pause_pk>/resume/", views.resume_subscription, name="resume"),
    path("subscriptions/<int:sub_pk>/bill/", views.generate_bill, name="generate_bill"),
]
