import sys
import os
sys.path.insert(0, os.path.abspath('backend'))

from app.services.image_processor import get_image_metadata, compute_sharpness, load_image, compute_hash, compute_quality_score
from PIL import Image, ImageFilter, ImageDraw

def create_image(path, size=(100, 100), color=(255, 255, 255), blur=False):
    img = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(img)
    for i in range(0, size[0], 10):
        draw.line([(i, 0), (i, size[1])], fill=(0, 0, 0), width=2)
    for i in range(0, size[1], 10):
        draw.line([(0, i), (size[0], i)], fill=(0, 0, 0), width=2)
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(radius=8))
    img.save(path, format="JPEG")
    return path

import tempfile
d = tempfile.mkdtemp()
img1 = os.path.join(d, "img1.jpg")
img2 = os.path.join(d, "img2.jpg")
img3 = os.path.join(d, "img3.jpg")
blur_img = os.path.join(d, "blur.jpg")

create_image(img1, (100, 100))
create_image(img2, (200, 200))
create_image(img3, (150, 150))
create_image(blur_img, (100, 100), blur=True)

for img in [img1, img2, img3, blur_img]:
    m = get_image_metadata(img)
    s = compute_sharpness(load_image(img))
    m['sharpness'] = s
    q = compute_quality_score(resolution=m['resolution'], file_size_bytes=m['file_size_bytes'], sharpness=m['sharpness'])
    print(f"{img}: res={m['resolution']} size={m['file_size_bytes']} sharp={s} is_blur={m['is_blurred']} score={q}")
