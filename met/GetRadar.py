# This script downloads rain radar maps from the met office

""" Set up local env """

import urllib
import json
import time
import calendar
import os
import os.path as osp

home = osp.expanduser("~")
data_dir = osp.join(home, "WetWizard", "data")

with open(osp.join(data_dir, "API_Auth")) as f:
    api_key = f.read()


""" First download a list of currently available time-stamps and find the new ones """

obs_layer = "http://datapoint.metoffice.gov.uk/public/data/layer/wxobs/"

capabilities_string = "all/json/capabilities?key="
capabilities_page = urllib.urlopen(obs_layer + capabilities_string + api_key)
capabilities_data = json.loads(capabilities_page.read())


# The times are in a horrible stringy format: this handles it.
class MetTime:
    def __init__(self, met_time):
        self.met_time = met_time
        self.ut = calendar.timegm(time.strptime(met_time, "%Y-%m-%dT%H:%M:%S"))


for layer in capabilities_data['Layers']['Layer']:
    if layer["Service"]["LayerName"] == "RADAR_UK_Composite_Highres":
        times = [MetTime(met_time) for met_time in layer["Service"]["Times"]["Time"]]

new_times = [met_time for met_time in times if met_time.ut not in os.listdir(osp.join(data_dir, "images"))]


""" Now we're ready to go get the rain radar image. """


def RainUrl(met_time):
    return obs_layer + "RADAR_UK_Composite_Highres/png?TIME=" + met_time + "Z&key=" + api_key

for met_time in new_times:
    image = urllib.urlopen(RainUrl(met_time.met_time))
    image_name = str(met_time.ut)
    with open(osp.join(data_dir, "images", image_name), "w") as f:
        f.write(image.read())
