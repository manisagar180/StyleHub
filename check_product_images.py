import ast
from pathlib import Path
from urllib.request import Request, urlopen

source = Path("update_product_images.py").read_text(encoding="utf-8-sig")
tree = ast.parse(source)

images = next(
    ast.literal_eval(node.value)
    for node in tree.body
    if isinstance(node, ast.Assign)
    and any(
        isinstance(target, ast.Name) and target.id == "PRODUCT_IMAGES"
        for target in node.targets
    )
)

for name, url in images.items():
    try:
        request = Request(
            url,
            method="HEAD",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urlopen(request, timeout=10) as response:
            print(f"{response.status} | {name}")
    except Exception as error:
        print(f"CHECK FAILED | {name} | {error}")
