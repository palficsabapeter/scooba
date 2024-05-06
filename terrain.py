lowland_terrain_types = [
    "plain",
    "farmland",
    "desert",
    "oasis",
    "jungle",
    "forest",
    "taiga",
    "wetland",
    "steppe",
    "floodplain",
    "dryland",
    "impassable desert"
]

highland_terrain_types = [
    "hill",
    "mountain",
    "desert mountain",
    "impassable mountain"
]

land_terrain_types = lowland_terrain_types + highland_terrain_types

water_terrain_types = [
    "river",
    "sea",
    "impassable sea"
]

all_terrain_types = land_terrain_types + water_terrain_types


class Terrain:
    def __init__(self, name, rgb, luminosity):
        if name not in all_terrain_types:
            print(f"Invalid name input. Value must be one of {all_terrain_types}")
        self.name = name

        if isinstance(rgb, tuple) and len(rgb) == 3:
            if (0 <= rgb[0] <= 255 and
                    0 <= rgb[1] <= 255 and
                    0 <= rgb[2] <= 255):
                self.rgb = rgb
            else:
                print(f"Invalid rgb input. Values must be between 0..255.")
        else:
            print(f"Invalid rgb input. Value-type must be tuple of 3.")

        self.luminosity = luminosity

    def is_water(self):
        return self.name in water_terrain_types

    def is_land(self):
        return self.name in land_terrain_types

    def is_lowland(self):
        return self.name in lowland_terrain_types

    def is_highland(self):
        return self.name in highland_terrain_types
