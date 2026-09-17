"""
Plain JSON endpoints (no DRF needed) for the three grading twists:

  T1  POST /clock    -> advance/set the virtual 'today', notify who's due
      GET  /outbox    -> see what got queued
  T6  POST /subscriptions/<id>/transfer    -> move ownership mid-cycle
      GET  /subscriptions/<id>/bill-split  -> billing split by owner
  T4  POST /import    -> bulk-clean a messy customer list
"""
import json
from datetime import datetime

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Customer, OutboxNotification, Plan, SimClock, Subscription
from .services import NotificationService

DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y/%m/%d"]


def _parse_date_flex(value):
    """Parse a date allowing several common formats. Returns None if
    blank/unparseable — callers decide whether that's a rejection or a
    fallback."""
    if value is None:
        return None
    value = str(value).strip()
    if not value:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _normalize_phone(raw):
    if not raw:
        return ""
    return "".join(ch for ch in str(raw) if ch.isdigit() or ch == "+")


def _json_body(request):
    try:
        return json.loads(request.body or "{}"), None
    except json.JSONDecodeError:
        return None, JsonResponse({"error": "invalid JSON body"}, status=400)


# ---------------------------------------------------------------- T1 ----

@csrf_exempt
@require_http_methods(["POST"])
def clock_advance(request):
    """POST /clock
    Body (optional JSON): {"date": "YYYY-MM-DD"}
      - if given: jump the virtual clock to this date
      - if omitted: advance by one day
    Then runs the morning routine: notify every customer whose
    subscription is active, due today (weekday, or weekend if the plan
    allows it), and not paused.
    """
    payload, err = _json_body(request)
    if err:
        return err

    date_str = payload.get("date")
    if date_str:
        new_date = _parse_date_flex(date_str)
        if not new_date:
            return JsonResponse({"error": f"could not parse date '{date_str}'"}, status=400)
        SimClock.set_today(new_date)
    else:
        new_date = SimClock.advance(days=1)

    notified = 0
    subs = Subscription.objects.filter(
        status=Subscription.STATUS_ACTIVE
    ).select_related("customer", "plan")

    for sub in subs:
        if sub.start_date > new_date:
            continue
        if sub.end_date and sub.end_date < new_date:
            continue
        if not sub._is_delivery_day(new_date):
            continue
        if sub.is_paused_on(new_date):
            continue
        owner = sub.owner_on(new_date)
        NotificationService.notify_delivery_today(sub, owner, new_date)
        notified += 1

    return JsonResponse({"date": new_date.isoformat(), "notified": notified})


@require_http_methods(["GET"])
def outbox_list(request):
    """GET /outbox  (optional ?date=YYYY-MM-DD filter)"""
    qs = OutboxNotification.objects.select_related("customer", "subscription")
    date_str = request.GET.get("date")
    if date_str:
        d = _parse_date_flex(date_str)
        if d:
            qs = qs.filter(delivery_date=d)

    results = [
        {
            "id": n.id,
            "customer_id": n.customer_id,
            "customer": n.customer.name,
            "phone": n.customer.phone,
            "subscription_id": n.subscription_id,
            "channel": n.channel,
            "message": n.message,
            "delivery_date": n.delivery_date.isoformat(),
            "created_at": n.created_at.isoformat(),
        }
        for n in qs
    ]
    return JsonResponse({"count": len(results), "results": results})


# ---------------------------------------------------------------- T6 ----

