import os

import cv2
import numpy as np
import pandas as pd
from hydra.utils import get_original_cwd
from omegaconf import DictConfig
from torch.utils.data import Dataset


class CloudDataset(Dataset):
    def __init__(
        self, df: pd.DataFrame, cfg: DictConfig, img_ids, transforms, preprocessing
    ):
        self.df = df
        self.image_folder = os.path.join(get_original_cwd(), cfg.image_in_dir)
        self.mask_folder = os.path.join(get_original_cwd(), cfg.masks_in_dir)
        self.img_ids = img_ids
        self.transforms = transforms
        self.preprocessing = preprocessing

    def __getitem__(self, idx):
        image_name = self.img_ids[idx]
        mask_path = os.path.join(self.mask_folder, image_name + ".npy")
        image_path = os.path.join(self.image_folder, image_name)
        img = cv2.imread(image_path)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mask = np.load(mask_path, allow_pickle=False)
        augmented = self.transforms(image=img, mask=mask)
        img = augmented["image"]
        mask = augmented["mask"]
        mask = np.transpose(augmented["mask"], [2, 0, 1])
        return img, mask

    def __len__(self):
        return len(self.img_ids)
