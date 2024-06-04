"""
Simple Prometheus client for EasyWeatherPro
The weather station data is based on the Tesa WS-2980c PRO personal weather station (PWS). 
This uses the EasyWeatherPro firmware found in many other PWS's (Ambient Weather, Ecowitt and other Fine Offset clones)

    Port 1111 is open for incoming telemetry from the Weather station - 30-60sec update cycle
    Port 8080 is open for scrape requests from Prometheus - 30sec update loop
    Stop this Prometheus Exporter client
    Metrics being sent to the Prometheus server uses Ecowitt or wundergraound format
    Currently using the Ecowitt data format - examples at the end of the file

    http://192.168.1.229/weatherServices.html
    version 1.0
"""

import json
import math
import sys

import gevent  # https://www.gevent.org/
from flask import Flask, request, send_file
from gevent.pywsgi import WSGIServer

# pip install prometheus_client
from prometheus_client import Gauge, start_http_server

# Weather station reciever Flask app
app = Flask("Weather")

PWSdata: dict = {}  # Incoming data from the PWS
isReady: bool = False  # make sure data has been read

# for i, v in enumerate(list):
# for k, v in dict.items()
pwsvar: list[str] = [
    "dateutc",
    "tempinf",
    "humidityin",
    "baromrelin",
    "baromabsin",
    "tempf",
    "humidity",
    "winddir",
    "windspeedmph",
    "windgustmph",
    "maxdailygust",
    "solarradiation",
    "uv",
    "rainratein",
    "eventrainin",
    "hourlyrainin",
    "dailyrainin",
    "weeklyrainin",
    "monthlyrainin",
    "yearlyrainin",
    "totalrainin",
    "dewpt",
    "chillpt",
    "frostpt",
    "feelslike",
]

pwsdesc: list[str] = [
    "Timestamp",
    "Indoor temperature °C",
    "Indoor humidity %",
    "Barometric pressure hPa (relative)",
    "Barometric pressure hPa (absolute)",
    "Outdoor temperature °C",
    "Outdoor humidity %",
    "Wind direction °",
    "Windspeed Km/h",
    "Windsgust Km/h",
    "Max daily wind gust Km/h",
    "Solar Radiation w/m^2",
    "UV index",
    "Last 10 minutes rainfall multiplication 6",
    "Event rain per hour ml/Hr",
    "Rain per hour ml/Hr",
    "Rain per day in ml",
    "Rain per week in ml",
    "Rain per month in ml",
    "Rain per year in L",
    "Total rain since power on in L",
    "Dew point temperature in  °C",
    "Wind chill index °C",
    "Frost point temperature in °C",
    'Metservice "Feels Like" °C',
]

gauges: dict[str, Gauge] = {}

# ======================
# Utility functions


def log(response: dict) -> None:
    """Log the JSON encoded telemetry to a text file

    Args:
        response (dict): key-value pairs from the POST request
    """
    try:
        f = open(".\\pws.txt", "a")
        # data = str(response)
        data = json.dumps(response)
        f.write(f"{data}\n")
        f.flush()
    finally:
        f.close()


def FtoC(T: float) -> float:
    """Convert Fahrenheit to Celsius

    Args:
        T (float): Temperature value in Fahrenheit

    Returns:
        float: Temperature value in Celsius
    """
    return round((T - 32) / 1.8, 1) if T is not None else 0


def CtoF(T: float) -> float:
    """Convert Fahrenheit to Celsius

    Args:
        T (float): Temperature value in Fahrenheit

    Returns:
        float: Temperature value in Celsius
    """
    return round((T * 1.8) + 32, 1) if T is not None else 0


def WindChillIndex(T: float, W: float) -> float:
    """Wind chill index/factor as based on the formula from
        https://en.wikipedia.org/wiki/Wind_chill
    Args:
        T (float): Temperature in Celsius
        W (float): Wind speed in Km/H

    Returns:
        float: wind chill index/factor
    """
    # Only for Temp < 10 °C and wind > 5Km/h
    if T < 10 or W < 5:
        return 0
    return round(
        13.112
        + (0.6215 * T)
        - 11.37 * math.pow(W, 0.16)
        + 0.3965 * T * math.pow(W, 0.16),
        0,
    )