@csrf_exempt
@require_http_methods(["POST"])
def transfer_subscription(request, sub_pk):
    """POST /subscriptions/<id>/transfer
    Body: {"to_phone": "..."} or {"to_customer_id": N}, plus "transfer_date".
    Plan and billing cycle carry over unchanged; only ownership moves.
    """
    subscription = get_object_or_404(Subscription, pk=sub_pk)
    payload, err = _json_body(request)
    if err:
        return err

    transfer_date = _parse_date_flex(payload.get("transfer_date"))
    if not transfer_date:
        return JsonResponse({"error": "a valid transfer_date is required"}, status=400)

    to_customer = None
    if payload.get("to_customer_id"):
        to_customer = Customer.objects.filter(pk=payload["to_customer_id"]).first()
    elif payload.get("to_phone"):
        to_customer = Customer.objects.filter(phone=_normalize_phone(payload["to_phone"])).first()

    if not to_customer:
        return JsonResponse(
            {"error": "target customer not found — pass to_customer_id or to_phone"}, status=404
        )

    try:
        transfer = subscription.transfer_to(to_customer, transfer_date)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({
        "subscription_id": subscription.pk,
        "from_customer": transfer.from_customer.name,
        "to_customer": transfer.to_customer.name,
        "transfer_date": transfer.transfer_date.isoformat(),
    }, status=201)


@require_http_methods(["GET"])
def bill_split(request, sub_pk):
    """GET /subscriptions/<id>/bill-split?year=YYYY&month=MM
    Pro-rated bill split by whoever was actually served each day."""
    subscription = get_object_or_404(Subscription, pk=sub_pk)
    try:
        year = int(request.GET["year"])
        month = int(request.GET["month"])
    except (KeyError, ValueError):
        return JsonResponse({"error": "year and month query params are required"}, status=400)

    result = subscription.calculate_bill_split(year, month)
    return JsonResponse({
        "subscription_id": subscription.pk,
        "total_days": result["total_days"],
        "per_day_rate": str(result["per_day_rate"]),
        "breakdown": [
            {
                "customer_id": item["customer"].pk,
                "customer": item["customer"].name,
                "delivered_days": item["delivered_days"],
                "amount": str(item["amount"]),
            }
            for item in result["breakdown"]
        ],
    })


# ---------------------------------------------------------------- T4 ----

@csrf_exempt
@require_http_methods(["POST"])
def import_customers(request):
    """POST /import
    Body: {"rows": [{"name": "...", "phone": "...", "start_date": "...",
                      "plan": "...", "address": "..."}, ...]}

    Cleans messy input into Customer + Subscription records:
      - blank name/phone, or phone too short              -> rejected
      - phone already seen (in this batch or in DB)        -> deduped
      - date parsed from several common formats; blank     -> defaults to today
      - unknown/blank plan name                            -> falls back to
                                                                the first Plan
    Returns {"imported", "deduped", "rejected", "details": {...}}.
    """
    payload, err = _json_body(request)
    if err:
        return err

    rows = payload.get("rows", [])
    default_plan = Plan.objects.first()

    imported = deduped = rejected = 0
    rejected_rows = []
    seen_phones = set()

    for idx, row in enumerate(rows):
        name = (row.get("name") or "").strip()
        phone = _normalize_phone(row.get("phone"))
        address = (row.get("address") or "").strip()
        start_date = _parse_date_flex(row.get("start_date")) or SimClock.today()

        if not name or not phone or len(phone) < 7:
            rejected += 1
            rejected_rows.append({"row": idx, "reason": "missing/invalid name or phone", "data": row})
            continue

        if phone in seen_phones or Customer.objects.filter(phone=phone).exists():
            deduped += 1
            continue
        seen_phones.add(phone)

        plan = default_plan
        plan_name = (row.get("plan") or "").strip()
        if plan_name:
            plan = Plan.objects.filter(name__iexact=plan_name).first() or default_plan

        if not plan:
            rejected += 1
            rejected_rows.append({"row": idx, "reason": "no plan available to assign", "data": row})
            continue

        customer = Customer.objects.create(name=name, phone=phone, address=address)
        Subscription.objects.create(customer=customer, plan=plan, start_date=start_date)
        imported += 1

    return JsonResponse({
        "imported": imported,
        "deduped": deduped,
        "rejected": rejected,
        "details": {"rejected_rows": rejected_rows},
    })
