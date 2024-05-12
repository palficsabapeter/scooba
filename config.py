from terrain import Terrain

land_terrains = [
    Terrain("plain", (204, 163, 102), 20),
    Terrain("farmland", (255, 0, 0), 20),
    Terrain("hill", (90, 50, 12), 40),
    Terrain("mountain", (100, 100, 100), 80),
    Terrain("desert mountain", (23, 19, 38), 80),
    Terrain("impassable mountain", (36, 36, 36), 110),
    Terrain("desert", (255, 229, 0), 20),
    Terrain("oasis", (155, 143, 204), 18),
    Terrain("jungle", (10, 60, 35), 21),
    Terrain("forest", (71, 178, 45), 21),
    Terrain("taiga", (46, 153, 89), 21),
    Terrain("wetland", (76, 153, 153), 18),
    Terrain("steppe", (200, 100, 25), 20),
    Terrain("floodplain", (55, 31, 153), 18),
    Terrain("dryland", (220, 45, 120), 20),
]

all_terrains = land_terrains + [
    Terrain("desert", (255, 229, 0), 20),
    Terrain("oasis", (155, 143, 204), 18),
    Terrain("jungle", (10, 60, 35), 21),
    Terrain("forest", (71, 178, 45), 21),
    Terrain("taiga", (46, 153, 89), 21),
    Terrain("wetland", (76, 153, 153), 18),
    Terrain("steppe", (200, 100, 25), 20),
    Terrain("floodplain", (55, 31, 153), 18),
    Terrain("dryland", (220, 45, 120), 20),
    Terrain("impassable desert", (255, 180, 30), 20),
    Terrain("sea", (68, 107, 163), 5),
    Terrain("impassable sea", (51, 67, 85), 2),
    Terrain("river", (142, 232, 255), 7)
]


def find_luminosity_by_rgb(rgb):
    for terrain in all_terrains:
        if terrain.rgb == rgb:
            return terrain.luminosity

    print(f"Input rgb was not found in list of terrains.")
    return 0


def find_luminosity_by_name(name):
    for terrain in all_terrains:
        if terrain.name == name:
            return terrain.luminosity

    print(f"Input name was not found in list of terrains.")
    return 0
