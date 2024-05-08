from pathlib import Path

import time

import numpy as np
from matplotlib import pyplot as plt
from perlin_numpy import generate_perlin_noise_2d


def convolve_noise_maps(noise_map_1, noise_map_2):
    print("Convolving two noise maps")
    h, w = noise_map_1.shape
    h2, w2 = noise_map_2.shape

    if h != h2 or w != w2:
        print(f"Invalide sizes. The two noise maps should have the same dimensions")

    arr = np.zeros((h, w))
    for i in range(h):
        for j in range(w):
            arr[i, j] = (noise_map_1[i, j] + noise_map_2[i, j]) / 2
    return arr

def generate_perlin_noises(width, height, num_of_perlin_noises, save_to_file):
    pn_arr = []
    for i in range(num_of_perlin_noises):
        seed = np.uint32(round(time.time()))
        pn1 = generate_perlin_noise(width, height, seed, 100, save_to_file)
        pn2 = generate_perlin_noise(width, height, seed, 25, save_to_file)
        convoluted = convolve_noise_maps(pn1, pn2)
        pn_arr.append(convoluted)
    return pn_arr

def generate_perlin_noise(width, height, seed, res, save_to_file):
    print(f"Generating perlin noise map with seed {seed} and resolution {res}")
    np.random.seed(seed)

    noise = generate_perlin_noise_2d((height, width), (res, res))

    if save_to_file:
        output_path = Path("./output").resolve() / f"perlin_noise_{seed}_{res}.png"
        plt.imsave(output_path, noise, cmap="gray")
        print(f"Successfully persisted Perlin noise file at {output_path}")

    return noise
