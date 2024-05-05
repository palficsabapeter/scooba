from PIL import Image
import argparse
from pathlib import Path
import config

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


def replace_color(pixel_colors, width):
    replaced_colors = []
    for i, pixel in enumerate(pixel_colors):
        pixelNoAlpha = tuple(pixel[:3])
        if isinstance(pixel, tuple) and len(pixel) == 4:
            if pixel[0] == pixel[1] == pixel[2] == 0:
                avg_color = get_average_color(pixel_colors, i, width)
                replaced_colors.append(avg_color)
            elif pixelNoAlpha in config.color_conversion_map:
                replaced_colors.append(config.color_conversion_map[pixelNoAlpha])
            else:
                replaced_colors.append(pixel)
        else:
            print(f"Invalid pixel format: {pixel}")
    return replaced_colors


def get_average_color(pixel_colors, index, width):
    total_r = total_g = total_b = 0
    count = 0

    for y_offset in range(-1, 2):
        for x_offset in range(-1, 2):
            if x_offset == y_offset == 0:
                continue  # Skip the center pixel
            neighbor_index = index + y_offset * width + x_offset
            if 0 <= neighbor_index < len(pixel_colors):
                color = pixel_colors[neighbor_index]
                if color[0] == color[1] == color[2] == 0: # if black, do not count this in  average
                    continue
                if color[:3] in config.color_conversion_map: # if found in conversion map, use the converted color
                    conversion_color = config.color_conversion_map[color[:3]]
                    total_r += conversion_color[0]
                    total_g += conversion_color[1]
                    total_b += conversion_color[2]
                    count += 1

    avg_r = total_r // count if count > 0 else 0
    avg_g = total_g // count if count > 0 else 0
    avg_b = total_b // count if count > 0 else 0

    return avg_r, avg_g, avg_b, 255

def compile_image(pixel_colors, width, height, output_path):
    print("Compiling image...")
    new_image = Image.new("RGBA", (width, height))
    new_image.putdata(pixel_colors)
    new_image.save(output_path)
    print(f"Image compiled and saved successfully at {output_path}")

def resolve_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("src", help="The path of the source file")
    parser.add_argument("dest", help="The path of the generated file")
    args = vars(parser.parse_args())

    src = args["src"]
    dest = Path(args["dest"]).resolve()
    if not dest.parent.exists():
        dest.parent.mkdir(parents=True)
    return tuple((src, dest))

if __name__ == "__main__":
    input_image_path, output_image_path = resolve_args()

    pixel_colors, width, height = get_pixel_colors(input_image_path)
    colors_replaced = replace_color(pixel_colors, width)
    compile_image(colors_replaced, width, height, output_image_path)
