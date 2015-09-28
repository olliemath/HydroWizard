""" This script initially downloads information about all known rivers
    from the rainchasers api and stores them. Subsequently it will only
    download updates to their levels. """

# Set up local environment
import urllib
import json
from os import path
import time

home = path.expanduser("~")
data_dir = path.join(home, "WetWizard", "data")


def GetNewRivers(update_link):
    new_rivers = []
    # While there are new readings to download, go get them.
    while True:
        attempts = 0
        response = None

        # Robust url query
        while attempts < 3:
            try:
                response = urllib.urlopen(update_link)
                break
            except IOError:
                attempts += 1
                time.sleep(5)
        if not response:
            raise IOError("resync fail at " + update_link)

        chunk = json.loads(response.read())
        if chunk['status'] != 200:
            raise IOError("resync fail at " + update_link)
        new_rivers += chunk['data']
        print(len(new_rivers))
        try:
            update_link = chunk['meta']['link']['next']
        except KeyError:
            update_link = chunk['meta']['link']['resume']
            break
    return new_rivers


def UpdateDictionary(old_rivers, new_rivers, levels_dict):
    for entry in new_rivers:
        try:
            river = entry['river']
            section = entry['section']
            time = entry['state']['time']
            level = entry['state']['source']['value']
        except KeyError:
            continue

        # If section is unknown add to old_rivers metadata.. otherwise just update level
        if river in levels_dict:
            if section in levels_dict[river]:
                if time not in levels_dict[river][section]:
                    levels_dict[river][section][time] = level
            else:
                levels_dict[river][section] = {time: level}
                old_rivers.append(entry)
        else:
            levels_dict[river] = {section: {time: level}}
            old_rivers.append(entry)


def main():
    # Check if script has run before
    if path.isfile(path.join(data_dir, "RiverMetaData.json")):
        with open(path.join(data_dir, "RiverMetaData.json")) as f:
            river_dict = json.load(f)
        with open(path.join(data_dir, "RiverLevels.json")) as f:
            levels_dict = json.load(f)

        rivers = river_dict['rivers']
        update_link = river_dict['update_link']

    else:
        rivers = []
        levels_dict = {}
        update_link = 'http://api.rainchasers.com/v1/river'

    # Get / process new information
    new_rivers = GetNewRivers(update_link)
    UpdateDictionary(rivers, new_rivers, levels_dict)

    # Dump to files
    with open(path.join(data_dir, "RiverMetaData.json"), "w") as output:
        json.dump(dict(update_link=update_link, rivers=rivers), output)

    with open(path.join(data_dir, "RiverLevels.json"), "w") as output:
        json.dump(levels_dict, f)


if __name__ == "__main__":
    main()
