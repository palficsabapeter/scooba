import argparse
import time
from pathlib import Path

import numpy
import numpy as np
from PIL import Image
from matplotlib import pyplot as plt
from perlin_numpy import generate_perlin_noise_2d


def save_noise_map(noise_array, width, height, seed, res1, res2, is_conv=False):
    filename = f"perlin_noise_{width}_{height}_{seed}_{res1}_{res2}"
    if is_conv:
        filename += "_convoluted.png"
    else:
        filename += ".png"

    output_path = output_folder / filename
    plt.imsave(output_path, noise_array, cmap="gray")
    print(f"Successfully persisted Perlin noise file at {output_path}")


def save_noise_map_data(noise_array: numpy.ndarray, width, height):
    noise_array.tofile(output_folder / f"perlin_noise_{width}_{height}.noise")


def convolve_noise_maps(noise_map_1, noise_map_2, ratio1=1.75, ratio2=0.25):
    h, w = noise_map_1.shape
    h2, w2 = noise_map_2.shape

    if h != h2 or w != w2:
        print(f"Invalid sizes. The two noise maps should have the same dimensions")

    arr = np.zeros((h, w))
    for i in range(h):
        for j in range(w):
            arr[i, j] = ((noise_map_1[i, j] * ratio1) + (noise_map_2[i, j] * ratio2)) / 2
    return arr


def generate_perlin_noises(width, height, save_images):
    seed = np.uint32(round(time.time()))
    pn1 = generate_perlin_noise(width, height, seed, 20, save_images)
    pn2 = generate_perlin_noise(width, height, seed, 25, save_images)
    pn3 = generate_perlin_noise(width, height, seed, 50, save_images)
    pn4 = generate_perlin_noise(width, height, seed, 100, save_images)

    print("Convoluting all noise maps")
    convoluted1 = convolve_noise_maps(pn1, pn2)
    convoluted2 = convolve_noise_maps(convoluted1, pn3)
    conv_all = convolve_noise_maps(convoluted2, pn4)
    if save_images:
        save_noise_map(conv_all, width, height, "all", 25, 100, True)

    save_noise_map_data(conv_all, width, height)
    return conv_all


def generate_perlin_noise(width, height, seed, res, save_images):
    print(f"Generating perlin noise map with seed {seed} and resolution {res}")
    np.random.seed(seed)

    noise = generate_perlin_noise_2d((height, width), (res, res))

    if save_images:
        save_noise_map(noise, width, height, seed, res, res)

    return noise


def resolve_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("working_file_path", help="The path of the working file")
    parser.add_argument("-s", "--save_images",
                        required=False, default=False,
                        help="This flag indicates whether the app should save the generated Perlin noise map as a file")
    args = vars(parser.parse_args())

    working_file_path = args["working_file_path"]
    save_images = bool(args["save_images"])
    return working_file_path, save_images


startup_msg = """
█▄░█ █▀█ █ █▀ █▀▀   █▀▀ █▀▀ █▄░█ █▀▀ █▀█ ▄▀█ ▀█▀ █▀█ █▀█
█░▀█ █▄█ █ ▄█ ██▄   █▄█ ██▄ █░▀█ ██▄ █▀▄ █▀█ ░█░ █▄█ █▀▄"""

output_folder = Path("./output/perlin_noise").resolve()

def run(working_file_path, save_images):
    print(startup_msg)

    image = Image.open(working_file_path)
    width, height = image.size

    if not output_folder.exists():
        output_folder.mkdir(parents=True)

    print("Generating noise maps")
    generate_perlin_noises(width, height, save_images)


if __name__ == "__main__":
    working_file_path, save_images = resolve_args()
    run(working_file_path, save_images)
