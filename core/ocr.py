import io
from typing import List

import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

_ocr = RapidOCR()


def ocr_from_image(image_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(image_bytes))
    image_np = np.array(image)
    result, _ = _ocr(image_np)
    if not result:
        return ""
    lines = [item[1] for item in result]
    return "\n".join(lines)


def ocr_from_images(images_bytes: List[bytes]) -> List[str]:
    return [ocr_from_image(img) for img in images_bytes]
