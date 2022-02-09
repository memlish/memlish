import os
from pathlib import PurePath, Path
from typing import List, Union, Tuple
from tqdm.auto import tqdm

import numpy as np
from PIL import Image

IMG_FILE_EXTENSIONS = ['JPEG', 'JPG', 'PNG',
                       'BMP', 'MPO', 'PPM', 'TIFF', 'GIF']


def is_valid_image(path):
    try:
        im = Image.open(path).verify()
        return True
    except:
        return False


def get_invalid_images(img_dir):
    invalid_images = []
    for f in tqdm(list(Path(img_dir).iterdir())):
        if has_valid_image_extension(f) and not is_valid_image(f):
            invalid_images.append(f)

    return invalid_images


def delete_files(file_list):
    for f in file_list:
        f.unlink()


def has_valid_image_extension(filename: str) -> bool:
    extension = Path(filename).suffix.replace('.', '')
    return extension.upper() in IMG_FILE_EXTENSIONS


def _check_3_dim(image_arr_shape: Tuple) -> None:
    assert image_arr_shape[2] == 3, (
        f'Received image array with shape: {image_arr_shape}, expected image array shape is '
        f'(x, y, 3)'
    )


def _add_third_dim(image_arr_2dim: np.ndarray) -> np.ndarray:
    image_arr_3dim = np.tile(
        image_arr_2dim[..., np.newaxis], (1, 1, 3)
    )  # convert (x, y) to (x, y, 3) (grayscale to rgb)
    return image_arr_3dim


def _raise_wrong_dim_value_error(image_arr_shape: Tuple) -> None:

    raise ValueError(
        f'Received image array with shape: {image_arr_shape}, expected number of image array dimensions are 3 for '
        f'rgb image and 2 for grayscale image!'
    )


def check_image_array_hash(image_arr: np.ndarray) -> None:

    image_arr_shape = image_arr.shape
    if len(image_arr_shape) == 3:
        _check_3_dim(image_arr_shape)
    elif len(image_arr_shape) > 3 or len(image_arr_shape) < 2:
        _raise_wrong_dim_value_error(image_arr_shape)


def expand_image_array_cnn(image_arr: np.ndarray) -> np.ndarray:

    image_arr_shape = image_arr.shape
    if len(image_arr_shape) == 3:
        _check_3_dim(image_arr_shape)
        return image_arr
    elif len(image_arr_shape) == 2:
        image_arr_3dim = _add_third_dim(image_arr)
        return image_arr_3dim
    else:
        _raise_wrong_dim_value_error(image_arr_shape)


def preprocess_image(
    image,
    target_size: Tuple[int, int] = None,
    grayscale: bool = False,
    return_np: bool = False,
) -> np.ndarray:
    if isinstance(image, np.ndarray):
        image = image.astype('uint8')
        image_pil = Image.fromarray(image)

    elif isinstance(image, Image.Image):
        image_pil = image
    else:
        raise ValueError(
            'Input is expected to be a numpy array or a pillow object!')

    if target_size:
        image_pil = image_pil.resize(target_size, Image.ANTIALIAS)

    if grayscale:
        image_pil = image_pil.convert('L')

    if return_np:
        return np.array(image_pil).astype('uint8')
    else:
        return image_pil


def load_image(
    image_file: Union[PurePath, str],
    target_size: Tuple[int, int] = None,
    grayscale: bool = False,
    IMG_FILE_EXTENSIONS: List[str] = IMG_FILE_EXTENSIONS,
    return_np: bool = False,
):
    try:
        img = Image.open(image_file)

        # validate image format
        if img.format not in IMG_FILE_EXTENSIONS:
            print(f'Invalid image format {img.format}!')
            return None

        else:
            if img.mode != 'RGB':
                # convert to RGBA first to avoid warning
                # we ignore alpha channel if available
                img = img.convert('RGBA').convert('RGB')

            img = preprocess_image(
                img, target_size=target_size, grayscale=grayscale, return_np=return_np)

            return img

    except Exception as e:
        print(f'Invalid image file {image_file}:\n{e}')
        return None
