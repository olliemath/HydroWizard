# This script downloads all current weather from the met office

""" Set up local env """

import urllib
import json
import os.path as osp

home = osp.expanduser("~")
data_dir = osp.join(home, "WetWizard", "data")

with open(data_dir + "API_Auth") as f:
    API_Key = f.read()

""" Begin download """

met_url = "http://datapoint.metoffice.gov.uk/public/data/layer/wxobs/all/json/capabilities?key=" + API_Key

response = urllib.urlopen()
data = json.loads(response.read())

LayerName = "RADAR_UK_Composite_Highres"
def RainUrl(time):
    return "http://datapoint.metoffice.gov.uk/public/data/layer/wxobs/" + LayerName + "/png?TIME=" + time + "Z"
