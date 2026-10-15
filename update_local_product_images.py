from app.database import SessionLocal
from app.models import Product

IMAGE_UPDATES = {
    "Activewear Leggings": "/images/activewear-leggings.jpg",
    "Casual Summer Dress": "/images/casual-summer-outfit.jpg",
    "Lightweight Running Shoes": "/images/lightweight-running-shoes.jpg",
    "Everyday Backpack": "/images/everyday-backpack.jpg",
    "Performance Sports T-Shirt": "/images/performance-sports-tshirt.jpg",
    "Training Joggers": "/images/training-joggers.jpg",
}


def main():
    db = SessionLocal()

    try:
        products = {
            product.name: product
            for product in db.query(Product).all()
        }

        missing = [
            name for name in IMAGE_UPDATES
            if name not in products
        ]

        if missing:
            raise ValueError(f"Products not found: {missing}")

        # Update only the six image paths.
        for name, image_path in IMAGE_UPDATES.items():
            products[name].image_url = image_path

        # Rename the summer product.
        products["Casual Summer Dress"].name = "Casual Summer Outfit"

        db.commit()

        print("SUCCESS: Six product image paths updated.")
        print("SUCCESS: Casual Summer Dress renamed to Casual Summer Outfit.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()