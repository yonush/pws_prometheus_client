# Data formats

## Example metrics format for Prometheus

This is produced by the pws client

    ## HELP python_gc_objects_collected_total Objects collected during gc
    # TYPE python_gc_objects_collected_total counter
    python_gc_objects_collected_total{generation="0"} 471.0
    python_gc_objects_collected_total{generation="1"} 431.0
    python_gc_objects_collected_total{generation="2"} 0.0
    # HELP python_gc_objects_uncollectable_total Uncollectable objects found during GC
    # TYPE python_gc_objects_uncollectable_total counter
    python_gc_objects_uncollectable_total{generation="0"} 0.0
    python_gc_objects_uncollectable_total{generation="1"} 0.0
    python_gc_objects_uncollectable_total{generation="2"} 0.0
    # HELP python_gc_collections_total Number of times this generation was collected
    # TYPE python_gc_collections_total counter
    python_gc_collections_total{generation="0"} 95.0
    python_gc_collections_total{generation="1"} 8.0
    python_gc_collections_total{generation="2"} 0.0
    # HELP python_info Python platform information
    # TYPE python_info gauge
    python_info{implementation="CPython",major="3",minor="10",patchlevel="9",version="3.10.9"} 1.0
    # HELP dateutc Timestamp
    # TYPE dateutc gauge
    dateutc 0.0
    # HELP tempinf Indoor temperature °C
    # TYPE tempinf gauge
    tempinf 19.0
    # HELP humidityin Indoor humidity %
    # TYPE humidityin gauge
    humidityin 46.0
    # HELP baromrelin Barometric pressure hPa (relative)
    # TYPE baromrelin gauge
    baromrelin 1020.9
    # HELP baromabsin Barometric pressure hPa (absolute)
    # TYPE baromabsin gauge
    baromabsin 1021.3
    # HELP tempf Outdoor temperature °C
    # TYPE tempf gauge
    tempf 18.5
    # HELP humidity Outdoor humidity %
    # TYPE humidity gauge
    humidity 44.0
    # HELP winddir Wind direction °
    # TYPE winddir gauge
    winddir 184.0
    # HELP windspeedmph Windspeed Km/h
    # TYPE windspeedmph gauge
    windspeedmph 0.4
    # HELP windgustmph Windsgust Km/h
    # TYPE windgustmph gauge
    windgustmph 1.8
    # HELP maxdailygust Max daily wind gust Km/h
    # TYPE maxdailygust gauge
    maxdailygust 29.5
    # HELP solarradiation Solar Radiation w/m^2
    # TYPE solarradiation gauge
    solarradiation 88.47
    # HELP uv UV index
    # TYPE uv gauge
    uv 0.0
    # HELP rainratein Last 10 minutes rainfall multiplication 6
    # TYPE rainratein gauge
    rainratein 0.0
    # HELP eventrainin Event rain per hour ml/Hr
    # TYPE eventrainin gauge
    eventrainin 0.0
    # HELP hourlyrainin Rain per hour ml/Hr
    # TYPE hourlyrainin gauge
    hourlyrainin 0.0
    # HELP dailyrainin Rain per day in ml
    # TYPE dailyrainin gauge
    dailyrainin 0.0
    # HELP weeklyrainin Rain per week in ml
    # TYPE weeklyrainin gauge
    weeklyrainin 0.0
    # HELP monthlyrainin Rain per month in ml
    # TYPE monthlyrainin gauge
    monthlyrainin 0.0
    # HELP yearlyrainin Rain per year in L
    # TYPE yearlyrainin gauge
    yearlyrainin 0.13
    # HELP totalrainin Total rain since power on in L
    # TYPE totalrainin gauge
    totalrainin 0.13
    # HELP dewpt Dew point temperature in  °C
    # TYPE dewpt gauge
    dewpt 6.0
    # HELP chillpt Wind chill index °C
    # TYPE chillpt gauge
    chillpt 0.0
    # HELP frostpt Frost point temperature in °C
    # TYPE frostpt gauge
    frostpt 3.5
    # HELP feelslike Metservice "Feels Like" °C
    # TYPE feelslike gauge
    feelslike 18.5

## Ecowitt data format

This is produced by the dumper.py tool in the \tool folder

    b'{
    "path": "/data/report/", 
    "query_data": {}, 
    "post_data": "PASSKEY=????
    stationtype=EasyWeatherPro_V5.1.6
    runtime=267786
    heap=24292
    dateutc=2024-05-28+06:45:42
    tempinf=62.1
    humidityin=55
    baromrelin=29.743
    baromabsin=29.754
    tempf=52.2
    humidity=70
    winddir=282
    windspeedmph=0.00
    windgustmph=0.00
    maxdailygust=11.41
    solarradiation=0.00
    uv=0
    rainratein=0.000
    eventrainin=0.000
    hourlyrainin=0.000
    dailyrainin=0.000
    weeklyrainin=0.000
    monthlyrainin=0.071
    yearlyrainin=0.071
    totalrainin=0.071
    wh65batt=0
    freq=433M
    model=WS2900_V2.02.03
    interval=30", 

    "form_data": {"PASSKEY": "???", "stationtype": "EasyWeatherPro_V5.1.6", "runtime": "267786", "heap": "24292", "dateutc": "2024-05-28 06:45:42", "tempinf": "62.1", "humidityin": "55", "baromrelin": "29.743", "baromabsin": "29.754", "tempf": "52.2", "humidity": "70", "winddir": "282", "windspeedmph": "0.00", "windgustmph": "0.00", "maxdailygust": "11.41", "solarradiation": "0.00", "uv": "0", "rainratein": "0.000", "eventrainin": "0.000", "hourlyrainin": "0.000", "dailyrainin": "0.000", "weeklyrainin": "0.000", "monthlyrainin": "0.071", "yearlyrainin": "0.071", "totalrainin": "0.071", "wh65batt": "0", "freq": "433M", "model": "WS2900_V2.02.03", "interval": "30"}, 

    "cookies": {}}'

##  Wunderground data format

This is produced by the dumper.py tool in the \tool folder

    b'{
    "path": "/weatherstation/updateweatherstation.php", 

    "query_data": {"ID": ""
    "PASSWORD": ""
    "tempf": "51.3"
    "humidity": "72"
    "dewptf": "42.4"
    "windchillf": "51.3"
    "winddir": "282"
    "windspeedmph": "0.00"
    "windgustmph": "0.00"
    "rainin": "0.000"
    "dailyrainin": "0.000"
    "weeklyrainin": "0.000"
    "monthlyrainin": "0.071"
    "yearlyrainin": "0.071"
    "totalrainin": "0.071"
    "solarradiation": "0.00"
    "UV": "0"
    "indoortempf": "61.9"
    "indoorhumidity": "55"
    "absbaromin": "29.751"
    "baromin": "29.740"
    "lowbatt": "0"
    "dateutc": "now"
    "softwaretype": "EasyWeatherPro_V5.1.6"
    "action": "updateraw"
    "realtime": "1"
    "rtfreq": "5"}, 

    "post_data": "", 
    "form_data": {}, 
    cookies": {}

    }'

