"""
Service-layer abstractions kept separate from views/models so they can be
swapped out later (e.g. NotificationService -> real Twilio/FCM client)
without touching business logic.
"""
from .models import OutboxNotification


class NotificationService:
    """In production this would call an SMS/push provider. Here it records
    to the Outbox table so delivery-day notifications are observable and
    testable via GET /outbox."""

    @staticmethod
    def notify_delivery_today(subscription, customer, delivery_date):
        message = (
            f"Hi {customer.name}, your {subscription.plan.name} tiffin "
            f"is on its way today ({delivery_date.isoformat()})."
        )
        return OutboxNotification.objects.create(
            customer=customer,
            subscription=subscription,
            channel="sms",
            message=message,
            delivery_date=delivery_date,
        )
