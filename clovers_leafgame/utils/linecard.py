import re
from pathlib import Path
from io import BytesIO
from fontTools.ttLib import TTFont

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from PIL.ImageFont import FreeTypeFont
from PIL.Image import Image as IMG

import matplotlib.font_manager as fm


class FontManager:
    def __init__(self, font_name: str, fallback: list[str], size: tuple = None) -> None:
        self.font_name: str = font_name
        self.fallback: list[str] = fallback
        self.cmap = TTFont(
            fm.findfont(fm.FontProperties(family=font_name)), fontNumber=0
        ).getBestCmap()
        self.fallback_cmap = {}
        for font in self.fallback:
            font_path = fm.findfont(fm.FontProperties(family=font))
            self.fallback_cmap[font_path] = TTFont(
                font_path, fontNumber=0
            ).getBestCmap()

        self.font_def = {self.new_font(font_name, k): k for k in size} if size else {}

    def font(self, size: int):
        return self.font_def.get(size) or self.new_font(self.font_name, size)

    def new_font(self, name: str, size: int):
        return ImageFont.truetype(font=name, size=size, encoding="utf-8")


def linecard_to_png(text: str, font_manager: FontManager, **kwargs):
    """
    文字转png
    """
    output = BytesIO()
    linecard(text, font_manager, **kwargs).save(output, format="png")
    return output


def remove_tag(text: str, pattern: re.Pattern):
    match = pattern.search(text)
    if match:
        start = match.start()
        end = match.end()
        return text[:start] + text[end:], text[start:end]
    else:
        return None


def line_wrap(line: str, width: int, font: FreeTypeFont, start: int = 0):
    text_x = start
    new_str = ""
    for char in line:
        text_x += font.getlength(char)
        if text_x > width:
            new_str += "\n" + char
            text_x = 0
        else:
            new_str += char
    return new_str


class Tag:
    def __init__(self, font, cmap) -> None:
        self.align: str = "left"
        self.font: FreeTypeFont = font
        self.cmap: dict = cmap
        self.color: str = None
        self.passport: bool = False
        self.noautowrap: bool = False
        self.nowrap: bool = False


class linecard_pattern:
    align = re.compile(r"\[left\]|\[right\]|\[center\]|\[pixel\]\[.*?\]")
    font = re.compile(r"\[font\]\[.*?\]\[.*?\]")
    color = re.compile(r"\[color\]\[.*?\]")
    passport = re.compile(r"\[passport\]")
    nowrap = re.compile(r"\[nowrap\]")
    noautowrap = re.compile(r"\[noautowrap\]")


