"""사진 찾기 Claude가 후보 사진을 확인할 때 쓴다. 크기를 출력하고 800px 미리보기를 만든다.

usage: python preview.py  (candidate.img → candidate_preview.jpg)
"""
from PIL import Image

im = Image.open("candidate.img")
print(f"{im.width}x{im.height}")
im.thumbnail((800, 800))
im.convert("RGB").save("candidate_preview.jpg", quality=85)
