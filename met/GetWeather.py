#!/usr/bin/env python2.7
# This script downloads rain radar maps from the met office

""" Set up local env """

import urllib
import json
import time
import calendar
import os
import os.path as osp
from optparse import OptionParser

home = osp.expanduser("~")
data_dir = osp.join(home, "WetWizard", "data")
image_dir = osp.join(data_dir, "images")

# We make all our data directories

with open(osp.join(data_dir, "API_Auth")) as f:
    api_key = f.read().rstrip()


""" First download a list of currently available time-stamps and find the new ones """

# Met office layers we're interested in
obs_layer = "http://datapoint.metoffice.gov.uk/public/data/layer/wxobs/"
fcs_layer = "http://datapoint.metoffice.gov.uk/public/data/layer/wxfcs/"

# We want them to return in JSON format
request_string = "all/json/capabilities?key="


# The times are in a horrible stringy format: this handles it.
class MetTime:
    def __init__(self, met_time):
        self.met_time = met_time
        self.ut = calendar.timegm(time.strptime(met_time, "%Y-%m-%dT%H:%M:%S"))


# The capabilities data is in massively tangled JSON format.
# This untangles things.
class MetData:
    def __init__(self, data):
        self.data = data
        self.layers = [_['Service']['LayerName'] for _ in data['Layers']['Layer']]

    def get_layer(self, layer_name):
        for layer in self.data['Layers']['Layer']:
            if layer['Service']['LayerName'] == layer_name:
                return layer
        raise KeyError("Layer not found", layer_name)

    def get_times(self, layer_name):
        try:
            return [MetTime(_) for _ in self.get_layer(layer_name)['Service']['Times']['Time']]
        except KeyError:
            return MetTime(self.get_layer(layer_name)['Service']['Timesteps']['@defaultTime'])

    def get_steps(self, layer_name):
        try:
            return self.get_layer(layer_name)['Service']['Timesteps']['Timestep']
        except KeyError:
            raise TypeError("Layer is not a forecast: ", layer_name)


# This function will ask the met what observations/forecasts are available and
# return a MetData class
def GetCapabilities(layer_name):
    page = urllib.urlopen(layer_name + request_string + api_key)
    return MetData(json.loads(page.read()))


""" Now we go get the data: it's a little too ad-hoc for me to see how to avoid re-using some code. """


# These helper functions take details of the layer we're trying to access and
# return an appropriate url.
def ObsUrl(layer_name, met_time):
    return obs_layer + layer_name + "/png?TIME=" + met_time + "Z&key=" + api_key


def FcsUrl(layer_name, met_time, step):
    return fcs_layer + layer_name + "/png?RUN=" + met_time + "Z&FORECAST=" + step + "&key=" + api_key


def GetRainObs():
    # Get avaiability from Met Office
    available_data = GetCapabilities(obs_layer)
    # Untangle
    times = available_data.get_times("RADAR_UK_Composite_Highres")
    if not osp.exists(osp.join(image_dir, "rain")):
        os.makedirs(osp.join(image_dir, "rain"))
    new_times = [t for t in times if str(t.ut) not in os.listdir(osp.join(image_dir, "rain"))]
    # Now download all the new images
    for t in new_times:
        image = urllib.urlopen(ObsUrl("RADAR_UK_Composite_Highres", t.met_time))
        image_data = image.read()
        # Sometimes the met office has only sent us annoying spam:
        if image_data == "Invalid timestep":
            continue
        image_name = str(t.ut)
        with open(osp.join(image_dir, "rain", image_name), "w") as f:
            f.write(image_data)


def GetTempObs():
    # This is actually the "0 hours ahead" time step in the forecast layer
    available_data = GetCapabilities(fcs_layer)
    # Untangle
    issued_at = available_data.get_times("Temperature")
    if not osp.exists(osp.join(image_dir, "temp")):
        os.makedirs(osp.join(image_dir, "temp"))
    if str(issued_at.ut) not in os.listdir(osp.join(image_dir, "temp")):
        image = urllib.urlopen(FcsUrl("Temperature", issued_at.met_time, "0"))
        image_data = image.read()
        # Get rid of spam
        if image_data == "Invalid timestep":
            return
        image_name = str(issued_at.ut)
        with open(osp.join(image_dir, "temp", image_name), "w") as f:
            f.write(image_data)


def GetRainFcs():
    available_data = GetCapabilities(fcs_layer)
    issued_at = available_data.get_times("Precipitation_Rate")
    steps = available_data.get_steps("Precipitation_Rate")
    # Make a new forecasts directory if it doesn't exist
    if not osp.exists(osp.join(image_dir, "forecasts", "rain")):
        os.makedirs(osp.join(image_dir, "forecasts", "rain"))
    for step in steps:
        image = urllib.urlopen(FcsUrl("Precipitation_Rate", issued_at.met_time, str(step)))
        image_data = image.read()
        if image_data == "Invalid timestep":
            continue
        # The "step" is number of hours ahead: we convert this to unix timestamp
        image_name = str(issued_at.ut + step * 3600)
        with open(osp.join(image_dir, "forecasts", "rain", image_name), "w") as f:
            f.write(image_data)


def GetTempFcs():
    available_data = GetCapabilities(fcs_layer)
    issued_at = available_data.get_times("Temperature")
    steps = available_data.get_steps("Temperature")
    if not osp.exists(osp.join(image_dir, "forecasts", "temp")):
        os.makedirs(osp.join(image_dir, "forecasts", "temp"))
    for step in steps:
        image = urllib.urlopen(FcsUrl("Temperature", issued_at.met_time, str(step)))
        image_data = image.read()
        if image_data == "Invalid timestep":
            continue
        image_name = str(issued_at.ut + step * 3600)
        with open(osp.join(image_dir, "forecasts", "temp", image_name), "w") as f:
            f.write(image_data)


""" Now we begin doing what the user wants: i.e. getting forecasts/observations/whatevs """

parser = OptionParser()
# Now add a set of booleans to work out what to do
parser.add_option("--rainobs", action="store_true", dest="rainobs", default=False,
                  help="Gets all available Rain Radar observations. These will be stored "
                  "at ~/WetWizard/data/images/rain.")
parser.add_option("--tempobs", action="store_true", dest="tempobs", default=False,
                  help="Gets temperatrue observation from most recent of 0900, 1500, 2100, or 0300. "
                  "These will be stored at ~/WetWizard/data/images/temp.")
parser.add_option("--rainfcs", action="store_true", dest="rainfcs", default=False,
                  help="Gets last issued set of precipitation forecast maps for 0-36 hours into the future. "
                  "These will be stored at ~/WetWizard/data/images/forecasts/rain.")
parser.add_option("--tempfcs", action="store_true", dest="tempfcs", default=False,
                  help="Gets last issued set of temperature forecast maps for 0-36 hours into the future. "
                  "These will be stored at ~/WetWizard/data/images/forecasts/temp.")
# Get the user's options
options, args = parser.parse_args()


# If no options given, do nothing
if not (options.rainobs or options.tempobs or options.rainfcs or options.tempfcs):
    print "Are you sure you don't want any weather data? Use --help to see available options."

if options.rainobs:
    GetRainObs()
if options.rainfcs:
    GetRainFcs()
if options.tempobs:
    GetTempObs()
if options.tempfcs:
    GetTempFcs()
