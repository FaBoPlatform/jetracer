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
        self.annotations = {}
        self.index_to_no = []
        self.refresh()
        self.random_hflip = random_hflip
    def __len__(self):
        return len(self.annotations)
    
    def __getitem__(self, idx):
        task_dataset_category_no = self.index_to_no[idx]
        ann = self.annotations[task_dataset_category_no]
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
        uuid_with_extension = items[-1]
        task_dataset_category_no = '_'.join(items[2:-1])  # 最後の部分（uuid.jpg）を除いた残り全て
        uuid = uuid_with_extension.split('.')[0]  # 拡張子を取り除く
        return int(x), int(y), task_dataset_category_no
        
    def refresh(self):
        self.annotations.clear()
        self.index_to_no.clear()
        for category in self.categories:
            category_index = self.categories.index(category)
            # noをユニークキーとするdict型でannotationを記録するため、ソート不要
            image_paths = glob.glob(os.path.join(self.directory, category, '*.jpg'))
            
            # _parseメソッドを使用してソートのためのキーを準備
            def sort_key(path):
                x, y, task_dataset_category_no = self._parse(path)
                # task_dataset_category_noを '_' で分割し、最後の要素（no）をint型に変換してソートキーとする
                parts = task_dataset_category_no.rsplit('_', 1)
                return (parts[0], int(parts[1])) if len(parts) > 1 else (task_dataset_category_no, 0)
            # 準備したキーでソート
            image_paths_sorted = sorted(image_paths, key=sort_key)
            
            for image_path in image_paths_sorted:
                x, y, task_dataset_category_no = self._parse(image_path)
                no = task_dataset_category_no.split('_')[-1]
                self.annotations[task_dataset_category_no] = {
                    'image_path': image_path,
                    'task_dataset_category_no': task_dataset_category_no,
                    'category_index': category_index,
                    'category': category,
                    'x': x,
                    'y': y,
                    'no': no
                }
                self.index_to_no.append(task_dataset_category_no)

    def save_entry(self, category, image, x, y, task_dataset_category_no):
        category_dir = os.path.join(self.directory, category)
        if not os.path.exists(category_dir):
            subprocess.call(['mkdir', '-p', category_dir])
            
        # 特定の no を持つ、任意の x, y のファイルを検索
        existing_files = glob.glob(os.path.join(category_dir, f"*_{task_dataset_category_no}_*.jpg"))
        
        if existing_files:
            # 既存のファイルが見つかった場合、リネーム
            old_file_path = existing_files[0]
            old_file_name = os.path.basename(old_file_path)
            
            # '{no}_' 以降の部分（UUID および ".jpg" 拡張子を含む）を抽出
            postfix = old_file_name.split(f"_{task_dataset_category_no}_", 1)[1]
            
            # 新しいファイル名を生成（古い UUID を保持）
            new_file_name = f'{x}_{y}_{task_dataset_category_no}_{postfix}'
            new_file_path = os.path.join(category_dir, new_file_name)
            
            os.rename(old_file_path, new_file_path)
        else:
            # 既存のファイルが見つからなかった場合、新規作成
            new_uuid = str(uuid.uuid1())
            filename = f'{x}_{y}_{task_dataset_category_no}_{new_uuid}.jpg'
            new_file_path = os.path.join(category_dir, filename)
            cv2.imwrite(new_file_path, image)
        
        self.refresh()
        return new_file_path

    def delete_entry(self, task_dataset_category_no):
        annotation = self.find_annotation(task_dataset_category_no)
        if annotation:
            image_path = annotation['image_path']
            os.remove(image_path)
            del self.annotations[task_dataset_category_no]  # キーに対応する要素を削除
            self.index_to_no = [n for n in self.index_to_no if n != task_dataset_category_no]  # マップも更新
            return image_path
        return None
    
    def get_count(self, category):
        i = 0
        for a in self.annotations:
            if a['category'] == category:
                i += 1
        return i

    def find_annotation(self, task_dataset_category_no):
        """
        指定された task_dataset_category_no に合致するアノテーションを検索します。
        
        Parameters:
            task_dataset_category_no (str): 検索するアノテーションの task_dataset_category_no

        Returns:
            dict or None: 見つかったアノテーションの辞書、見つからなければ None
        """
        return self.annotations.get(task_dataset_category_no, None)

    def find_annotation_from_index(self, idx):
        if len(self.index_to_no) >= idx + 1:
            task_dataset_category_no = self.index_to_no[idx]
        else:
            return None
        return self.annotations.get(task_dataset_category_no, None)


    def find_task_dataset_category_no_from_index(self, idx):
        ann = self.find_annotation_from_index(idx)
        if ann is None:
            return None
        else:
            return ann['task_dataset_category_no']

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