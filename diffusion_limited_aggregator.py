import argparse
import random
import math
from PIL import Image
from pathlib import Path


import imageio
import numpy as np
from matplotlib import pyplot as plt
from scipy.ndimage import gaussian_filter
import progress_bar as pb


def cast_to_16_bit(eight_bit_color):
    return int((eight_bit_color / 256) * 65536)

def lookup(arr, coordinates: []):
    return arr[coordinates[0], coordinates[1]]


def neighbor_filled(arr, y, x):
    left = 0
    if x - 1 >= 0:
        left = lookup(arr, [y, x - 1])
    right = 0
    if x + 1 < width:
        right = lookup(arr, [y, x + 1])
    up = 0
    if y + 1 < height:
        up = lookup(arr, [y + 1, x])
    down = 0
    if y - 1 >= 0:
        down = lookup(arr, [y - 1, x])
    return left > 0 or right > 0 or up > 0 or down > 0


def generate(height, width, seed_spawn_area):
    max_seed_spawns = int(round(math.sqrt(math.sqrt(width * height))))
    min_seed_spawns = int(round(math.sqrt(max_seed_spawns)))
    num_of_seeds = random.randint(min_seed_spawns, max_seed_spawns)
    total = round((width * height) / 4)
    print(f"Generating DLA noise map with {num_of_seeds} seeds and {total} total peaks")
    arr = np.zeros((height, width))
    minimum_dist_of_seeds = 0
    dist_y = height / num_of_seeds
    dist_x = width / num_of_seeds
    if dist_y < dist_x:
        minimum_dist_of_seeds = dist_y
    else:
        minimum_dist_of_seeds = dist_x
    ctr = 0
    seeds = []
    for i in range(num_of_seeds):
        seed_y = 0
        seed_x = 0
        in_allowed_seed_spawn_area = False
        while not in_allowed_seed_spawn_area:
            seed_y = random.randint(0, height - 1)
            seed_x = random.randint(0, width - 1)
            r, g, b = seed_spawn_area[seed_y, seed_x, :3]
            if r == g == b == 255:
                in_allowed_seed_spawn_area = True
            for j in range(i):
                prev_seed_y, prev_seed_x = seeds[j]
                if abs(prev_seed_y - seed_y) >= minimum_dist_of_seeds or abs(prev_seed_x - seed_x) >= minimum_dist_of_seeds:
                    in_allowed_seed_spawn_area = False
        seeds.append([seed_y, seed_x])
        arr[seed_y, seed_x] = cast_to_16_bit(255)
        ctr += 1

    allowed_dist_from_seed = round(minimum_dist_of_seeds / 2)

    i = 1
    while ctr < total:
        for _, seed in enumerate(seeds):
            weight = cast_to_16_bit((128 * ((total - i * 3) / total)) + 127)
            x = 0
            y = 0
            seed_y = seed[0]
            seed_x = seed[1]
            pb.print_progress_bar(ctr, total, length=20)
            correctly_generated_start_coordinates = False
            freeze = False
            while not correctly_generated_start_coordinates:
                pb.print_progress_bar(ctr, total, length=20)
                min_x = seed_x - allowed_dist_from_seed
                if min_x < 0:
                    min_x = 0
                elif min_x >= width:
                    min_x = width - 1

                min_y = seed_y - allowed_dist_from_seed
                if min_y < 0:
                    min_y = 0
                elif min_y >= height:
                    min_y = height - 1
                x = random.randint(min_x, seed_x + allowed_dist_from_seed - 1)
                y = random.randint(min_y, seed_y + allowed_dist_from_seed - 1)
                if width > x >= 0 and 0 <= y < height and arr[y, x] == 0:
                    correctly_generated_start_coordinates = True

            while not freeze:
                pb.print_progress_bar(ctr, total, length=20)
                if neighbor_filled(arr, y, x):
                    arr[y, x] = weight
                    freeze = True
                    ctr += 1
                else:
                    direction = random.randint(0, 3)
                    match direction:
                        case 0:  # left
                            if x - 1 >= 0:
                                x -= 1
                        case 1:  # right
                            if x + 1 < width:
                                x += 1
                        case 2:  # up
                            if y + 1 < height:
                                y += 1
                        case 3:  # down
                            if y - 1 >= 0:
                                y -= 1

        if allowed_dist_from_seed < width and allowed_dist_from_seed < height:
            allowed_dist_from_seed += 5
        i += 1

    return arr


def save_noise_map(noise_array, output_folder):
    filename = f"dla.png"
    output_path = Path(output_folder).resolve() / filename

    for i, row in enumerate(noise_array):
        for j, p in enumerate(row):
            if p == 0:
                noise_array[i, j] = cast_to_16_bit(127)
    im = np.array(noise_array, np.uint16)
    blurred = gaussian_filter(im, sigma=2)
    imageio.imwrite(output_path, blurred)
    print(f"Successfully persisted DLA noise file at {output_path}")


def resolve_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("src", help="The path of the source file")
    args = vars(parser.parse_args())

    src = args["src"]
    return src


if __name__ == "__main__":
    image_path = resolve_args()
    image = Image.open(image_path)
    width, height = image.size
    print(f"Loading image for DLA with size {width}, {height}")
    output_folder = Path("./output/dla").resolve()
    if not output_folder.exists():
        output_folder.mkdir(parents=True)

    image_array = np.asarray(image)
    noise_map = generate(height, width, image_array)
    save_noise_map(noise_map, output_folder)
