import argparse
import random
from pathlib import Path

import imageio
import numpy as np
from PIL import Image

import config
import progress_bar as pb


def get_pixel_colors(image_path):
    image = Image.open(image_path)
    width, height = image.size
    print(f"Width of the image: {width}")
    print(f"Height of the image: {height}")
    pixel_colors = []
    for y in range(height):
        for x in range(width):
            pixel_color = image.getpixel((x, y))
            pixel_colors.append(pixel_color)
    return pixel_colors, width, height


def cast_to_16_bit(eight_bit_color):
    return int((eight_bit_color / 256) * 65536)


def mix_in_noise(luminosity, perlin_noise):
    floodplain_height = config.find_luminosity_by_name("floodplain")
    if luminosity <= floodplain_height:  # keep water and lowland as is
        return luminosity

    impassable_mountain_height = config.find_luminosity_by_name("impassable mountain")
    mountain_height = config.find_luminosity_by_name("mountain")
    hill_height = config.find_luminosity_by_name("hill")
    plain_height = config.find_luminosity_by_name("plain")

    mountain_upward_tolerance = impassable_mountain_height - mountain_height
    mountain_downward_tolerance = mountain_height - hill_height
    hill_upward_tolerance = mountain_height - hill_height
    hill_downward_tolerance = hill_height - config.find_luminosity_by_name("floodplain")
    plain_upward_tolerance = hill_height - plain_height

    p_noise = 0
    if mountain_height <= luminosity:
        p_noise = mountain_upward_tolerance * perlin_noise
    elif hill_height <= luminosity < mountain_height:
        p_noise = hill_upward_tolerance * perlin_noise
    elif floodplain_height <= luminosity < hill_height:
        p_noise = plain_upward_tolerance * perlin_noise

    rand_base = 1 + 0.0625 - (random.randint(0, 625) / 10000)
    res = (luminosity * rand_base) + p_noise

    if luminosity >= impassable_mountain_height:
        # don't turn high mountains into Mars volcanoes
        if res > impassable_mountain_height:
            return impassable_mountain_height
        # don't turn high mountains too low
        elif res < impassable_mountain_height - mountain_downward_tolerance:
            return impassable_mountain_height - mountain_downward_tolerance
    elif luminosity >= mountain_height:
        # don't turn regular mountains into Mt. Everest
        if res > mountain_height + mountain_upward_tolerance:
            return mountain_height + mountain_upward_tolerance
        # don't turn high mountains too low
        elif res < mountain_height - mountain_downward_tolerance:
            return mountain_height - mountain_downward_tolerance
    elif luminosity >= hill_height:
        # don't turn regular mountains into Mt. Everest
        if res > hill_height + hill_upward_tolerance:
            return hill_height + hill_upward_tolerance
        # don't turn high mountains too low
        elif res < hill_height - hill_downward_tolerance:
            return hill_height - hill_downward_tolerance
    elif luminosity < hill_height:
        # don't turn lowland into water
        if res < floodplain_height:
            return floodplain_height
        # don't turn lowland into hills
        elif res > plain_height + plain_upward_tolerance:
            return plain_height + plain_upward_tolerance

    return int(res)


def replace_color(pixel_colors, width, convoluted_perlin_noise):
    print("Converting colors to luminosity")

    replaced_colors = []

    iteration_length = len(pixel_colors)

    print(f"Replacing pixel colors with luminosity")
    for i, pixel in enumerate(pixel_colors):
        pb.print_progress_bar(i, iteration_length, length=25)
        pixel_no_alpha = tuple(pixel[:3])

        perlin_noise_at_index = convoluted_perlin_noise[i]

        if isinstance(pixel, tuple) and len(pixel) == 4:
            if pixel[0] == pixel[1] == pixel[2] == 0:
                avg_l = get_average_color(pixel_colors, i, width)
                avg_l = mix_in_noise(avg_l, perlin_noise_at_index)
                replaced_colors.append(cast_to_16_bit(avg_l))
            elif config.find_luminosity_by_rgb(pixel_no_alpha):
                lum = config.find_luminosity_by_rgb(pixel_no_alpha)
                lum = mix_in_noise(lum, perlin_noise_at_index)
                replaced_colors.append(cast_to_16_bit(lum))
            else:
                replaced_colors.append(cast_to_16_bit(pixel[0]))
        else:
            print(f"Invalid pixel format: {pixel}")
    return replaced_colors


def get_average_color(pixel_colors, index, width):
    total_l = 0
    count = 0

    for y_offset in range(-1, 2):
        for x_offset in range(-1, 2):
            if x_offset == y_offset == 0:
                continue  # Skip the center pixel
            neighbor_index = index + y_offset * width + x_offset
            if 0 <= neighbor_index < len(pixel_colors):
                color = pixel_colors[neighbor_index]
                if color[0] == color[1] == color[2] == 0:  # if black, do not count this in  average
                    continue
                if config.find_luminosity_by_rgb(color[:3]):  # if found in conversion map, use the converted color
                    conversion_luminosity = config.find_luminosity_by_rgb(color[:3])
                    total_l += conversion_luminosity
                    count += 1

    avg_l = total_l // count if count > 0 else 0

    return avg_l


def compile_image(pixel_colors, width, height, output_file_path):
    print("Compiling image...")
    im = np.array(pixel_colors, np.uint16).reshape((height, width))
    imageio.imwrite(output_file_path, im)
    print(f"Image compiled and saved successfully at {output_file_path}")


def resolve_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("src", help="The path of the source file")
    args = vars(parser.parse_args())

    src = args["src"]
    return src


if __name__ == "__main__":
    input_image_path = resolve_args()
    output_file_path = Path("./output").resolve() / f"heightmap.png"
    if not output_file_path.parent.exists():
        output_file_path.parent.mkdir(parents=True)

    pixel_colors, width, height = get_pixel_colors(input_image_path)
    print("Reading noise map")
    perlin_noise = np.fromfile(f"./output/perlin_noise_{width}_{height}.noise", dtype=float)

    colors_replaced = replace_color(pixel_colors, width, perlin_noise)
    compile_image(colors_replaced, width, height, output_file_path)
