import sys
import os
sys.path.insert(0, os.path.abspath('backend'))

from app.services.image_processor import get_image_metadata, compute_sharpness, load_image, compute_hash, compute_quality_score
from PIL import Image, ImageFilter

def create_image(path, size=(100, 100), color=(255, 255, 255), blur=False):
    img = Image.new("RGB", size, color)
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(radius=8))
    img.save(path, format="JPEG")
    return path

import tempfile
d = tempfile.mkdtemp()
sharp = os.path.join(d, "sharp.jpg")
blur = os.path.join(d, "blur.jpg")

create_image(sharp, (100, 100))
create_image(blur, (100, 100), blur=True)

for img in [sharp, blur]:
    m = get_image_metadata(img)
    s = compute_sharpness(load_image(img))
    m['sharpness'] = s
    print(f"{img}: sharp={s} is_blurred={m['is_blurred']}")
