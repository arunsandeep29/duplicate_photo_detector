import sys
import os
sys.path.insert(0, os.path.abspath('backend'))

from app.services.duplicate_finder import find_duplicates
from app.services.image_processor import get_image_metadata, compute_sharpness, load_image, compute_hash, compute_quality_score
from PIL import Image

def create_image(path, size=(100, 100), color=(255, 255, 255)):
    img = Image.new("RGB", size, color)
    img.save(path, format="JPEG")
    return path

import tempfile
d = tempfile.mkdtemp()
img1 = os.path.join(d, "img1.jpg")
img2 = os.path.join(d, "img2.jpg")
img3 = os.path.join(d, "img3.jpg")

create_image(img1, (100, 100))
create_image(img2, (200, 200))
create_image(img3, (150, 150))

for img in [img1, img2, img3]:
    m = get_image_metadata(img)
    s = compute_sharpness(load_image(img))
    m['sharpness'] = s
    q = compute_quality_score(resolution=m['resolution'], file_size_bytes=m['file_size_bytes'], sharpness=m['sharpness'])
    print(f"{img}: res={m['resolution']} size={m['file_size_bytes']} sharp={s} score={q}")
