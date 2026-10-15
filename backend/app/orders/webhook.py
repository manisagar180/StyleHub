import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models import CartItem, Order, OrderItem, Product
router = APIRouter(prefix="/api/payments", tags=["Payments"])
@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    if (
        not settings.stripe_webhook_secret
        or settings.stripe_webhook_secret.startswith("whsec_REPLACE")
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe webhook secret is not configured.",
        )
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature.",
        )
    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            settings.stripe_webhook_secret,
        )
    except (ValueError, stripe.SignatureVerificationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe webhook signature or payload.",
        ) from exc
    # Convert Stripe SDK objects to ordinary dictionaries before using .get().
    event_data = event.to_dict()
    event_type = event_data.get("type")
    intent = (event_data.get("data") or {}).get("object") or {}
    supported_events = {
        "payment_intent.succeeded",
        "payment_intent.payment_failed",
        "payment_intent.canceled",
    }
    if event_type not in supported_events:
        return {"received": True, "handled": False}
    intent_id = intent.get("id")
    if not intent_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe event has no PaymentIntent ID.",
        )
    order = (
        db.query(Order)
        .filter(Order.stripe_payment_intent_id == intent_id)
        .with_for_update()
        .first()
    )
    if order is None:
        return {"received": True, "handled": False}
    metadata = intent.get("metadata") or {}
    expected_amount = int(
        (order.total_amount * 100)
    )
    if (
        metadata.get("order_id") != str(order.id)
        or metadata.get("user_id") != str(order.user_id)
        or intent.get("currency", "").lower() != order.currency.lower()
        or intent.get("amount") != expected_amount
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment details do not match the order.",
        )
    # Idempotency: never process a successful order twice.
    if order.status == "SUCCESS":
        return {"received": True, "handled": True}
    if event_type == "payment_intent.payment_failed":
        # A failed payment attempt may be retried by the customer.
        return {"received": True, "handled": True}
    if event_type == "payment_intent.canceled":
        try:
            if order.inventory_reserved:
                items = (
                    db.query(OrderItem)
                    .filter(OrderItem.order_id == order.id)
                    .all()
                )
                for item in items:
                    product = (
                        db.query(Product)
                        .filter(Product.id == item.product_id)
                        .first()
                    )
                    if product is not None:
                        product.stock += item.quantity
                order.inventory_reserved = False
            order.status = "FAILED"
            db.commit()
        except Exception:
            db.rollback()
            raise
        return {"received": True, "handled": True}
    if intent.get("status") != "succeeded":
        return {"received": True, "handled": False}
    if intent.get("amount_received") != expected_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The received payment amount does not match the order.",
        )
    if not order.inventory_reserved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Order inventory is not reserved; manual reconciliation is required.",
        )
    try:
        items = (
            db.query(OrderItem)
            .filter(OrderItem.order_id == order.id)
            .all()
        )
        if not items:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Order has no items; manual reconciliation is required.",
            )
        # Inventory was reserved when the order was created.
        # Remove matching cart items, but do not decrement stock again.
        for item in items:
            cart_item = (
                db.query(CartItem)
                .filter(
                    CartItem.user_id == order.user_id,
                    CartItem.product_id == item.product_id,
                )
                .first()
            )
            if cart_item is not None:
                db.delete(cart_item)
        order.status = "SUCCESS"
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"received": True, "handled": True}