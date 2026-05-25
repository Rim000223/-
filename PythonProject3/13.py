from PIL import Image, ImageFilter, ImageDraw
import os

filename = "image.jpg"

if os.path.exists(filename):
    img = Image.open(filename)

    print("--- Задание 1 ---")
    img.show()
    print(f"Размер: {img.size}")
    print(f"Формат: {img.format}")
    print(f"Цветовая модель: {img.mode}")

    print("\n--- Задание 2 ---")
    w, h = img.size

    img.resize((w // 3, h // 3)).save("resized_image.jpg")

    img.transpose(Image.FLIP_LEFT_RIGHT).save("horizontal_mirror.jpg")
    img.transpose(Image.FLIP_TOP_BOTTOM).save("vertical_mirror.jpg")
    print("Сохранены: resized_image.jpg, horizontal_mirror.jpg, vertical_mirror.jpg")

    print("\n--- Задание 3 ---")

    folder = "filtered_images"

    filters = [
        ImageFilter.SHARPEN,
        ImageFilter.EDGE_ENHANCE,
        ImageFilter.DETAIL,
        ImageFilter.CONTOUR,
        ImageFilter.FIND_EDGES
    ]

    for i, f_filter in enumerate(filters):
        filtered_img = img.filter(f_filter)
        filtered_img.save(f"{folder}/filtered_{i + 1}.jpg")
        print(f"Сохранено: {folder}/filtered_{i + 1}.jpg")

    print("\n--- Задание 4 ---")
    img_rgba = img.convert("RGBA")

    txt = Image.new('RGBA', img_rgba.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt)
    draw.text((50, 50), "MY WATERMARK", fill=(255, 255, 255, 128))

    watermarked = Image.alpha_composite(img_rgba, txt)
    watermarked.save("image_with_watermark.png")
    print("Сохранено: image_with_watermark.png")
else:
    print(f"Файл {filename} не найден в папке проекта!")