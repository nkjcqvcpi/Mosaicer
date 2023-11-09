from math import ceil

from PIL import Image, ImageDraw, ImageFilter, ImageChops

THUMBNAIL_SIZE = (720, 720)  # (576, 576)


def render(img, fn, mosaics=None, blur=False, watermarks=None, thumbnail=False, resize=None) -> (Image.Image, str):
    """
    :type img: PIL.Image.Image
    :type fn: str
    :type mosaics: (float, float, OrderedDict) or None
    :type blur: bool
    :type watermarks: (Image.Image, Image.Image, float, OrderedDict) or None
    :type thumbnail: bool
    :type resize: int or None
    """
    if mosaics:
        width_line, scale_img, mosaics = mosaics
        draw = ImageDraw.Draw(img)
        for _, line in mosaics.items():
            line = [i / scale_img for i in line]
            draw.line(line, width=ceil(width_line / scale_img), fill=0)
        fn += '.MOSAIC'
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(radius=50))
        fn += '.BLUR'
    if watermarks:
        wm, wm_i, scale_img, watermarks = watermarks
        for x, y, s, i in watermarks.values():
            wmr = wm_i if i else wm
            wmr = wmr.resize((int(wmr.width * s / scale_img), int(wmr.height * s / scale_img)))
            img.paste(wmr, (int(x / scale_img), int(y / scale_img)), wmr)
        fn += '.WM'
    if thumbnail:
        img.thumbnail(THUMBNAIL_SIZE)
        fn += '.THUMB'
    elif resize:
        # self.res_list[self.combobox_res.get()]
        if img.width >= img.height:  # horizontal
            new_height = resize
            scale = new_height / img.height
            new_width = int(scale * img.width)
        else:  # vertical
            new_width = resize
            scale = new_width / img.width
            new_height = int(scale * img.height)
        img = img.resize((new_width, new_height))
        fn += '.RESIZE'
    return img, fn


def calc_scale(img, canvas_width, canvas_height):
    """
    :type img: Image.Image
    :type canvas_width: int
    :type canvas_height: int
    """
    canvas_width, canvas_height = int(canvas_width * 0.9), int(canvas_height * 0.9)

    ratio_aspect_ori = img.width / img.height
    ratio_aspect_can = canvas_width / canvas_height

    scale_width = canvas_width / img.width
    scale_height = canvas_height / img.height

    if ratio_aspect_ori > ratio_aspect_can:
        display_size = (canvas_width, int(img.height * scale_width))
        scale_img = scale_width
    elif ratio_aspect_ori <= ratio_aspect_can:
        display_size = (int(img.width * scale_height), canvas_height)
        scale_img = scale_height
    else:
        display_size = (canvas_width, canvas_height)
        scale_img = scale_width

    width_line = ceil(0.01 * max(display_size))

    return display_size, scale_img, width_line


def make_watermark(width, height, wm_path, angle, margin=10, sep=(1.5, 3), alpha=0.5):
    bg_color = (0, 0, 0, 0)
    wm_fs = Image.new('RGBA', (3 * width, 3 * height), bg_color)

    wm_width = int(min(wm_fs.size) * 0.1)
    wm = Image.open(wm_path)
    wm = wm.resize((wm_width, int(wm_width * wm.height / wm.width)))

    wm_fs_draw = ImageDraw.Draw(wm_fs)
    fg_color = [int((255 - i) * alpha) for i in bg_color]
    for x in range(margin, wm_fs.width - margin, int(sep[0] * wm.width)):
        for y in range(margin, wm_fs.height - margin, int(sep[1] * wm.height)):
            wm_fs_draw.bitmap((x, y), wm, fill=fg_color)

    wm_fs = wm_fs.rotate(angle)
    wm_fs = wm_fs.crop((width, height, 2 * width, 2 * height))
    return wm_fs


def watermarker(img_path, wm_path, output_path, angle=-30, alpha=.5, mode='lighter'):
    ori_img = Image.open(img_path).convert('RGBA')
    wm_img = make_watermark(width=ori_img.width, height=ori_img.height, wm_path=wm_path, angle=angle, alpha=alpha)
    if mode == 'lighter':
        out = ImageChops.add(ori_img, wm_img)
    elif mode == 'darker':
        out = ImageChops.subtract(ori_img, wm_img)
    else:
        raise ValueError(f'Unknown mode: {mode}')

    out = out.convert('RGB')
    out.save(output_path)