def Frostpoint(T: float, Ts: float) -> float:  # in °C
    """Calculates the frost point temperature as per the formulae and constants in
        https://docs.vaisala.com/r/M211280EN-D/en-US/GUID-10D5B48D-8D47-40AF-9F4F-953C3C05CE13/GUID-060D9333-9043-49F3-9575-1C2AF978BBF9

    Args:
        T (float): Temperature in Celsius
        Ts (float):  Dew Point temperature in Celsius

    Returns:
        float: frost point temperature in Celsius
    """
    Ts_K = 273.15 + Ts
    T_K = 273.15 + T
    frostpoint_k = (
        Ts_K - T_K + 2671.02 / ((2954.61 / T_K) + 2.193665 * math.log(T_K) - 13.3448)
    )
    return round(frostpoint_k - 273.15, 1)


def Dewpoint(T: float, RH: float) -> float:  # in °C
    """Dew point as calculated in https://en.wikipedia.org/wiki/Dew_point
        Specifically the a & b constants from 1974 Psychrometry and Psychrometric Charts.
    Args:
        T (float): Temperature in Celsius
        RH (float): Relative humidity as %

    Returns:
        float: dew Point temperature in Celsius
    """
    A = 17.27
    B = 237.7
    alpha = ((A * T) / (B + T)) + math.log(RH / 100.0)
    return round((B * alpha) / (A - alpha), 1)


def FeelsLike(T: float, W: float, RH: float) -> float:
    """A feels like temperature value as per https://blog.metservice.com/FeelsLikeTemp
        This function combines three formula to produce one of four temperatures
        - Feels like temperature
        - Apparent temperature
        - Metservice rollover temperature
        - Actual measured temperature

    Args:
        T (float): Temperature in Celsius
        W (float): Wind speed in Km/H
        RH (float): Relative humidity as %

    Returns:
        float: Feels like temperature
    """
    # Dew point calculation - see above for details
    alpha = ((17.27 * T) / (237.7 + T)) + math.log(RH / 100.0)
    DP = (237.7 * alpha) / (17.27 - alpha)

    # Apparent temperature calculation
    Wms = (W * 1000) / 3600  # Km/h -> m/s
    AT = T + 0.33 * DP - 0.7 * Wms - 4.0

    # Windchill index
    WC = (
        13.112
        + (0.6215 * T)
        - 11.37 * math.pow(W, 0.16)
        + 0.3965 * T * math.pow(W, 0.16)
    )
    # Windchill
    if T < 10 and W > 4:
        return WC

    # Metservice rollover
    if T > 11 and T < 15:
        return T - ((T - DP) * (14 - T) / 4)
    # Max of Apparent or Measured Temp
    return max(T, AT)


# convert temperatures, distances, pressures and other calculations to local units
def LocaliseData(PWSdata: dict) -> dict:
    """Convert any imperial data (Feet, Miles, Fahrenheit) into metric (Meters, Kilometers, Celsius )
        also calculates some additional telemetry such as dew point, frost point, wind chill indx and "Feels Like"

    Args:
        PWSdata (dict): POST data as floats except for the dateutc (string)

    Returns:
        dict: Converted and calculaetd telemetry
    """
    # fix temperatures F to C
    # Celcius = (Fahrenheit - 32) / 1.8
    # Fahrenheit = (Celsius * 1.8) + 32
    PWSdata["tempinf"] = FtoC(PWSdata["tempinf"])
    PWSdata["tempf"] = FtoC(PWSdata["tempf"])

    # 1 hPa = 0.029529983071445 inHg
    # 1 inch of mercury = ±33.86 millibars or hPa.
    # sealevel is ±29.29inHg or 1013mb @ 1000feet or 305m
    # The air pressure at sea level is 1018 hPa (QNH)
    PWSdata["baromrelin"] = round(PWSdata["baromrelin"] / 0.029529983071445, 1)
    PWSdata["baromabsin"] = round(PWSdata["baromabsin"] / 0.029529983071445, 1)

    # convert miles to km
    # 1mile = 1.609344Km
    PWSdata["windspeedmph"] = round(PWSdata["windspeedmph"] * 1.609344, 1)
    PWSdata["windgustmph"] = round(PWSdata["windgustmph"] * 1.609344, 1)
    PWSdata["maxdailygust"] = round(PWSdata["maxdailygust"] * 1.609344, 1)

    # Calculate a couple of additonal metrics AFTER the above unit conversions
    PWSdata["dewpt"] = Dewpoint(PWSdata["tempf"], PWSdata["humidity"])
    PWSdata["frostpt"] = Frostpoint(PWSdata["tempf"], PWSdata["dewpt"])
    PWSdata["chillpt"] = WindChillIndex(PWSdata["tempf"], PWSdata["windspeedmph"])
    PWSdata["feelslike"] = FeelsLike(
        PWSdata["tempf"], PWSdata["windspeedmph"], PWSdata["humidity"]
    )

    return PWSdata


