import argparse
import math
import random
from os import listdir
from os.path import isfile
from pathlib import Path

from matplotlib import pyplot as plt

import imageio
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

import cell_divider
import progress_bar as pb


def lookup(arr, coordinates: []):
    return arr[coordinates[0], coordinates[1]]


def neighbor_filled(height, width, arr, y, x):
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


def neighbor_in_allowed_seed_spawn_are(height, width, neighbor_seed_y, neighbor_seed_x, seed_spawn_area):
    if height > neighbor_seed_y >= 0 and width > neighbor_seed_x >= 0:
        left_r, left_g, left_b = seed_spawn_area[neighbor_seed_y, neighbor_seed_x, :3]
        if left_r == left_g == left_b == 255:
            return True
    return False


def neighbors_in_allowed_seed_spawn_area(height, width, seed_y, seed_x, seed_spawn_area):
    left_neighbor_y, left_neighbor_x = seed_y, seed_x - 1
    left_neighbor_in_allowed_seed_spawn_area = neighbor_in_allowed_seed_spawn_are(height, width, left_neighbor_y, left_neighbor_x, seed_spawn_area)

    right_neighbor_y, right_neighbor_x = seed_y, seed_x + 1
    right_neighbor_in_allowed_seed_spawn_area = neighbor_in_allowed_seed_spawn_are(height, width, right_neighbor_y,
                                                                                  right_neighbor_x, seed_spawn_area)
    up_neighbor_y, up_neighbor_x = seed_y + 1, seed_x
    up_neighbor_in_allowed_seed_spawn_area = neighbor_in_allowed_seed_spawn_are(height, width, up_neighbor_y,
                                                                                  up_neighbor_x, seed_spawn_area)
    down_neighbor_y, down_neighbor_x = seed_y - 1, seed_x
    down_neighbor_in_allowed_seed_spawn_area = neighbor_in_allowed_seed_spawn_are(height, width, down_neighbor_y,
                                                                                  down_neighbor_x, seed_spawn_area)
    return (left_neighbor_in_allowed_seed_spawn_area and
            right_neighbor_in_allowed_seed_spawn_area and
            up_neighbor_in_allowed_seed_spawn_area and
            down_neighbor_in_allowed_seed_spawn_area)


def generate(height, width, seed_spawn_area):
    max_fillable_pixels = 0
    for i, row in enumerate(seed_spawn_area):
        for j, p in enumerate(row):
            r, g, b = seed_spawn_area[i, j, :3]
            if r == g == b == 255:
                max_fillable_pixels += 1

    max_seed_spawns = int(round(math.sqrt(math.sqrt(max_fillable_pixels))))
    min_seed_spawns = int(round(math.sqrt(max_seed_spawns)))
    num_of_seeds = random.randint(min_seed_spawns, max_seed_spawns)
    total = round(max_fillable_pixels / 3)
    print(f"Generating DLA noise map with {num_of_seeds} seeds and {total} total peaks")
    arr = np.full((height, width), 0.5, dtype=float)
    minimum_dist_of_seeds = 0
    area_of_spawn = math.sqrt(max_fillable_pixels)
    if area_of_spawn == 0:
        return []
    dist_y = (height / area_of_spawn) - 1
    dist_x = (width / area_of_spawn) - 1
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
        lifetime = minimum_dist_of_seeds * minimum_dist_of_seeds * 5
        while not in_allowed_seed_spawn_area and lifetime > 0:
            lifetime -= 1
            seed_y = random.randint(0, height - 1)
            seed_x = random.randint(0, width - 1)
            r, g, b = seed_spawn_area[seed_y, seed_x, :3]
            if r == g == b == 255:
                in_allowed_seed_spawn_area = neighbors_in_allowed_seed_spawn_area(height, width, seed_y, seed_x, seed_spawn_area)
            for j in range(i):
                prev_seed_y, prev_seed_x = seeds[j]
                if abs(prev_seed_y - seed_y) >= minimum_dist_of_seeds or abs(
                        prev_seed_x - seed_x) >= minimum_dist_of_seeds:
                    in_allowed_seed_spawn_area = False
        seeds.append([seed_y, seed_x])
        arr[seed_y, seed_x] = 1.0
        ctr += 1

    allowed_dist_from_seed = 5

    i = 1
    while ctr < total:
        for _, seed in enumerate(seeds):
            weight = ((0.5 * ((total - i * 3) / total)) + 0.5)
            x = 0
            y = 0
            seed_y = seed[0]
            seed_x = seed[1]
            correctly_generated_start_coordinates = False
            freeze = False
            lifetime = allowed_dist_from_seed * allowed_dist_from_seed * 5
            while not correctly_generated_start_coordinates and lifetime > 0:
                lifetime -= 1
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
                if width > x >= 0 and 0 <= y < height and arr[y, x] <= 0.5:
                    correctly_generated_start_coordinates = True

            while not freeze and lifetime > 0:
                lifetime -= 1
                pb.print_progress_bar(ctr, total, length=20)
                r, g, b = seed_spawn_area[y, x, :3]
                if neighbor_filled(height, width, arr, y, x) and r == g == b == 255:
                    arr[y, x] = weight
                    freeze = True
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

            ctr += 1

        if allowed_dist_from_seed < width and allowed_dist_from_seed < height:
            allowed_dist_from_seed += 5
        i += 1

    return arr