def linecard(
    text: str,
    font_manager: FontManager,
    font_size: int,
    width: int = None,
    height: int = None,
    padding: tuple = (20, 20),
    spacing: float = 1.2,
    bg_color: str = None,
    autowrap: bool = False,
    canvas=None,
) -> IMG:
    """
    指定宽度单行文字
        ----:横线

        [left]靠左
        [right]靠右
        [center]居中
        [pixel][400]指定像素

        [font][font_name][font_size]指定字体

        [color][#000000]指定本行颜色

        [nowrap]不换行
        [noautowrap]不自动换行
        [passport]保持标记
    """
    text = text.replace("\r\n", "\n")
    lines = text.split("\n")
    padding_x = padding[0]
    padding_y = padding[1]

    align = "left"

    font_def = font_manager.font(font_size)
    cmap_def = font_manager.cmap

    tag = Tag(font_def, cmap_def)

    x, max_x, y, charlist = (0.0, 0.0, 0.0, [])
    for line in lines:
        if tag.passport:
            tag.passport = False
        else:
            tag.__init__(font_def, cmap_def)

        if data := remove_tag(line, linecard_pattern.align):
            line, align = data
            if align.startswith("[pixel]["):
                tag.align = align[8:-1]
                x = 0
            else:
                tag.align = align[1:-1]
        elif tag.nowrap:
            tag.align = "nowrap"

        if data := remove_tag(line, linecard_pattern.font):
            line, font = data
            if font.startswith("[font]["):
                font = font[7:-1]
                inner_font_name, inner_font_size = font.split("][", 1)
                inner_font_size = int(inner_font_size) if inner_font_size else font_size
                inner_font_name = inner_font_name or font_def.path
                try:
                    tag.font = ImageFont.truetype(
                        font=inner_font_name, size=inner_font_size, encoding="utf-8"
                    )
                    tag.cmap = TTFont(
                        tag.font.path, fontNumber=tag.font.index
                    ).getBestCmap()
                except OSError:
                    pass

        if data := remove_tag(line, linecard_pattern.color):
            line, color = data
            tag.color = color[8:-1]

        if data := remove_tag(line, linecard_pattern.noautowrap):
            line = data[0]
            tag.noautowrap = True

        if data := remove_tag(line, linecard_pattern.nowrap):
            line = data[0]
            nowrap = True
        else:
            nowrap = False

        if data := remove_tag(line, linecard_pattern.passport):
            line = data[0]
            tag.passport = True

        if (
            autowrap
            and not tag.noautowrap
            and width
            and tag.font.getlength(line) > width
        ):
            line = line_wrap(line, width - padding_x, tag.font, x)

        if line == "----":
            inner_tmp = tag.font.size * spacing
            charlist.append([line, None, y, inner_tmp, tag.color, None])
            y += inner_tmp
        else:
            line_segs = line.split("\n")
            for seg in line_segs:
                for char in seg:
                    ord_char = ord(char)
                    inner_font = tag.font
                    if ord_char not in tag.cmap:
                        for (
                            fallback_font,
                            fallback_cmap,
                        ) in font_manager.fallback_cmap.items():
                            if ord_char in fallback_cmap:
                                inner_font = ImageFont.truetype(
                                    font=fallback_font,
                                    size=tag.font.size,
                                    encoding="utf-8",
                                )
                                break
                        else:
                            char = "□"
                    charlist.append([char, x, y, inner_font, tag.color, tag.align])
                    x += inner_font.getlength(char)
                max_x = max(max_x, x)
                x, y = (x, y) if nowrap else (0, y + tag.font.size * spacing)

    width = width if width else int(max_x + padding_x * 2)
    height = height if height else int(y + padding_y * 2)
    canvas = canvas if canvas else Image.new("RGBA", (width, height), bg_color)
    draw = ImageDraw.Draw(canvas)

    for i, (char, x, y, font, color, align) in enumerate(charlist):
        if char == "----":
            color = color if color else "gray"
            inner_y = y + (font - 0.5) // 2 + padding_y
            draw.line(((0, inner_y), (width, inner_y)), fill=color, width=4)
        else:
            if align == "left":
                start_x = padding_x
            elif align == "nowrap":
                pass
            elif align.isdigit():
                start_x = int(align)
            else:
                for inner_i, inner_y in enumerate(map(lambda x: (x[2]), charlist[i:])):
                    if inner_y != y:
                        inner_index = charlist[i + inner_i - 1]
                        break
                else:
                    inner_index = charlist[-1]
                inner_char = inner_index[0]
                inner_font = inner_index[3]
                inner_x = inner_index[1]
                inner_x += inner_font.getlength(inner_char)
                if align == "right":
                    start_x = width - inner_x - padding_x
                elif align == "center":
                    start_x = (width - inner_x) // 2
                else:
                    start_x = padding_x
            color = color if color else "black"
            draw.text((start_x + x, y + padding_y), char, fill=color, font=font)

    return canvas


def info_splicing(
    info: list[IMG],
    BG_path: Path = None,
    width: int = 880,
    padding: int = 20,
    spacing: int = 20,
    BG_type: str = "GAUSS",
):
    """
    信息拼接
        info:信息图片列表
        bg_path:背景地址
    """

    height = padding
    for image in info:
        # x = image.size[0] if x < image.size[0] else x
        height += image.size[1]
        height += spacing * 2
    else:
        height = height - spacing + padding

    size = (width + padding * 2, height)
    if BG_path:
        bg = Image.open(BG_path).convert("RGB")
        canvas = CropResize(bg, size)
    else:
        canvas = Image.new("RGB", size, "white")
        BG_type = "#00000099"

    height = padding

    def colorBG(canvas: IMG, image: IMG):
        colorBG = Image.new("RGBA", (width, image.size[1]), BG_type)
        canvas.paste(colorBG, (20, height), mask=colorBG)
        canvas.paste(image, (20, height), mask=image)

    def blurBG(canvas: IMG, image: IMG):
        box = (20, height, 900, height + image.size[1])
        region = canvas.crop(box)
        blurred_region = region.filter(ImageFilter.GaussianBlur(radius=10))
        canvas.paste(blurred_region, box)
        canvas.paste(image, (20, height), mask=image)

    def noneBG(canvas: IMG, image: IMG):
        canvas.paste(image, (20, height), mask=image)

    funcBG = {"GAUSS": blurBG, "NONE": noneBG}.get(BG_type, colorBG)

    for image in info:
        funcBG(canvas, image)
        height += image.size[1]
        height += spacing * 2
    output = BytesIO()
    canvas.convert("RGB").save(output, format="png")
    return output


def CropResize(img: IMG, size: tuple[int, int]):
    """
    修改图像尺寸
    """

    test_x = img.size[0] / size[0]
    test_y = img.size[1] / size[1]

    if test_x < test_y:
        width = img.size[0]
        height = size[1] * test_x
    else:
        width = size[0] * test_y
        height = img.size[1]

    center = (img.size[0] / 2, img.size[1] / 2)
    output = img.crop(
        (
            int(center[0] - width / 2),
            int(center[1] - height / 2),
            int(center[0] + width / 2),
            int(center[1] + height / 2),
        )
    )
    output = output.resize(size)
    return output
