import cv2


IMAGE_HEIGHT = 224
IMAGE_WIDTH = 224
GRID_STEP = 30

# 例：ピクセル指定のROI（左,上,右,下）
# ROI_BOX_PX = (50, 90, 174, 115)
ROI_BOX_PX = (50, 90, 174, 224)


def draw_grids(img):
    x_mid = int(IMAGE_WIDTH / 2)
    y_mid = int(IMAGE_HEIGHT / 2)
    color_mid = (255, 255, 0)
    color_normal = (100, 100, 255)

    marked_img = img.copy()
    marked_img = cv2.line(marked_img, (x_mid, 0), (x_mid, IMAGE_HEIGHT), color_mid, 1)
    marked_img = cv2.line(marked_img, (0, y_mid), (IMAGE_WIDTH, y_mid), color_mid, 1)
    for x_offset in range(GRID_STEP, x_mid, GRID_STEP):
        marked_img = cv2.line(marked_img, (x_mid - x_offset, 0), (x_mid - x_offset, IMAGE_HEIGHT), color_normal, 1)
        marked_img = cv2.line(marked_img, (x_mid + x_offset, 0), (x_mid + x_offset, IMAGE_HEIGHT), color_normal, 1)
    for y_offset in range(GRID_STEP, y_mid, GRID_STEP):
        marked_img = cv2.line(marked_img, (0, y_mid - y_offset), (IMAGE_WIDTH, y_mid - y_offset), color_normal, 1)
        marked_img = cv2.line(marked_img, (0, y_mid + y_offset), (IMAGE_WIDTH, y_mid + y_offset), color_normal, 1)

    return marked_img


def clip_box_px(box, w, h):
    """画像サイズに合わせて (l,t,r,b) をクリップ"""
    l, t, r, b = box
    l = max(0, min(l, w))
    r = max(0, min(r, w))
    t = max(0, min(t, h))
    b = max(0, min(b, h))
    if r <= l: r = min(w, l + 1)
    if b <= t: b = min(h, t + 1)
    return int(l), int(t), int(r), int(b)


def rel_to_abs(box_rel, w, h):
    """相対座標 (xc,yc,w,h) → ピクセル (l,t,r,b)"""
    xc, yc, bw, bh = box_rel
    l = int((xc - bw / 2) * w)
    t = int((yc - bh / 2) * h)
    r = int((xc + bw / 2) * w)
    b = int((yc + bh / 2) * h)
    return clip_box_px((l, t, r, b), w, h)


def mask_keep_roi_and_resize(img, box_px, size=(IMAGE_WIDTH, IMAGE_HEIGHT)):
    """
    ROI以外を黒で塗りつぶしてから size にリサイズ
    box_px: (left, top, right, bottom) [ピクセル]
    """
    import numpy as np

    h, w = img.shape[:2]
    l, t, r, b = clip_box_px(box_px, w, h)
    masked = np.zeros_like(img)
    masked[t:b, l:r] = img[t:b, l:r]
    out = cv2.resize(masked, size, interpolation=cv2.INTER_CUBIC)
    return out


def crop_only_and_resize(img, box_px, size=(IMAGE_WIDTH, IMAGE_HEIGHT)):
    """
    ROIを切り抜いてから size にリサイズ（黒ベタなし）
    """
    h, w = img.shape[:2]
    l, t, r, b = clip_box_px(box_px, w, h)
    crop = img[t:b, l:r]
    out = cv2.resize(crop, size, interpolation=cv2.INTER_CUBIC)
    return out
