"""배경 제거된 제품 PNG를 배경 위에 얹어 1:1 썸네일을 만든다. 제품 픽셀은 손대지 않는다.

usage: python compose.py <background.jpg> <cutout.png> <out.jpg>
"""
import sys

from PIL import Image, ImageFilter

bg_path, cut_path, out_path = sys.argv[1:4]

bg = Image.open(bg_path).convert("RGBA")
side = min(bg.size)
left, top = (bg.width - side) // 2, (bg.height - side) // 2
bg = bg.crop((left, top, left + side, top + side))

cut = Image.open(cut_path).convert("RGBA")
cut = cut.crop(cut.getbbox())
# 흰 배경 누끼컷의 가장자리 흰 테두리(halo)를 1px 깎아낸다
cut.putalpha(cut.getchannel("A").filter(ImageFilter.MinFilter(3)))
# 긴 변을 화면의 60%로 — 네이버 정사각 크롭에서도 안 잘리고, 배경이 무늬뿐이라 크기 기준이 없어 자연스럽다
# 단 원본의 2배 넘게 키우면 흐려지므로 작은 사진은 덜 키운다 (AI 업스케일은 작은 라벨 글자를 지어내서 안 씀)
scale = min(0.6 * side / max(cut.size), 2.0)
cut = cut.resize((round(cut.width * scale), round(cut.height * scale)), Image.LANCZOS)
x = (side - cut.width) // 2
y = round(side * 0.56 - cut.height / 2)  # 살짝 아래로, 위쪽은 제목 얹을 여백

# 그림자: 제품 실루엣을 흐리게 해서 오른쪽 아래로
pad, blur, off = round(side * 0.05), side * 0.015, round(side * 0.02)
shadow = Image.new("RGBA", (cut.width + pad * 2, cut.height + pad * 2), (70, 50, 30, 0))
mask = Image.new("L", shadow.size, 0)
mask.paste(cut.getchannel("A").point(lambda a: a * 0.35), (pad, pad))
shadow.putalpha(mask.filter(ImageFilter.GaussianBlur(blur)))

bg.alpha_composite(shadow, (x - pad + off, y - pad + off))
bg.alpha_composite(cut, (x, y))
bg.convert("RGB").save(out_path, quality=90)
