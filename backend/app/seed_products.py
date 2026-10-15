from decimal import Decimal

from app.database import SessionLocal
from app.models import Product


SAMPLE_PRODUCTS = [
    # Clothing
    {
        "name": "Classic Cotton T-Shirt",
        "category": "Clothing",
        "description": "A comfortable cotton T-shirt for everyday wear.",
        "price": Decimal("799.00"),
        "stock": 50,
    },
    {
        "name": "Slim Fit Denim Jeans",
        "category": "Clothing",
        "description": "Versatile slim-fit denim jeans.",
        "price": Decimal("1799.00"),
        "stock": 30,
    },
    {
        "name": "Casual Summer Dress",
        "category": "Clothing",
        "description": "A lightweight dress for warm-weather outings.",
        "price": Decimal("1499.00"),
        "stock": 20,
    },
    {
        "name": "Classic Hoodie",
        "category": "Clothing",
        "description": "A soft hoodie for casual everyday comfort.",
        "price": Decimal("1299.00"),
        "stock": 25,
    },
    {
        "name": "Formal Oxford Shirt",
        "category": "Clothing",
        "description": "A smart shirt suitable for work and events.",
        "price": Decimal("999.00"),
        "stock": 35,
    },

    # Footwear
    {
        "name": "Everyday Casual Sneakers",
        "category": "Footwear",
        "description": "Versatile sneakers for everyday outfits.",
        "price": Decimal("2499.00"),
        "stock": 18,
    },
    {
        "name": "Lightweight Running Shoes",
        "category": "Footwear",
        "description": "Lightweight shoes for running and exercise.",
        "price": Decimal("2999.00"),
        "stock": 15,
    },
    {
        "name": "Classic Comfort Sandals",
        "category": "Footwear",
        "description": "Comfortable sandals for casual outings.",
        "price": Decimal("899.00"),
        "stock": 22,
    },

    # Accessories
    {
        "name": "Everyday Backpack",
        "category": "Accessories",
        "description": "A practical backpack for work and travel.",
        "price": Decimal("1599.00"),
        "stock": 16,
    },
    {
        "name": "Minimalist Wallet",
        "category": "Accessories",
        "description": "A compact wallet for everyday essentials.",
        "price": Decimal("599.00"),
        "stock": 28,
    },
    {
        "name": "Classic Baseball Cap",
        "category": "Accessories",
        "description": "A casual cap with an adjustable fit.",
        "price": Decimal("399.00"),
        "stock": 40,
    },

    # Outerwear
    {
        "name": "Modern Casual Jacket",
        "category": "Outerwear",
        "description": "A versatile jacket for cooler days.",
        "price": Decimal("3299.00"),
        "stock": 12,
    },
    {
        "name": "Soft Knit Cardigan",
        "category": "Outerwear",
        "description": "A comfortable cardigan for layering.",
        "price": Decimal("1899.00"),
        "stock": 17,
    },
    {
        "name": "Classic Denim Jacket",
        "category": "Outerwear",
        "description": "A timeless denim jacket for casual styling.",
        "price": Decimal("3799.00"),
        "stock": 10,
    },

    # Sportswear
    {
        "name": "Performance Training Shorts",
        "category": "Sportswear",
        "description": "Lightweight shorts for training and exercise.",
        "price": Decimal("699.00"),
        "stock": 32,
    },
    {
        "name": "Performance Sports T-Shirt",
        "category": "Sportswear",
        "description": "Breathable sports T-shirt for active workouts.",
        "price": Decimal("1299.00"),
        "stock": 25,
    },
    {
        "name": "Training Joggers",
        "category": "Sportswear",
        "description": "Comfortable athletic joggers for training.",
        "price": Decimal("2199.00"),
        "stock": 20,
    },
    {
        "name": "Activewear Leggings",
        "category": "Sportswear",
        "description": "Stretch-fit leggings for exercise and daily activity.",
        "price": Decimal("1899.00"),
        "stock": 18,
    },
    {
        "name": "Training Zip Jacket",
        "category": "Sportswear",
        "description": "A lightweight zip-up jacket for warm-ups and workouts.",
        "price": Decimal("2799.00"),
        "stock": 12,
    },
]


def seed_products():
    db = SessionLocal()

    try:
        added_count = 0

        for product_data in SAMPLE_PRODUCTS:
            existing_product = (
                db.query(Product)
                .filter(Product.name == product_data["name"])
                .first()
            )

            if existing_product is None:
                db.add(Product(**product_data))
                added_count += 1

        db.commit()

        total_count = db.query(Product).count()
        print(f"Product seeding completed. Added {added_count} new products.")
        print(f"Total products in catalogue: {total_count}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_products()