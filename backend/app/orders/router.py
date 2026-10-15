from decimal import Decimal, ROUND_HALF_UP

import stripe
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import CartItem, Order, OrderItem, Product, User
from app.orders.schemas import OrderResponse, PaymentIntentResponse

router = APIRouter(prefix="/api/orders", tags=["Orders"])


def get_order_response(db: Session, order: Order) -> OrderResponse:
    items = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order.id)
        .order_by(OrderItem.id.asc())
        .all()
    )

    return OrderResponse(
        id=order.id,
        total_amount=order.total_amount,
        currency=order.currency,
        status=order.status,
        stripe_payment_intent_id=order.stripe_payment_intent_id,
        created_at=order.created_at,
        items=[
            {
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.subtotal,
            }
            for item in items
        ],
    )


def release_reserved_inventory(db: Session, order: Order) -> None:
    """Restore reserved stock at most once."""
    if not order.inventory_reserved:
        return

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


@router.post(
    "/",
    response_model=PaymentIntentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order_and_payment(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if (
        not settings.stripe_secret_key
        or settings.stripe_secret_key.startswith("sk_test_REPLACE")
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe test secret key is not configured.",
        )

    stripe.api_key = settings.stripe_secret_key

    cart_items = (
        db.query(CartItem)
        .filter(CartItem.user_id == current_user.id)
        .order_by(CartItem.id.asc())
        .all()
    )
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your cart is empty.",
        )

    cart_signature = sorted(
        (item.product_id, item.quantity) for item in cart_items
    )
    total_amount = Decimal("0.00")
    cart_products = {}

    # Validate the cart and calculate its current total before reusing an order.
    for cart_item in cart_items:
        product = (
            db.query(Product)
            .filter(
                Product.id == cart_item.product_id,
                Product.is_active.is_(True),
            )
            .first()
        )
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A product in your cart is unavailable.",
            )
        cart_products[product.id] = product
        total_amount += Decimal(str(product.price)) * cart_item.quantity

    amount_paise = int(
        (total_amount * 100).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )
    if amount_paise <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order total must be greater than zero.",
        )

    # Reuse a matching pending order so repeated Checkout clicks don't
    # create duplicate orders or reserve inventory a second time.
    pending_orders = (
        db.query(Order)
        .filter(
            Order.user_id == current_user.id,
            Order.status == "PENDING",
            Order.inventory_reserved.is_(True),
        )
        .order_by(Order.id.desc())
        .all()
    )

    for order in pending_orders:
        order_items = (
            db.query(OrderItem)
            .filter(OrderItem.order_id == order.id)
            .order_by(OrderItem.id.asc())
            .all()
        )
        order_signature = sorted(
            (item.product_id, item.quantity) for item in order_items
        )
        if (
            order_signature != cart_signature
            or Decimal(str(order.total_amount)) != total_amount
        ):
            continue

        try:
            if order.stripe_payment_intent_id:
                intent = stripe.PaymentIntent.retrieve(
                    order.stripe_payment_intent_id
                )

                if intent.status == "succeeded":
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            "This order has already been paid. "
                            "Refresh your order history before checking out again."
                        ),
                    )

                if intent.status == "canceled":
                    release_reserved_inventory(db, order)
                    order.status = "FAILED"
                    db.commit()
                    continue

                if intent.client_secret:
                    return PaymentIntentResponse(
                        order_id=order.id,
                        payment_intent_id=intent.id,
                        client_secret=intent.client_secret,
                        amount=amount_paise,
                        currency="inr",
                    )

            # Pending order exists but does not have a saved PaymentIntent.
            intent = stripe.PaymentIntent.create(
                amount=amount_paise,
                currency="inr",
                metadata={
                    "order_id": str(order.id),
                    "user_id": str(current_user.id),
                },
                idempotency_key=(
                    f"stylehub-order-{order.id}-{amount_paise}"
                ),
            )
            order.stripe_payment_intent_id = intent.id
            db.commit()
            db.refresh(order)

            return PaymentIntentResponse(
                order_id=order.id,
                payment_intent_id=intent.id,
                client_secret=intent.client_secret,
                amount=amount_paise,
                currency="inr",
            )

        except HTTPException:
            raise
        except stripe.StripeError as exc:
            print(
                "Stripe pending-order retry failed:",
                type(exc).__name__,
                str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unable to resume the pending Stripe payment. Check the server terminal.",
            ) from exc

    # No matching reusable pending order exists. Lock products and validate stock.
    order_lines = []
    try:
        for cart_item in cart_items:
            product = (
                db.query(Product)
                .filter(
                    Product.id == cart_item.product_id,
                    Product.is_active.is_(True),
                )
                .with_for_update()
                .first()
            )
            if product is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A product in your cart is unavailable.",
                )
            if cart_item.quantity > product.stock:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for {product.name}.",
                )

            unit_price = Decimal(str(product.price))
            subtotal = unit_price * cart_item.quantity
            order_lines.append(
                {
                    "product": product,
                    "quantity": cart_item.quantity,
                    "unit_price": unit_price,
                    "subtotal": subtotal,
                }
            )

        order = Order(
            user_id=current_user.id,
            total_amount=total_amount,
            currency="inr",
            status="PENDING",
            inventory_reserved=True,
        )
        db.add(order)
        db.flush()

        for line in order_lines:
            line["product"].stock -= line["quantity"]
            db.add(
                OrderItem(
                    order_id=order.id,
                    product_id=line["product"].id,
                    product_name=line["product"].name,
                    quantity=line["quantity"],
                    unit_price=line["unit_price"],
                    subtotal=line["subtotal"],
                )
            )

        db.commit()
        db.refresh(order)

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise

    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_paise,
            currency="inr",
            metadata={
                "order_id": str(order.id),
                "user_id": str(current_user.id),
            },
            idempotency_key=f"stylehub-order-{order.id}-{amount_paise}",
        )
        order.stripe_payment_intent_id = intent.id
        db.commit()
        db.refresh(order)

        return PaymentIntentResponse(
            order_id=order.id,
            payment_intent_id=intent.id,
            client_secret=intent.client_secret,
            amount=amount_paise,
            currency="inr",
        )

    except stripe.StripeError as exc:
        print(
            "Stripe PaymentIntent creation failed:",
            type(exc).__name__,
            str(exc),
        )
        db.rollback()

        failed_order = (
            db.query(Order)
            .filter(
                Order.id == order.id,
                Order.user_id == current_user.id,
            )
            .first()
        )
        if failed_order is not None:
            try:
                release_reserved_inventory(db, failed_order)
                failed_order.status = "FAILED"
                db.commit()
            except Exception:
                db.rollback()
                print(
                    "WARNING: Could not release reserved inventory for "
                    f"order {order.id}; manual reconciliation is required."
                )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Stripe could not create the payment. Check the server terminal.",
        ) from exc


@router.get("/", response_model=list[OrderResponse])
def get_order_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc(), Order.id.desc())
        .all()
    )
    return [get_order_response(db, order) for order in orders]


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.user_id == current_user.id,
        )
        .first()
    )
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found.",
        )
    return get_order_response(db, order)