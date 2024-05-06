from perlin_numpy import generate_perlin_noise_2d
import math
import numpy

def generate_perlin_noise(width, height, seed=0):
    print("Generating perlin noise map")
    numpy.random.seed(seed)
    gcd = int(math.gcd(width, height) / 2)
    noise = generate_perlin_noise_2d((height, width), (gcd, gcd))
    #plt.imsave("./output/perlin_noise.png", noise, cmap="gray")
    return noise