def save_noise_map(noise_array, filename, prev_file=False):
    if prev_file:
        filename = filename[:-4] + f"_dla.png"
    output_path = Path(output_folder).resolve() / filename

    blurred = gaussian_filter(noise_array, sigma=2)
    plt.imsave(output_path, blurred, cmap="gray")
    print(f"Successfully persisted DLA noise file at {output_path}")


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
█▀▄ █ █▀▀ █▀▀ █░█ █▀ █ █▀█ █▄░█ ▄▄ █░░ █ █▀▄▀█ █ ▀█▀ █▀▀ █▀▄   ▄▀█ █▀▀ █▀▀ █▀█ █▀▀ █▀▀ ▄▀█ ▀█▀ █ █▀█ █▄░█
█▄▀ █ █▀░ █▀░ █▄█ ▄█ █ █▄█ █░▀█ ░░ █▄▄ █ █░▀░█ █ ░█░ ██▄ █▄▀   █▀█ █▄█ █▄█ █▀▄ ██▄ █▄█ █▀█ ░█░ █ █▄█ █░▀█"""

output_folder = Path("./output/dla").resolve()


def run(working_file, save_images):
    print(startup_msg)
    input_folder = cell_divider.output_folder
    files_only = [f for f in listdir(input_folder) if isfile(input_folder / f)]
    if not output_folder.exists():
        output_folder.mkdir(parents=True)

    noise_maps = []
    print(f"DLA is going to generate noise maps for {len(files_only)} files")
    for _, file_name in enumerate(files_only):
        file_path = input_folder / file_name
        image = Image.open(file_path)
        width, height = image.size
        print(f"Loading image {file_name} for DLA with size {width}, {height}")
        image_array = np.asarray(image)
        noise_map = generate(height, width, image_array)
        if save_images:
            save_noise_map(noise_map, file_name, True)

        separated = file_path.name.split("x")
        y = int(separated[1].split("_")[0].split(".")[0])
        x = int(separated[0].split("_")[2])
        noise_maps.append([noise_map, y, x])

    working_image = Image.open(working_file)
    width, height = working_image.size
    noise_array = np.full((height, width), 0.5, dtype=float)
    for _, noise_map_data in enumerate(noise_maps):
        noise_map = noise_map_data[0]
        y = noise_map_data[1]
        x = noise_map_data[2]
        for i, row in enumerate(noise_map):
            for j, p in enumerate(row):
                if p > 0.5:
                    real_y = y + i
                    real_x = x + j
                    noise_array[real_y, real_x] = p

    save_noise_map(noise_array, f"convoluted_{width}_{height}.png")

    blurred_image = Image.open(output_folder / f"convoluted_{width}_{height}.png")
    blurred_array = np.asarray(blurred_image)
    to_save = np.zeros((height, width), dtype=float)
    for i, row in enumerate(blurred_array):
        for j, pixel in enumerate(row):
            luminosity = pixel[0]
            to_save[i, j] = luminosity / 256
    to_save.tofile(output_folder / f"dla_{width}_{height}.noise")


if __name__ == "__main__":
    working_file, save_images = resolve_args()
    run(working_file, save_images)
