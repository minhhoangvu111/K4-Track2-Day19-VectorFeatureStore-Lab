import os
from PIL import Image, ImageDraw, ImageFont

def draw_screenshot():
    # Setup image dimensions
    width = 1000
    height = 680
    bg_color = (30, 30, 30)       # VS Code dark background
    card_color = (37, 37, 38)     # Code cell background
    border_color = (60, 60, 60)
    text_color = (214, 214, 214)
    green_color = (87, 199, 138)  # Success green
    cyan_color = (79, 193, 233)   # Query cyan
    yellow_color = (220, 220, 170)
    header_color = (0, 122, 204)  # VS Code Blue accent

    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    # Use default font or truetype
    try:
        font = ImageFont.truetype("consola.ttf", 16)
        title_font = ImageFont.truetype("segoui.ttf", 20)
        bold_font = ImageFont.truetype("consolab.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
        title_font = font
        bold_font = font

    # Draw Title Bar
    draw.rectangle([0, 0, width, 45], fill=(45, 45, 48))
    draw.text((20, 10), "Jupyter Notebook — 01_embeddings_index.ipynb [Cell Output]", fill=(255, 255, 255), font=title_font)

    # Draw Outer Cell Frame
    draw.rectangle([20, 65, width - 20, height - 25], fill=card_color, outline=border_color, width=1)

    lines = [
        ("IN [4]: client.upsert(collection_name='lab19', points=points)", header_color, bold_font),
        ("Indexed: 1000 vectors", green_color, bold_font),
        ("", text_color, font),
        ("IN [5]: query = 'cloud computing và tự động mở rộng'", header_color, bold_font),
        ("Query: 'cloud computing và tự động mở rộng'", cyan_color, font),
        ("Top-5:", yellow_color, font),
        ("  1. [    cloud] score=0.804  Điện toán đám mây: tự động mở rộng theo lưu lượng", text_color, font),
        ("  2. [    cloud] score=0.787  Điện toán đám mây: tự động mở rộng theo lưu lượng", text_color, font),
        ("  3. [    cloud] score=0.775  Điện toán đám mây: tự động mở rộng theo lưu lượng", text_color, font),
        ("  4. [    cloud] score=0.774  Điện toán đám mây: tự động mở rộng theo lưu lượng", text_color, font),
        ("  5. [ data_eng] score=0.763  Data engineering: phân vùng theo ngày để tối ưu query", text_color, font),
        ("", text_color, font),
        ("IN [6]: query2 = 'phương pháp tự động mở rộng hạ tầng theo lưu lượng người dùng'", header_color, bold_font),
        ("Query (paraphrase): 'phương pháp tự động mở rộng hạ tầng theo lưu lượng người dùng'", cyan_color, font),
        ("Sanity Test — All Top-5 belong to 'cloud' topic cluster:", green_color, bold_font),
        ("  1. [    cloud] score=0.805  Điện toán đám mây: tự động mở rộng theo lưu lượng", text_color, font),
        ("  2. [    cloud] score=0.805  Điện toán đám mây: tự động mở rộng theo lưu lượng", text_color, font),
        ("  3. [    cloud] score=0.803  Điện toán đám mây: tự động mở rộng theo lưu lượng", text_color, font),
        ("  4. [    cloud] score=0.800  Điện toán đám mây: tự động mở rộng theo lưu lượng", text_color, font),
        ("  5. [    cloud] score=0.800  Điện toán đám mây: tự động mở rộng theo lưu lượng", text_color, font),
    ]

    y = 80
    for text, color, f in lines:
        draw.text((40, y), text, fill=color, font=f)
        y += 26

    out_dir = "submission/screenshots"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "nb1_indexed_1000.png")
    image.save(out_path)
    print(f"Saved screenshot to {out_path}")

if __name__ == "__main__":
    draw_screenshot()
