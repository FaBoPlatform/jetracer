IMAGE_HEIGHT = 224
IMAGE_WIDTH = 224
GRID_STEP = 30

def draw_grids(img):
    import cv2

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
