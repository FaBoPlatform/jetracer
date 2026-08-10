import torch
import torchvision.transforms as transforms
import torch.nn.functional as F
import cv2
import PIL.Image
import numpy as np

mean = torch.Tensor([0.485, 0.456, 0.406]).cuda()
std = torch.Tensor([0.229, 0.224, 0.225]).cuda()

def preprocess(image):
    device = torch.device("cuda")
    # JP7.2: OpenCV 4.13のGStreamer appsinkはBGRx(4ch)を無変換で受けるため、
    # jetcamのフレームが4チャンネルで来ることがある。BGRの3chに落とす。
    if image.ndim == 3 and image.shape[-1] == 4:
        image = np.ascontiguousarray(image[:, :, :3])
    image = PIL.Image.fromarray(image)
    image = transforms.functional.to_tensor(image).to(device)
    image.sub_(mean[:, None, None]).div_(std[:, None, None])
    return image[None, ...]
