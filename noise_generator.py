import math
from pathlib import Path

import numpy
from matplotlib import pyplot as plt
from perlin_numpy import generate_perlin_noise_2d


def generate_perlin_noise(width, height, seed, save_to_file):
    print(f"Generating perlin noise map with seed {seed}")
    numpy.random.seed(seed)
    gcd = int(math.gcd(width, height))
    noise = generate_perlin_noise_2d((height, width), (gcd, gcd))

    if save_to_file:
        output_path = Path("./output").resolve() / f"perlin_noise_{seed}.png"
        plt.imsave(output_path, noise, cmap="gray")
        print(f"Successfully persisted Perlin noise file at {output_path}")

    return noise
