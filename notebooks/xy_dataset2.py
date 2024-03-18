import torch
import os
import glob
import uuid
import PIL.Image
import torch.utils.data
import subprocess
import cv2
import numpy as np


class XYDataset(torch.utils.data.Dataset):
    def __init__(self, directory, categories, transform=None, random_hflip=False):
        super(XYDataset, self).__init__()
        self.directory = directory
        self.categories = categories
        self.transform = transform
        self.refresh()
        self.random_hflip = random_hflip
        
    def __len__(self):
        return len(self.annotations)
    
    def __getitem__(self, idx):
        ann = self.annotations[idx]
        image = cv2.imread(ann['image_path'], cv2.IMREAD_COLOR)
        image = PIL.Image.fromarray(image)
        width = image.width
        height = image.height
        if self.transform is not None:
            image = self.transform(image)
        
        x = 2.0 * (ann['x'] / width - 0.5) # -1 left, +1 right
        y = 2.0 * (ann['y'] / height - 0.5) # -1 top, +1 bottom
        
        if self.random_hflip and float(np.random.random(1)) > 0.5:
            image = torch.from_numpy(image.numpy()[..., ::-1].copy())
            x = -x
            
        return image, ann['category_index'], torch.Tensor([x, y])
    
    def _parse(self, path):
        basename = os.path.basename(path)
        items = basename.split('_')
        x = items[0]
        y = items[1]
        no = items[2]
        return int(x), int(y), int(no)
        
    def refresh(self):
        self.annotations = []
        for category in self.categories:
            category_index = self.categories.index(category)
            # ここでファイルのリストを取得し、最終変更日時でソート
            image_paths = sorted(glob.glob(os.path.join(self.directory, category, '*.jpg')), 
                                 key=os.path.getmtime)
            for image_path in image_paths:
                x, y, no = self._parse(image_path)
                self.annotations += [{
                    'image_path': image_path,
                    'category_index': category_index,
                    'category': category,
                    'x': x,
                    'y': y,
                    'no': no
                }]
        
    def old_save_entry(self, category, image, x, y, no):
        category_dir = os.path.join(self.directory, category)
        if not os.path.exists(category_dir):
            subprocess.call(['mkdir', '-p', category_dir])
            
        filename = '%d_%d_%d_%s.jpg' % (x, y, no, str(uuid.uuid1()))
        
        image_path = os.path.join(category_dir, filename)
        cv2.imwrite(image_path, image)
        self.refresh()


    def save_entry(self, category, image, x, y, no):
        category_dir = os.path.join(self.directory, category)
        if not os.path.exists(category_dir):
            subprocess.call(['mkdir', '-p', category_dir])
            
        # 特定の no を持つ、任意の x, y のファイルを検索
        existing_files = glob.glob(os.path.join(category_dir, f"*_{no}_*.jpg"))
        
        if existing_files:
            # 既存のファイルが見つかった場合、リネーム
            old_file_path = existing_files[0]
            old_file_name = os.path.basename(old_file_path)
            
            # '{no}_' 以降の部分（UUID および ".jpg" 拡張子を含む）を抽出
            postfix = old_file_name.split(f"_{no}_", 1)[1]
            
            # 新しいファイル名を生成（古い UUID を保持）
            new_file_name = f'{x}_{y}_{no}_{postfix}'
            new_file_path = os.path.join(category_dir, new_file_name)
            
            os.rename(old_file_path, new_file_path)
        else:
            # 既存のファイルが見つからなかった場合、新規作成
            new_uuid = str(uuid.uuid1())
            filename = f'{x}_{y}_{no}_{new_uuid}.jpg'
            image_path = os.path.join(category_dir, filename)
            cv2.imwrite(image_path, image)
        
        self.refresh()

    def delete_entry(self, no):
        annotation = self.find_annotation(no)
        if annotation:
            image_path = annotation['image_path']
            os.remove(image_path)
            self.annotations = [ann for ann in self.annotations if ann['no'] != no]
            return image_path
        return None
    
    def get_count(self, category):
        i = 0
        for a in self.annotations:
            if a['category'] == category:
                i += 1
        return i

    def find_annotation(self, no):
        """
        指定された no に合致するアノテーションを検索します。
        
        Parameters:
            no (int): 検索するアノテーションの no

        Returns:
            dict or None: 見つかったアノテーションの辞書、見つからなければ None
        """
        for annotation in self.annotations:
            if annotation['no'] == no:
                return annotation
        return None

class HeatmapGenerator():
    def __init__(self, shape, std):
        self.shape = shape
        self.std = std
        self.idx0 = torch.linspace(-1.0, 1.0, self.shape[0]).reshape(self.shape[0], 1)
        self.idx1 = torch.linspace(-1.0, 1.0, self.shape[1]).reshape(1, self.shape[1])
        self.std = std
        
    def generate_heatmap(self, xy):
        x = xy[0]
        y = xy[1]
        heatmap = torch.zeros(self.shape)
        heatmap -= (self.idx0 - y)**2 / (self.std**2)
        heatmap -= (self.idx1 - x)**2 / (self.std**2)
        heatmap = torch.exp(heatmap)
        return heatmap