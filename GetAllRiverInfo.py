# This script downloads information about all known rivers from the rainchasers
# api and stores them.

# Only use this to get all known info, get-ins, get-outs etc. A different script
# handles updating levels etc


""" Set up local environment """

import urllib
import json
import os.path as osp
import time

home = osp.expanduser("~")
data_dir = osp.join(home, "WetWizard", "data")


""" Now we're ready to download the data """

rivers = []
next_river = 'http://api.rainchasers.com/v1/river'


while True:
    attempts = 0
    response = None

    while attempts < 3:
        try:
            response = urllib.urlopen(next_river)
            break
        except IOError:
            attempts += 1
            time.sleep(5)
    if not response:
        raise IOError("resync fail at " + next_river)

    chunk = json.loads(response.read())
    if chunk['status'] != 200:
        raise IOError("resync fail at " + next_river)
    rivers += chunk['data']
    print(len(rivers))
    try:
        next_river = chunk['meta']['link']['next']
    except KeyError:
        next_river = chunk['meta']['link']['resume']
        break

with open(osp.join(data_dir, "ResumeLink.txt"), "w") as output:
    output.write(next_river)

with open(osp.join(data_dir, "CurrentRiverData.txt"), "w") as output:
    json.dump(rivers, output)
