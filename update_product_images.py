from app.database import SessionLocal
from app.models import Product

PRODUCT_IMAGES = {
    "Classic Cotton T-Shirt": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=700",
    "Slim Fit Denim Jeans": "https://images.unsplash.com/photo-1542272604-787c3835535d?w=700",
    "Casual Summer Dress": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=700",
    "Classic Hoodie": "https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=700",
    "Formal Oxford Shirt": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=700",
    "Everyday Casual Sneakers": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=700",
    "Lightweight Running Shoes": "https://images.unsplash.com/photo-1552674605-db6ffd4facb5?w=700",
    "Classic Comfort Sandals": "https://images.unsplash.com/photo-1603487742131-4160ec999306?w=700",
    "Everyday Backpack": "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=700",
    "Minimalist Wallet": "https://images.unsplash.com/photo-1627123424574-724758594e93?w=700",
    "Classic Baseball Cap": "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?w=700",
    "Modern Casual Jacket": "https://images.unsplash.com/photo-1548126032-079a0fb0099d?w=700",
    "Soft Knit Cardigan": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=700",
    "Classic Denim Jacket": "https://images.unsplash.com/photo-1543076447-215ad9ba6923?w=700",
    "Performance Training Shorts": "https://images.unsplash.com/photo-1591195853828-11db59a44f6b?w=700",
    "Performance Sports T-Shirt": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=700",
    "Training Joggers": "https://images.unsplash.com/photo-1552902865-b72c031ac5ea?w=700",
    "Activewear Leggings": "https://images.unsplash.com/photo-1616279968959-30b0738951e3?w=700",
    "Training Zip Jacket": "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=700",
}

def main():
    db = SessionLocal()
    try:
        products = {p.name: p for p in db.query(Product).all()}
        missing = [name for name in PRODUCT_IMAGES if name not in products]

        if missing:
            raise ValueError("Products not found: " + ", ".join(missing))

        for name, image_url in PRODUCT_IMAGES.items():
            products[name].image_url = image_url

        db.commit()
        print("Updated image URLs for 19 existing products.")
        print("No product names, prices, stock, orders, or payments changed.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
main()