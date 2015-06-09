# This requires pypng to decode the image from colors to rain
# If you have pip then "pip install pypng" (need sudo if not in a virtualenv)

""" Set up local env """

import png
import os.path as osp
import os
import json

home = osp.expanduser("~")
image_dir = osp.join(home, "WetWizard", "data", "images")
rainarray_dir = osp.join(home, "WetWizard", "data", "rainarrays")


""" Now we work on conversion """

# Met office denotes rainy-ness by RGBA: we convert to a numerical system
color_dict = {(199, 191, 193, 128): 0, (0, 0, 254, 255): 1, (50, 101, 254, 255): 2, (127, 127, 0, 255): 3,
              (254, 203, 0, 255): 4, (254, 152, 0, 255): 5, (254, 0, 0, 255): 6, (254, 0, 254, 255): 7,
              (229, 254, 254, 255): 8, (0, 0, 0, 0): 0}


def MapMaker(image):
    FILE = osp.join(image_dir, image)

    # Get a list of RGBA-values giving the photo
    data = png.Reader(filename=FILE).read_flat()
    flat_list = data[2].tolist()

    # Single out the RBGA vectors
    pix_list = [tuple(flat_list[i:i+4]) for i in range(0, len(flat_list), 4)]

    # Now we convert the color to an interger from 0-8 representing raininess
    # For reference: 2 is 0.5-1 mm/hour, 3 is 1-2 mm/hour, etc
    rain_list = [color_dict[p] for p in pix_list]

    # Finally return this as a 500x500 array (list of lists)
    return [rain_list[i:i+500] for i in range(0, len(rain_list), 500)]


""" If run as main script we convert all new files """


def main():
    if not osp.exists(rainarray_dir):
        os.makedirs(rainarray_dir)
    rainarrays = os.listdir(rainarray_dir)
    images = os.listdir(image_dir)
    new_files = [filename for filename in images if filename not in rainarrays]

    count = 0.0
    total = len(new_files)
    for image in new_files:
        rain_map = MapMaker(image)
        with open(osp.join(rainarray_dir, image), "w") as f:
            json.dump(rain_map, f)
        count += 1
        print int(100 * count / total), "% done"

if __name__ == "__main__":
    main()
