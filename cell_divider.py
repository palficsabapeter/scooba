import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from matplotlib import pyplot as plt

import config as c
import progress_bar as pb


def is_mountain_pixel(rgb: []):
    mountain_rgb = c.mountain_terrain.rgb
    desert_mountain_rgb = c.desert_mountain_terrain.rgb
    impassable_mountain_rgb = c.impassable_mountain_terrain.rgb

    is_mountain = mountain_rgb[0] == rgb[0] and mountain_rgb[1] == rgb[1] and mountain_rgb[2] == rgb[2]
    is_desert_mountain = desert_mountain_rgb[0] == rgb[0] and desert_mountain_rgb[1] == rgb[1] and desert_mountain_rgb[2] == rgb[2]
    is_impassable_mountain = impassable_mountain_rgb[0] == rgb[0] and impassable_mountain_rgb[1] == rgb[1] and impassable_mountain_rgb[2] == rgb[2]

    return is_mountain or is_desert_mountain or is_impassable_mountain


def check_for_up_way(i: int, j: int, pixels: [[]], height):
    if i + 1 < height:
        next_pixel = pixels[i + 1, j]
        if is_mountain_pixel(next_pixel[:3]) and next_pixel[3] != 1:
            return True
    return False


def check_for_down_way(i: int, j: int, pixels: [[]]):
    if i - 1 >= 0:
        next_pixel = pixels[i - 1, j]
        if is_mountain_pixel(next_pixel[:3]) and next_pixel[3] != 1:
            return True
    return False


def check_for_left_way(i: int, j: int, pixels: [[]]):
    if j - 1 >= 0:
        next_pixel = pixels[i, j - 1]
        if is_mountain_pixel(next_pixel[:3]) and next_pixel[3] != 1:
            return True
    return False


def check_for_right_way(i: int, j: int, pixels: [[]], width):
    if j + 1 < width:
        next_pixel = pixels[i, j + 1]
        if is_mountain_pixel(next_pixel[:3]) and next_pixel[3] != 1:
            return True
    return False


def check_and_set_direction(i: int, j: int, pixels: [[]], width, height, is_first=False):
    if width > j >= 0 and height > i >= 0:
        if check_for_right_way(i, j, pixels, width):
            return True, "right"
        elif check_for_up_way(i, j, pixels, height):
            return True, "up"
        elif check_for_left_way(i, j, pixels):
            return True, "left"
        elif check_for_down_way(i, j, pixels):
            return True, "down"
        elif not is_first:
            return True, "back"

    return False, ""


def step_back_and_remove_direction(i: int, j: int, prev_dir):
    match prev_dir:
        case "right":
            return i, j - 1
        case "up":
            return i - 1, j
        case "left":
            return i, j + 1
        case "down":
            return i + 1, j
        case "":
            return -1, -1


def dfs(pixels: [[]], i, j, width, height, current_progress, full_progress):
    cell = []
    earlier_directions = []
    cell.append([i, j])
    pixels[i, j, 3] = 1
    current_progress += 1

    can_go, direction = check_and_set_direction(i, j, pixels, width, height, is_first=True)
    while can_go:
        pb.print_progress_bar(current_progress, full_progress, length=20)
        if pixels[i, j, 3] == 0:
            pixels[i, j, 3] = 1
            current_progress += 1
        if [i, j] not in cell:
            cell.append([i, j])

        if direction != "back":
            earlier_directions.append(direction)
        match direction:
            case "right":
                j += 1
                can_go, direction = check_and_set_direction(i, j, pixels, width, height)
            case "up":
                i += 1
                can_go, direction = check_and_set_direction(i, j, pixels, width, height)
            case "left":
                j -= 1
                can_go, direction = check_and_set_direction(i, j, pixels, width, height)
            case "down":
                i -= 1
                can_go, direction = check_and_set_direction(i, j, pixels, width, height)
            case "back":
                if len(earlier_directions) > 0:
                    prev_direction = earlier_directions.pop()
                    i, j = step_back_and_remove_direction(i, j, prev_direction)
                    can_go, direction = check_and_set_direction(i, j, pixels, width, height)
                else:
                    can_go = False

    return cell


