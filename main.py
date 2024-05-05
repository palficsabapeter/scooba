from PIL import Image


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


def replace_color(pixel_colors, width, height):
    color_map = {
        (255, 255, 255, 255): (0, 0, 0, 255),  # White (transparent)
        (204, 162, 103, 255): (32, 32, 32, 255),  # Plains
        (254, 1, 0, 255): (46, 46, 46, 255),  # Farmlands
        (90, 51, 13, 255): (86, 86, 86, 255),  # Hills
        (101, 100, 101, 255): (150, 150, 150, 255),  # Mountains
        (254, 228, 0, 255): (34, 34, 34, 255),  # Desert
        (22, 19, 39, 255): (130, 130, 130, 255),  # Desert Mountain
        (154, 143, 205, 255): (40, 40, 40, 255),  # Oasis
        (11, 61, 35, 255): (46, 46, 46, 255),  # Jungle
        (71, 179, 44, 255): (54, 54, 54, 255),  # Forest
        (46, 152, 88, 255): (15, 15, 15, 255),  # Taiga
        (76, 153, 153, 255): (11, 11, 11, 255),  # Wetlands
        (200, 101, 24, 255): (30, 30, 30, 255),  # Steppe
        (54, 31, 152, 255): (7, 7, 7, 255),  # Floodplains
        (221, 44, 120, 255): (40, 40, 40, 255),  # Drylands
        (36, 37, 37, 255): (20, 20, 20, 255),  # Impassable Land
        (68, 106, 162, 255): (5, 5, 5, 255),  # Traversable Sea
        (51, 67, 85, 255): (2, 2, 2, 255),  # Impassable Sea
        (142, 233, 254, 255): (7, 7, 7, 255)  # Rivers
    }

    replaced_colors = []
    for i, pixel in enumerate(pixel_colors):
        if isinstance(pixel, tuple) and len(pixel) == 4:
            if pixel[0] == pixel[1] == pixel[2] == 0:
                avg_color = get_average_color(pixel_colors, i, width, height)
                replaced_colors.append(avg_color)
            elif pixel in color_map:
                replaced_colors.append(color_map[pixel])
            else:
                replaced_colors.append(pixel)
        else:
            print(f"Invalid pixel format: {pixel}")
    return replaced_colors


def get_average_color(pixel_colors, index, width, height):
    total_r = total_g = total_b = total_a = 0
    count = 0

    for y_offset in range(-1, 2):
        for x_offset in range(-1, 2):
            if x_offset == y_offset == 0:
                continue  # Skip the center pixel
            neighbor_index = index + y_offset * width + x_offset
            if 0 <= neighbor_index < len(pixel_colors):
                color = pixel_colors[neighbor_index]
                if color[0] == color[1] == color[2] == 0:  # Check if pixel is black
                    total_r += color[0]
                    total_g += color[1]
                    total_b += color[2]
                    total_a += color[3]
                    count += 1

    avg_r = total_r // count if count > 0 else 0
    avg_g = total_g // count if count > 0 else 0
    avg_b = total_b // count if count > 0 else 0
    avg_a = total_a // count if count > 0 else 0

    return avg_r, avg_g, avg_b, avg_a





def compile_image(pixel_colors, width, height, output_path):
    print("Compiling image...")
    new_image = Image.new("RGBA", (width, height))
    new_image.putdata(pixel_colors)
    new_image.save(output_path + ".png")
    print(f"Image compiled and saved successfully at {output_path}.png")


input_image_path = "images/tiroshmap_1.png"
output_image_path = "C:\\Users\\ERR0R\\PycharmProjects\\pythonProject\\images"
pixel_colors, width, height = get_pixel_colors(input_image_path)
colors_replaced = replace_color(pixel_colors, width, height)
compile_image(colors_replaced, width, height, output_image_path)
