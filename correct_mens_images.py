from app.database import SessionLocal
from app.models import Product

IMAGE_UPDATES = {
    "Casual Summer Outfit": "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=700",
    "Everyday Backpack": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=700",
    "Lightweight Running Shoes": "https://images.unsplash.com/photo-1460353581641-37baddab0fa2?w=700",
    "Performance Sports T-Shirt": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=700",
    "Activewear Leggings": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=700",
}

def main():
    db = SessionLocal()
    try:
        products = {p.name: p for p in db.query(Product).all()}
        missing = sorted(set(IMAGE_UPDATES) - products.keys())
        if missing:
            raise ValueError("Products not found: " + ", ".join(missing))

        print("All five product names found.")
        print("No database changes made yet.")
        print("Image URLs still require visual confirmation.")

    finally:
        db.close()

if __name__ == "__main__":
    main()
