from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product
from app.products.schemas import ProductResponse

router = APIRouter(prefix="/api/products", tags=["Products"])

Department = Literal["Men", "Women", "Kids"]
Category = Literal["Clothing", "Footwear", "Accessories", "Outerwear"]


@router.get("/", response_model=list[ProductResponse])
def get_products(
    department: Department | None = Query(default=None),
    category: Category | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(Product.is_active.is_(True))

    if department is not None:
        query = query.filter(Product.department == department)

    if category is not None:
        query = query.filter(Product.category == category)

    if search is not None:
        query = query.filter(Product.name.ilike(f"%{search.strip()}%"))

    return query.order_by(Product.id.asc()).all()


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.is_active.is_(True),
        )
        .first()
    )

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )

    return product