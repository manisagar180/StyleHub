from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user
from app.database import get_db
from app.models import CartItem, Product, User
from app.cart.schemas import (
    CartItemCreate,
    CartItemResponse,
    CartItemUpdate,
    CartProductResponse,
    CartResponse,
)

router = APIRouter(prefix="/api/cart", tags=["Shopping Cart"])


def build_cart_item_response(item: CartItem, product: Product):
    return CartItemResponse(
        id=item.id,
        product_id=item.product_id,
        quantity=item.quantity,
        product=CartProductResponse.model_validate(product),
        subtotal=product.price * item.quantity,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def get_owned_cart_item(
    item_id: int,
    user_id: int,
    db: Session,
) -> tuple[CartItem, Product]:
    item = (
        db.query(CartItem)
        .filter(
            CartItem.id == item_id,
            CartItem.user_id == user_id,
        )
        .first()
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found.",
        )

    product = db.query(Product).filter(
        Product.id == item.product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    return item, product


@router.post(
    "/items",
    response_model=CartItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_to_cart(
    data: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = (
        db.query(Product)
        .filter(
            Product.id == data.product_id,
            Product.is_active.is_(True),
        )
        .first()
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or unavailable.",
        )

    if product.stock < data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested quantity exceeds available stock.",
        )

    item = (
        db.query(CartItem)
        .filter(
            CartItem.user_id == current_user.id,
            CartItem.product_id == product.id,
        )
        .first()
    )

    if item:
        new_quantity = item.quantity + data.quantity

        if new_quantity > product.stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Requested quantity exceeds available stock.",
            )

        item.quantity = new_quantity
    else:
        item = CartItem(
            user_id=current_user.id,
            product_id=product.id,
            quantity=data.quantity,
        )
        db.add(item)

    try:
        db.commit()
        db.refresh(item)
    except Exception:
        db.rollback()
        raise

    return build_cart_item_response(item, product)


@router.get("/", response_model=CartResponse)
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items = (
        db.query(CartItem)
        .filter(CartItem.user_id == current_user.id)
        .order_by(CartItem.id.asc())
        .all()
    )

    response_items = []
    total_price = Decimal("0.00")
    total_items = 0

    for item in items:
        product = db.query(Product).filter(
            Product.id == item.product_id
        ).first()

        if product is None:
            continue

        response_items.append(
            build_cart_item_response(item, product)
        )
        total_items += item.quantity
        total_price += product.price * item.quantity

    return CartResponse(
        items=response_items,
        total_items=total_items,
        total_price=total_price,
    )


@router.patch(
    "/items/{item_id}",
    response_model=CartItemResponse,
)
def update_cart_item(
    item_id: int,
    data: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item, product = get_owned_cart_item(
        item_id,
        current_user.id,
        db,
    )

    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This product is no longer available.",
        )

    if data.quantity > product.stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Requested quantity exceeds available stock.",
        )

    item.quantity = data.quantity

    try:
        db.commit()
        db.refresh(item)
    except Exception:
        db.rollback()
        raise

    return build_cart_item_response(item, product)


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_cart_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(CartItem)
        .filter(
            CartItem.id == item_id,
            CartItem.user_id == current_user.id,
        )
        .first()
    )

    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found.",
        )

    db.delete(item)
    db.commit()
    return None