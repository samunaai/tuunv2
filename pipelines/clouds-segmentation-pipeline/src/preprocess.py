import os
from typing import List

import cv2
import numpy as np
import nvidia.dali.fn as fn
from hydra.utils import get_original_cwd
from nvidia import dali
from nvidia.dali import pipeline_def
from omegaconf import DictConfig
from tqdm import tqdm
import time


def preprocess(cfg: DictConfig):
    time_start = time.time()
    image_output_directory = os.path.join(get_original_cwd(), cfg.image_out_dir)
    mask_output_directory = os.path.join(get_original_cwd(), cfg.masks_out_dir)
    image_input_directory = os.path.join(get_original_cwd(), cfg.data_path, "train_images")

    os.makedirs(image_output_directory, exist_ok=True)
    os.makedirs(mask_output_directory, exist_ok=True)
    image_names = sorted([fname for fname in os.listdir(image_input_directory)])
    image_paths = sorted(
        [os.path.join(image_input_directory, fname) for fname in os.listdir(image_input_directory)]
    )
    pipeline = image_resizing_pipeline(
        file_names=image_paths,
        height_out=cfg.resize_height,
        width_out=cfg.resize_width,
        device=cfg.device,
        batch_size=cfg.batch_size,
        num_threads=10,
        device_id=0,
    )
    pipeline.build()
    num_batches = (
        len(image_names) // cfg.batch_size + 1
        if len(image_names) % cfg.batch_size != 0
        else 0
    )
    cur = 0
    for _ in tqdm(range(num_batches)):
        images = pipeline.run()
        if isinstance(images[0], dali.backend_impl.TensorListGPU):
            images = images[0].as_cpu()
        images = images.as_array()
        for j in range(len(images)):
            cv2.imwrite(
                os.path.join(image_output_directory, image_names[cur]),
                cv2.cvtColor(images[j], cv2.COLOR_BGR2RGB),
            )
            cur += 1
            if cur == len(image_names):
                break  # handling last batch of a smaller size
    print(f"Images have been resized and save to {image_output_directory}!")
    masks_file_names = [
        x.replace("train_images", "train_masks") + ".npy" for x in image_paths
    ]
    for i in tqdm(range(len(masks_file_names))):
        arr = np.load(masks_file_names[i])
        name = masks_file_names[i].split("/")[-1]
        resized_arr = np.zeros((cfg.resize_height, cfg.resize_width, 4))
        resized_arr[..., 0] = cv2.resize(
            arr[0],
            (cfg.resize_width, cfg.resize_height),
            interpolation=cv2.INTER_LINEAR,
        )
        resized_arr[..., 1] = cv2.resize(
            arr[1],
            (cfg.resize_width, cfg.resize_height),
            interpolation=cv2.INTER_LINEAR,
        )
        resized_arr[..., 2] = cv2.resize(
            arr[2],
            (cfg.resize_width, cfg.resize_height),
            interpolation=cv2.INTER_LINEAR,
        )
        resized_arr[..., 3] = cv2.resize(
            arr[3],
            (cfg.resize_width, cfg.resize_height),
            interpolation=cv2.INTER_LINEAR,
        )
        np.save(
            os.path.join(get_original_cwd(), os.path.join(cfg.masks_out_dir, name)),
            resized_arr,
        )
    print(f"Masks have been resized and saved to {cfg.masks_out_dir}!")
    time_end = time.time()
    return time.strftime("%Hh%Mm%Ss", time.gmtime(time_end - time_start))

@pipeline_def
def image_resizing_pipeline(
    file_names: List[str], height_out: int, width_out: int, device: str
):
    jpegs, _ = fn.readers.file(files=file_names)
    if device == "gpu":
        images = fn.decoders.image(jpegs, device="mixed")  # cpu, mixed
        images = fn.resize(images.gpu(), size=[height_out, width_out], device="gpu")
    else:
        images = fn.decoders.image(jpegs, device="cpu")  # cpu, mixed
        images = fn.resize(images, size=[height_out, width_out], device="cpu")
    return images
