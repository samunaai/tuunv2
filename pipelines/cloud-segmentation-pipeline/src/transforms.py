import albumentations as albu
from albumentations.pytorch.transforms import ToTensorV2


def get_train_aug():
    train_transform = [
        #  albu.Resize(320, 640),
        albu.HorizontalFlip(p=0.5),
        albu.VerticalFlip(p=0.5),
        albu.ShiftScaleRotate(
            scale_limit=0.3, rotate_limit=15, shift_limit=0.1, p=0.5, border_mode=0
        ),
        albu.GridDistortion(p=0.5),
        albu.OpticalDistortion(p=0.5, distort_limit=0.1, shift_limit=0.2),
        albu.RandomBrightnessContrast(p=0.5),
        albu.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ToTensorV2(),
    ]
    return albu.Compose(train_transform)


def get_valid_aug():
    test_transform = [
        # albu.Resize(320, 640),
        albu.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ToTensorV2(),
    ]
    return albu.Compose(test_transform)


def to_tensor(x):
    """
    Convert image or mask.
    """
    return x.transpose(2, 0, 1).astype("float32")


def get_preprocessing(preprocessing_fn):

    _transform = [
        #  albu.Lambda(image=preprocessing_fn),
        albu.Lambda(image=ToTensorV2(), mask=ToTensorV2()),
    ]
    return albu.Compose(_transform)
