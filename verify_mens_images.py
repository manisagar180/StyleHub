from urllib.request import Request, urlopen

candidates = {
    "Men's summer outfit": "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=700",
    "Men's backpack": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=700",
    "Running shoes": "https://images.unsplash.com/photo-1460353581641-37baddab0fa2?w=700",
    "Men's sports T-shirt": "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=700",
    "Men's training tights": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=700",
}

for name, url in candidates.items():
    try:
        req = Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(req, timeout=10) as response:
            print(f"{response.status} | {name} | {response.headers.get('Content-Type')}")
    except Exception as error:
        print(f"FAILED | {name} | {error}")
