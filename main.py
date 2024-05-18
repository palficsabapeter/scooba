import argparse
import random
from pathlib import Path

import imageio
import numpy as np
from PIL import Image

import cell_divider
import config
import diffusion_limited_aggregator
import noise_generator
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
    return int((eight_bit_color / 255) * 65536)


def mix_in_noise(luminosity, input_noise, mode):
    floodplain_height = config.find_luminosity_by_name("floodplain")
    if luminosity <= floodplain_height:  # keep water and lowland as is
        return luminosity

    impassable_mountain_height = config.find_luminosity_by_name("impassable mountain")
    mountain_height = config.find_luminosity_by_name("mountain")
    hill_height = config.find_luminosity_by_name("hill")
    plain_height = config.find_luminosity_by_name("plain")

    impassable_mountain_downward_tolerance = (impassable_mountain_height - hill_height) / 2
    mountain_upward_tolerance = impassable_mountain_height - mountain_height
    mountain_downward_tolerance = mountain_height - hill_height
    hill_upward_tolerance = mountain_height - hill_height
    hill_downward_tolerance = (hill_height - config.find_luminosity_by_name("floodplain")) / 2
    plain_upward_tolerance = hill_height - plain_height

    noise = 0
    res = 0
    rand_base = 1 + 0.0625 - (random.randint(0, 625) / 10000)
    if mode == "dla":
        normalized_dla = (input_noise - 0.5) * 2
        if normalized_dla > 1:
            print("above")
        elif normalized_dla < -1:
            print("below")
        if impassable_mountain_height <= luminosity:
            upheight = impassable_mountain_height / 4
            downheight = impassable_mountain_height - hill_height
            if normalized_dla > 0:
                res = upheight * normalized_dla
            else:
                res = downheight * normalized_dla
            res += impassable_mountain_height
        elif mountain_height <= luminosity:
            upheight = impassable_mountain_height - mountain_height
            downheight = mountain_height - plain_height
            if normalized_dla > 0:
                res = upheight * normalized_dla
            else:
                res = downheight * normalized_dla
            res += mountain_height
        elif hill_height <= luminosity < mountain_height:
            upheight = mountain_height - hill_height
            downheight = hill_height - floodplain_height
            if normalized_dla > 0:
                res = upheight * normalized_dla
            else:
                res = downheight * normalized_dla
            res += hill_height
        elif floodplain_height <= luminosity < hill_height:
            upheight = (hill_height - floodplain_height) / 2
            plain_center_height = floodplain_height + upheight
            res = plain_center_height + (upheight * normalized_dla)
    elif mode == "perlin":
        if mountain_height <= luminosity:
            noise = mountain_upward_tolerance * input_noise
        elif hill_height <= luminosity < mountain_height:
            noise = hill_upward_tolerance * input_noise
        elif floodplain_height <= luminosity < hill_height:
            noise = plain_upward_tolerance * input_noise
        res = (luminosity * rand_base) + noise

    if mode == "perlin":
        if luminosity >= impassable_mountain_height:
            # don't turn high mountains into Mars volcanoes
            if res > impassable_mountain_height + mountain_upward_tolerance:
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


def replace_color(pixel_colors, width, convoluted_perlin_noise, dla_arr):
    print("Converting colors to luminosity")

    replaced_colors = []

    iteration_length = len(pixel_colors)
    print(f"Replacing pixel colors with luminosity")
    for i, pixel in enumerate(pixel_colors):
        pb.print_progress_bar(i, iteration_length, length=25)
        pixel_no_alpha = tuple(pixel[:3])

        perlin_noise_at_index = convoluted_perlin_noise[i]
        dla_at_index = dla_arr[i]

        if isinstance(pixel, tuple) and len(pixel) == 4:
            if pixel[0] == pixel[1] == pixel[2] == 0:
                if pixel[3] == 255:
                    replaced_colors.append(cast_to_16_bit(pixel[0]))
                else:
                    replaced_colors.append(cast_to_16_bit(5))
            elif config.find_luminosity_by_rgb(pixel_no_alpha):
                lum = config.find_luminosity_by_rgb(pixel_no_alpha)
                if dla_at_index > 0:
                    lum = mix_in_noise(lum, dla_at_index, "dla")
                else:
                    lum = mix_in_noise(lum, perlin_noise_at_index, "perlin")
                replaced_colors.append(cast_to_16_bit(lum))
            else:
                replaced_colors.append(cast_to_16_bit(pixel[0]))
        else:
            print(f"Invalid pixel format: {pixel}")

    print("Averaging luminosities")
    for i, luminosity in enumerate(replaced_colors):
        if luminosity == 0:
            avg_l = get_average_luminosity(replaced_colors, i, width)
            replaced_colors[i] = avg_l

    return replaced_colors


def get_average_luminosity(pixel_luminosities, index, width):
    total_l = 0
    count = 0

    for y_offset in range(-1, 2):
        for x_offset in range(-1, 2):
            if x_offset == y_offset == 0:
                continue  # Skip the center pixel
            neighbor_index = index + y_offset * width + x_offset
            if 0 <= neighbor_index < len(pixel_luminosities):
                luminosity = pixel_luminosities[neighbor_index]
                if luminosity > 2:  # skip black pixels
                    total_l += luminosity
                    count += 1

    avg_l = total_l // count if count > 0 else 0

    return avg_l


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
    print("Running noise generator")
    #noise_generator.run(input_image_path, False)
    print("Reading noise map")
    perlin_noise = np.fromfile(noise_generator.output_folder / f"perlin_noise_{width}_{height}.noise", dtype=float)

    print("Running cell divider")
    #cell_divider.run(input_image_path)
    print("Running DLA")
    diffusion_limited_aggregator.run(input_image_path, False)

    dla_noise_map = np.fromfile(diffusion_limited_aggregator.output_folder / f"dla_{width}_{height}.noise", dtype=float)
    colors_replaced = replace_color(pixel_colors, width, perlin_noise, dla_noise_map)
    compile_image(colors_replaced, width, height, output_file_path)
