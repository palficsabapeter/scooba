import argparse
import random
from pathlib import Path

import imageio
import numpy
from PIL import Image

import config
import noise_generator as ng


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


def mix_in_noise(luminosity, perlin):
    if luminosity <= 7:  # keep water as is
        return luminosity

    rand_base = 1 + 0.0625 - (random.randint(0, 625) / 10000)
    p_noise = 12 * perlin
    res = (luminosity * rand_base) + p_noise

    if (p_noise > 9 or p_noise < -9) and luminosity >= 18:
        print(f"Mess: P noise: {p_noise}, l: {luminosity}, res: {res}")

    # don't turn flatlands into water
    if luminosity >= config.find_luminosity_by_name("wetland") > res:
        res = config.find_luminosity_by_name("wetland")
    # neither turn flatlands into high hills
    elif luminosity < config.find_luminosity_by_name("hill") < res:
        res = config.find_luminosity_by_name("hill") + 1
    # neither turn hills into flatlands
    elif luminosity >= config.find_luminosity_by_name("hill") > res:
        res = config.find_luminosity_by_name("hill") - 1
    # neither turn hills into mountains
    elif luminosity < config.find_luminosity_by_name("mountain") < res:
        res = config.find_luminosity_by_name("mountain") + 1
    # neither turn mountains into hills
    elif luminosity >= config.find_luminosity_by_name("mountain") > res:
        res = config.find_luminosity_by_name("mountain") - 1
    # neither turn high mountains into Mars volcanoes
    elif res > config.find_luminosity_by_name("impassable mountain"):
        res = config.find_luminosity_by_name("impassable mountain") + 1

    return int(res)


def replace_color(pixel_colors, width, perlin_noise):
    print("Converting colors to luminosity")
    pn_arr = numpy.asarray(perlin_noise)
    replaced_colors = []

    for i, pixel in enumerate(pixel_colors):
        pixel_no_alpha = tuple(pixel[:3])
        x = int(i / width)
        y = int(i % width)
        pn = pn_arr[x][y]

        if isinstance(pixel, tuple) and len(pixel) == 4:
            if pixel[0] == pixel[1] == pixel[2] == 0:
                avg_l = get_average_color(pixel_colors, i, width)
                avg_l = mix_in_noise(avg_l, pn)
                replaced_colors.append(cast_to_16_bit(avg_l))
            elif config.find_luminosity_by_rgb(pixel_no_alpha):
                l = config.find_luminosity_by_rgb(pixel_no_alpha)
                l = mix_in_noise(l, pn)
                replaced_colors.append(cast_to_16_bit(l))
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
    im = numpy.array(pixel_colors, numpy.uint16).reshape((height, width))
    imageio.imwrite(output_file_path, im)
    print(f"Image compiled and saved successfully at {output_file_path}")


def resolve_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("src", help="The path of the source file")
    parser.add_argument("-s", "--seed", required=False, default=0, help="The seed used during Perlin noise generation")
    parser.add_argument("-p", "--save_perlin_noise_file",
                        required=False, default=False,
                        help="This flag indicates whether the app should save the generated Perlin noise map as a file.")
    args = vars(parser.parse_args())

    src = args["src"]
    seed = int(args["seed"])
    save_perlin_noise_file = args["save_perlin_noise_file"]
    return src, seed, save_perlin_noise_file


if __name__ == "__main__":
    input_image_path, seed, save_perlin_noise_file = resolve_args()
    output_file_path = Path("./output").resolve() / f"heightmap_{seed}.png"
    if not output_file_path.parent.exists():
        output_file_path.parent.mkdir(parents=True)

    pixel_colors, width, height = get_pixel_colors(input_image_path)
    pn = ng.generate_perlin_noise(width, height, seed, save_perlin_noise_file)

    colors_replaced = replace_color(pixel_colors, width, pn)
    compile_image(colors_replaced, width, height, output_file_path)
