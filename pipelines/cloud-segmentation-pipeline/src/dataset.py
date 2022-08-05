import os

import cv2
import numpy as np
import pandas as pd
from hydra.utils import get_original_cwd
from omegaconf import DictConfig
from torch.utils.data import Dataset


class CloudDataset(Dataset):
    def __init__(
        self, df: pd.DataFrame, image_in_dir, img_ids, transforms, preprocessing
    ):
        self.df = df
        self.image_folder = os.path.join(get_original_cwd(), image_in_dir)
        self.img_ids = img_ids
        self.transforms = transforms
        self.preprocessing = preprocessing


    def rle_decode(self, mask_rle: str="", shape: tuple=(None, None)):
        """Source: https://www.kaggle.com/artgor/segmentation-in-pytorch-using-convenient-tools"""
        s = mask_rle.split()
        starts, lengths = [np.asarray(x, dtype=int) for x in (s[0:][::2], s[1:][::2])]
        starts -= 1
        ends = starts + lengths
        img = np.zeros(shape[0] * shape[1], dtype=np.uint8)
        for lo, hi in zip(starts, ends):
            img[lo:hi] = 1
        return img.reshape(shape, order="F")


    def make_mask(self, df: pd.DataFrame, image_name: str='img.jpg', shape: tuple=(None, None)):
        """Source: https://www.kaggle.com/artgor/segmentation-in-pytorch-using-convenient-tools"""
        encoded_masks = df.loc[df['im_id'] == image_name, 'EncodedPixels']
        masks = np.zeros((shape[0], shape[1], 4), dtype=np.float32)
        for idx, label in enumerate(encoded_masks.values):
            try:
                mask = self.rle_decode(label, shape)
            except:
                mask = np.zeros(shape)
            masks[:, :, idx] = mask      
        return masks

    def __getitem__(self, idx):
        image_name = self.img_ids[idx]
        image_path = os.path.join(self.image_folder, image_name)
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        mask = self.make_mask(self.df, image_name=image_name, shape=(img.shape[0],img.shape[1]))

        augmented = self.transforms(image=img, mask=mask) 
        img = augmented["image"]
        mask = augmented["mask"]
        mask = np.transpose(augmented["mask"], [2, 0, 1])

        return img, mask

    def __len__(self):
        return len(self.img_ids)