@app.route("/favicon.ico")
def favi():
    return send_file("./favicon.ico", mimetype="image/ico")


@app.route("/", methods=["GET"])
def index():
    """Simple front page, not really required by Prometheus client but is informative"""
    msg = """
        <H1>Simple Prometheus Exporter client for EasyWeatherPro </h2>
        <p>The weather station data is based on the Tesa WS-2980c PRO personal weather station (PWS). 
           This uses the EasyWeatherPro firmware found in many other PWS's (Ambient Weather, Ecowitt and other Fine Offset clones)
         <ul>
         <li>Port 1111 is open for incoming telemetry from the Weather station - 60sec send cycle</li>
         <li>Port 8080 is open for scrape requests from <a href="https://prometheus.io/">Prometheus</a> - 30sec update loop
         <li><a href="/stop">Stop</a> this Prometheus Exporter client</a>
         <li><a href="http://localhost:8080/metrics" target="_blank" rel="noopener noreferrer"  >Metrics</a> being sent to the Prometheus server</a>
         </ul>
    """
    return msg


@app.route("/stop", methods=["GET"])
def PWSstop():
    """The client tends to run in the background if run as a binary so this is used to stop the process"""
    sys.exit()


@app.route("/telemetry", methods=["GET", "POST"])
def posted() -> str:
    """The main weather station GET/POST handler for incoming telemety.
        The POST data is added to a staging list for further processing

    Returns:
        str: simple response text after the GET or POST has been handled
    """
    global PWSdata, pwsvar, isReady

    # transfer the weather station POST data to the staging list - PWSdata
    if request.method == "POST":
        PWSdata.clear()
        for k in pwsvar:
            try:
                if k in [
                    "dewpt",
                    "chillpt",
                    "frostpt",
                    "feelslike",
                ]:  # these are calculated and not in the POST data
                    PWSdata[k] = 0
                elif k == "dateutc":  # this is a string and not a gauge value
                    PWSdata[k] = request.form[k]
                else:
                    PWSdata[k] = float(request.form[k])  # convert to float
            except:
                ValueError(f"Invalid telemetry value {request.form[k]}")
        PWSdata = LocaliseData(PWSdata)  # data fixups
        log(PWSdata)

        isReady = True
        return f"Ok read."
    if request.method == "GET":
        return f"Weather Easy Weather Pro Prometheus Exporter."
    return f"Get request."


def process_request() -> None:
    """Main handler for the Promethus client - called once every 30 seconds to update the metrics"""
    global pwsvar, PWSdata, isReady
    # print(".", end="")

    # make sure there is some data
    if not isReady:
        return

    # iterate over the list of pws variables
    for k in pwsvar:
        # skip over the Timestamp, not a gauge variable
        if k == "dateutc":
            continue

        v: float = PWSdata[k]
        # now = datetime.strptime(PWSdata['dateutc'],"%Y-%m-%d %H:%M:%S") # e.g. '2024-06-03 01:02:17'
        # gauges['dateutc'].labels(data="data", readable_datetime=now).set(float(time.time()))
        try:
            gauges[k].set(v)
        except:
            ValueError(f"Unable to set {k} with {v}")

    isReady = False


"""
  Make the promeutheus client available for scrapping .
  Change the port below to suit your system if 8080 is not available - CLI is in progress
  browse to http://localhost:8080 to confirm operation
  Start the HTTP service and publish the metrics
"""
if __name__ == "__main__":
    # create the gauges for the PWS variables
    for i, v in enumerate(pwsvar):
        # g = Gauge("DateData","Date string data as a metric",["data", "readable_datetime"])
        # g.labels(data="data", readable_datetime="").set(0)
        g = Gauge(v, pwsdesc[i])
        g.set(0)
        gauges[v] = g

    # setup the personal webserver reciever
    pws = WSGIServer(("0.0.0.0", 1111), app)
    pws.start()

    # start the prometheus scraper endpoint
    start_http_server(8080, "0.0.0.0")
    while True:
        process_request()
        gevent.sleep(30)