def discover_by_dfs(pixels: [[]], i, j, width, height, cell_ctr, current_progress, full_progress):
    cell = []
    if is_mountain_pixel(pixels[i, j, :3]):
        cell = dfs(pixels, i, j, width, height, current_progress, full_progress)
        cell_ctr += 1

    return j, cell, cell_ctr


def skip_while_not_plain_or_in_cells(pixel_row: [], i, j, width, height, cells: [[]]):
    current = pixel_row[j]
    next = pixel_row[j + 1]
    while j + 1 < width and (pixel_row[j, 3] == 1 or (not is_mountain_pixel(current[:3]))):
        pb.print_progress_bar(i * width, width * height, length=20)
        current = next
        j += 1
        next = pixel_row[j]
    return j


def cellularize_image_array(pixels: [[]], full_progress):
    print("Cellularizing image array")
    height = len(pixels)
    width = len(pixels[0])
    cells = []
    cell_ctr = 0
    current_progress = 0

    for i, pixel_row in enumerate(pixels):
        j = 0
        for _, pixel in enumerate(pixel_row):
            while j + 1 < width is not None:
                j = skip_while_not_plain_or_in_cells(pixel_row, i, j, width, height, cells)
                j, cell, cell_ctr = discover_by_dfs(pixels, i, j, width, height, cell_ctr, current_progress, full_progress)

                if len(cell) > 0:
                    cells.append(cell)

    return cells


def load_image_into_array(image_path):
    image = Image.open(image_path)
    width, height = image.size
    cellularizable_pixels = 0

    print(f"Width of the image: {width}")
    print(f"Height of the image: {height}")
    print(f"Loading image into array")
    arr = np.array(image)
    for i, row in enumerate(arr):
        for j, pixel in enumerate(row):
            pb.print_progress_bar(i * width, width * height, length=20)
            rgb_no_alpha = arr[i, j, :3]
            if not is_mountain_pixel(rgb_no_alpha):
                arr[i, j, 3] = 1
            else:
                arr[i, j, 3] = 0
                cellularizable_pixels += 1

    return arr, cellularizable_pixels


def save_cells(cells: [], output_folder):
    for i, cell in enumerate(cells):
        min_x = -1
        min_y = -1
        max_x = 0
        max_y = 0
        if len(cell) >= 10:
            for _, pixel in enumerate(cell):
                x = pixel[0]
                y = pixel[1]
                if x < min_x or min_x < 0:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y or min_y < 0:
                    min_y = y
                if y > max_y:
                    max_y = y

            height = max_y - min_y + 1
            width = max_x - min_x + 1
            arr = np.zeros((height, width))
            for _, pixel in enumerate(cell):
                x = pixel[0] - min_x
                y = pixel[1] - min_y
                arr[y, x] = 1

            arr = np.transpose(arr)
            save_noise_map(arr, output_folder, f"_{i}_{min_y}x{min_x}")


def save_noise_map(noise_array, output_folder, axis):
    filename = f"cellularized{axis}.png"
    output_path = Path(output_folder).resolve() / filename
    plt.imsave(output_path, noise_array, cmap="gray")
    print(f"Successfully persisted cell divided noise file at {output_path}")


def resolve_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("src", help="The path of the source file")
    args = vars(parser.parse_args())

    src = args["src"]
    return src


if __name__ == "__main__":
    src = resolve_args()
    output_folder = Path("./output/cell_noise").resolve()
    if not output_folder.exists():
        output_folder.mkdir(parents=True)

    arr, full_progress = load_image_into_array(src)
    cells = cellularize_image_array(arr, full_progress)
    save_cells(cells, output_folder)
