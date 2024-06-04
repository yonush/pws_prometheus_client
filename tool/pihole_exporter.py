# !/usr/bin/env python3

#
#   Copyright (c) 2018 Daniel Schmitz
#
#   Permission is hereby granted, free of charge, to any person obtaining a copy
#   of this software and associated documentation files (the "Software"), to deal
#   in the Software without restriction, including without limitation the rights
#   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#   copies of the Software, and to permit persons to whom the Software is
#   furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included in all
#   copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#   SOFTWARE.

import argparse
import json
import socket
import urllib.request
from io import StringIO

from prometheus_metrics import exporter, generate_latest


class pihole_exporter(exporter):
    def __init__(self, url, auth, extended=False):
        super().__init__()
        self.url = url
        self.auth = auth
        self.api_url = f'http://{self.url}/admin/api.php'
        self.httpd = None
        self.extended = extended

        self.summary_raw_url = self.api_url + '?summaryRaw'
        self.top_item_url = self.api_url + '?topItems=100'
        self.top_sources_url = self.api_url + '?getQuerySources=100'
        self.forward_destinations_url = self.api_url + '?getForwardDestinations'
        self.query_types_url = self.api_url + '?getQueryTypes'
        self.get_all_queries_url = self.api_url + '?getAllQueries'
        self.metrics_handler.add('pihole_top_sources', 'client')
        self.metrics_handler.add('pihole_top_queries', 'domain')
        self.metrics_handler.add('pihole_top_ads', 'domain')
        self.metrics_handler.add('pihole_forward_destinations', 'resolver')
        self.metrics_handler.add('pihole_query_type', 'query_type')
        self.metrics_handler.add('pihole_client_queries',
                                 ['hostname', 'domain', 'answer_type'])

    def get_json(self, url):
        if self.auth:
            url += "&auth=%s" % self.auth
        response = urllib.request.urlopen(url)
        data = response.read()
        text = data.decode('utf-8')
        io = StringIO(text)
        json_text = json.load(io)
        return json_text

    def get_summary(self):
        summary_raw = self.get_json(self.summary_raw_url)

        for i in summary_raw:
            if i == "status":
                if summary_raw[i] == 'enabled':
                    self.metrics_handler.add_update(f'pihole_{i}', 1)
                else:
                    self.metrics_handler.add_update(f'pihole_{i}', 0)
            elif i == "gravity_last_updated":
                self.metrics_handler.add_update(f'pihole_{i}',summary_raw[i]['absolute'])
            else:
                self.metrics_handler.add_update(f'pihole_{i}',summary_raw[i])

    def get_exteneded_metrics(self):
        aq = self.get_json(self.get_all_queries_url)
        if aq:
            client_data = dict()
            for i in aq['data']:
                hostname = i[3]
                domain = i[2]
                answer_type = i[4]
                if not hostname in client_data:
                    client_data[hostname] = dict()
                if not domain in client_data[hostname]:
                    client_data[hostname][domain] = dict()
                if not answer_type in client_data[hostname][domain]:
                    client_data[hostname][domain][answer_type] = 1
                else:
                    client_data[hostname][domain][answer_type] += 1
            self.metrics_handler.update('pihole_client_queries', client_data)

    def generate_latest(self):
        self.get_summary()

        top_items = self.get_json(self.top_item_url)
        if top_items:
            for item in top_items:
                self.metrics_handler.update(f'pihole_{item}',top_items[item],
                )
        top_sources = self.get_json(self.top_sources_url)
        if top_sources:
            self.metrics_handler.update('pihole_top_sources',
                                        top_sources['top_sources'])

        fw_dest = self.get_json(self.forward_destinations_url)
        if fw_dest:
            self.metrics_handler.update('pihole_forward_destinations',
                                        fw_dest['forward_destinations'])

        qt = self.get_json(self.query_types_url)
        if qt:
            self.metrics_handler.update('pihole_query_type', qt['querytypes'])

        if self.extended:
            self.get_exteneded_metrics()

        return generate_latest()

    def make_wsgi_app(self):
        def prometheus_app(environ, start_response):
            output = self.generate_latest()
            status = str('200 OK')
            headers = [(str('Content-type'), str('text/plain'))]
            start_response(status, headers)
            return [output]

        return prometheus_app


def get_authentication_token():
    token = None
    filename = '/etc/pihole/setupVars.conf'
    try:
        with open(filename) as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith('WEBPASSWORD'):
                    token = line.split('=')[1]
                    return token
            return None
    except (FileNotFoundError):
        print(f"Unable to find: {filename}")


def main():
    parser = argparse.ArgumentParser(description='pihole_exporter')
    parser.add_argument(
        '-o', '--pihole', help='pihole adress', default='pi.hole')
    parser.add_argument(
        '-p',
        '--port',
        type=int,
        help='port pihole_exporter is listening on',
        default=9311)
    parser.add_argument(
        '-i',
        '--interface',
        help='interface pihole_exporter will listen on',
        default='0.0.0.0')
    parser.add_argument(
        '-a', '--auth', help='Pihole password hash', default=None)
    parser.add_argument(
        '-e',
        '--extended-metrics',
        help="Extended pihole metrics",
        action='store_true',
        default=False)
    args = parser.parse_args()

    #args.pihole = '192.168.1.5'
    args.auth = '0a3b6a2866a9e8b549c7906b167a5233374818f6b23c809a61ddac003ca89074'
    auth_token = args.auth
    if auth_token == None:
        auth_token = get_authentication_token()

    exporter = pihole_exporter(args.pihole, auth_token, args.extended_metrics)
    exporter.make_server(args.interface, args.port)


if __name__ == '__main__':
    main()
"""

# HELP python_gc_objects_collected_total Objects collected during gc
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 130.0
python_gc_objects_collected_total{generation="1"} 289.0
python_gc_objects_collected_total{generation="2"} 0.0
# HELP python_gc_objects_uncollectable_total Uncollectable objects found during GC
# TYPE python_gc_objects_uncollectable_total counter
python_gc_objects_uncollectable_total{generation="0"} 0.0
python_gc_objects_uncollectable_total{generation="1"} 0.0
python_gc_objects_uncollectable_total{generation="2"} 0.0
# HELP python_gc_collections_total Number of times this generation was collected
# TYPE python_gc_collections_total counter
python_gc_collections_total{generation="0"} 44.0
python_gc_collections_total{generation="1"} 3.0
python_gc_collections_total{generation="2"} 0.0
# HELP python_info Python platform information
# TYPE python_info gauge
python_info{implementation="CPython",major="3",minor="10",patchlevel="9",version="3.10.9"} 1.0
# HELP pihole_top_sources pihole top sources
# TYPE pihole_top_sources gauge
pihole_top_sources{client="Sora97.local|192.168.1.223"} 58974.0
pihole_top_sources{client="REDBITS.local|192.168.1.238"} 13319.0
pihole_top_sources{client="Rustyknife.local|192.168.1.2"} 12208.0
pihole_top_sources{client="DingoBox.local|192.168.1.205"} 9686.0
pihole_top_sources{client="Nathan-TNT.local|192.168.1.248"} 8365.0
pihole_top_sources{client="Galaxy-Note10.local|192.168.1.211"} 6585.0
pihole_top_sources{client="Helen-s-Note20-Ultra.local|192.168.1.237"} 4142.0
pihole_top_sources{client="S380HB.local|192.168.1.245"} 3502.0
pihole_top_sources{client="Helen-s-Note20-Ultra.local|192.168.1.226"} 3194.0
pihole_top_sources{client="John-s-S23-Ultra.local|192.168.1.222"} 2374.0
pihole_top_sources{client="HueBridge.local|192.168.1.202"} 2164.0
pihole_top_sources{client="plexy.local|192.168.1.4"} 1593.0
pihole_top_sources{client="amazon-ee64cf0cf.local|192.168.1.239"} 1217.0
pihole_top_sources{client="plexnas.local|192.168.1.218"} 940.0
pihole_top_sources{client="wlan0.local|192.168.1.215"} 875.0
pihole_top_sources{client="localhost|127.0.0.1"} 799.0
pihole_top_sources{client="Helen-s-Note20-Ultra.local|192.168.1.201"} 770.0
pihole_top_sources{client="Helen-s-Note20-Ultra.local|192.168.1.231"} 760.0
pihole_top_sources{client="SV11.local|192.168.1.235"} 617.0
pihole_top_sources{client="Helen-s-Note20-Ultra.local|192.168.1.204"} 535.0
pihole_top_sources{client="Nathan-TNT.local|192.168.1.230"} 513.0
pihole_top_sources{client="Helen-s-Note20-Ultra.local|192.168.1.209"} 449.0
pihole_top_sources{client="Galaxy-Note10.local|192.168.1.247"} 282.0
pihole_top_sources{client="REDBITS.local|192.168.1.236"} 138.0
pihole_top_sources{client="TAG009478.local|192.168.1.234"} 84.0
pihole_top_sources{client="wlan0.local|192.168.1.208"} 67.0
pihole_top_sources{client="Sora97.local|192.168.1.212"} 64.0
pihole_top_sources{client="Sora97.local|192.168.1.242"} 54.0
pihole_top_sources{client="John-s-S23-Ultra.local|192.168.1.219"} 54.0
pihole_top_sources{client="John-s-S23-Ultra.local|192.168.1.207"} 46.0
pihole_top_sources{client="WeatherStation.local|192.168.1.229"} 35.0
pihole_top_sources{client="kobo.local|192.168.1.203"} 30.0
pihole_top_sources{client="tvtplink.local|192.168.1.179"} 24.0
pihole_top_sources{client="Helen-s-Note20-Ultra.local|192.168.1.206"} 17.0
pihole_top_sources{client="Helen-s-Note20-Ultra.local|192.168.1.225"} 11.0
pihole_top_sources{client="Sora97.local|192.168.1.217"} 11.0
pihole_top_sources{client="Nathan-TNT.local|192.168.1.250"} 9.0
pihole_top_sources{client="Helen-s-Note20-Ultra.local|192.168.1.210"} 8.0
pihole_top_sources{client="S380HB.local|192.168.1.243"} 6.0
pihole_top_sources{client="espressif.local|192.168.1.227"} 6.0
pihole_top_sources{client="Flatblue.local|192.168.1.214"} 3.0
pihole_top_sources{client="Netatmo.local|192.168.1.244"} 1.0
# HELP pihole_top_queries pihole top queries
# TYPE pihole_top_queries gauge
pihole_top_queries{domain="wpad.local"} 12652.0
pihole_top_queries{domain="www.google.com"} 1474.0
pihole_top_queries{domain="p2p-ohi-2.anker-in.com"} 1452.0
pihole_top_queries{domain="p2p-cal-2.anker-in.com"} 1452.0
pihole_top_queries{domain="catalog.gamepass.com"} 1287.0
pihole_top_queries{domain="clients4.google.com"} 1135.0
pihole_top_queries{domain="datarouter.ol.epicgames.com"} 1122.0
pihole_top_queries{domain="api.amazonalexa.com"} 1073.0
pihole_top_queries{domain="plexy"} 936.0
pihole_top_queries{domain="data.meethue.com"} 877.0
pihole_top_queries{domain="staticcdn.duckduckgo.com"} 726.0
pihole_top_queries{domain="mtalk.google.com"} 694.0
pihole_top_queries{domain="clientsettingscdn.roblox.com"} 668.0
pihole_top_queries{domain="edge.microsoft.com"} 645.0
pihole_top_queries{domain="security-app.eufylife.com"} 598.0
pihole_top_queries{domain="connectivitycheck.gstatic.com"} 596.0
pihole_top_queries{domain="d3p8zr0ffa9t17.cloudfront.net"} 578.0
pihole_top_queries{domain="ssl.gstatic.com"} 542.0
pihole_top_queries{domain="account-public-service-prod03.ol.epicgames.com"} 478.0
pihole_top_queries{domain="login.microsoftonline.com"} 441.0
pihole_top_queries{domain="edge-term4-syd1.roblox.com"} 434.0
pihole_top_queries{domain="clients3.google.com"} 416.0
pihole_top_queries{domain="play.googleapis.com"} 405.0
pihole_top_queries{domain="safebrowsing.googleapis.com"} 388.0
pihole_top_queries{domain="thumbnails.roblox.com"} 381.0
pihole_top_queries{domain="www.youtube.com"} 374.0
pihole_top_queries{domain="ephemeralcounters.api.roblox.com"} 363.0
pihole_top_queries{domain="tr.rbxcdn.com"} 356.0
pihole_top_queries{domain="c7.rbxcdn.com"} 339.0
pihole_top_queries{domain="c5.rbxcdn.com"} 337.0
pihole_top_queries{domain="disney.api.edge.bamgrid.com"} 334.0
pihole_top_queries{domain="presence-public-service-prod.ol.epicgames.com"} 332.0
pihole_top_queries{domain="t6.rbxcdn.com"} 331.0
pihole_top_queries{domain="c1.rbxcdn.com"} 330.0
pihole_top_queries{domain="outlook.office365.com"} 330.0
pihole_top_queries{domain="c2.rbxcdn.com"} 329.0
pihole_top_queries{domain="c4.rbxcdn.com"} 323.0
pihole_top_queries{domain="t3.rbxcdn.com"} 323.0
pihole_top_queries{domain="c6.rbxcdn.com"} 322.0
pihole_top_queries{domain="t7.rbxcdn.com"} 321.0
pihole_top_queries{domain="c3.rbxcdn.com"} 319.0
pihole_top_queries{domain="t5.rbxcdn.com"} 318.0
pihole_top_queries{domain="apis.roblox.com"} 313.0
pihole_top_queries{domain="t0.rbxcdn.com"} 311.0
pihole_top_queries{domain="t4.rbxcdn.com"} 311.0
pihole_top_queries{domain="t1.rbxcdn.com"} 311.0
pihole_top_queries{domain="t2.rbxcdn.com"} 306.0
pihole_top_queries{domain="www.netflix.com"} 305.0
pihole_top_queries{domain="c0.rbxcdn.com"} 300.0
pihole_top_queries{domain="ipv6.msftconnecttest.com"} 298.0
pihole_top_queries{domain="web.diagnostic.networking.aws.dev"} 289.0
pihole_top_queries{domain="mmechocaptiveportal.com"} 288.0
pihole_top_queries{domain="i.ytimg.com"} 286.0
pihole_top_queries{domain="presence.roblox.com"} 285.0
pihole_top_queries{domain="assetdelivery.roblox.com"} 279.0
pihole_top_queries{domain="friends.roblox.com"} 267.0
pihole_top_queries{domain="accounts.google.com"} 260.0
pihole_top_queries{domain="games.roblox.com"} 258.0
pihole_top_queries{domain="outlook.office.com"} 247.0
pihole_top_queries{domain="collector.azure.eaglex.ic.gov"} 243.0
pihole_top_queries{domain="collector.azure.microsoft.scloud"} 243.0
pihole_top_queries{domain="settings-win.data.microsoft.com"} 239.0
pihole_top_queries{domain="contile.services.mozilla.com"} 233.0
pihole_top_queries{domain="ctldl.windowsupdate.com"} 228.0
pihole_top_queries{domain="clients2.google.com"} 221.0
pihole_top_queries{domain="sync-v2.brave.com"} 220.0
pihole_top_queries{domain="clientservices.googleapis.com"} 220.0
pihole_top_queries{domain="account-public-service-prod.ol.epicgames.com"} 215.0
pihole_top_queries{domain="update.googleapis.com"} 212.0
pihole_top_queries{domain="www.mangago.me"} 203.0
pihole_top_queries{domain="fcm.googleapis.com"} 194.0
pihole_top_queries{domain="www.gstatic.com"} 180.0
pihole_top_queries{domain="www.googleapis.com"} 173.0
pihole_top_queries{domain="www.bing.com"} 173.0
pihole_top_queries{domain="vod-ftc-ap-south-1.media.dssott.com"} 170.0
pihole_top_queries{domain="edgeservices.bing.com"} 154.0
pihole_top_queries{domain="vod-akc-ap-south-1.media.dssott.com"} 154.0
pihole_top_queries{domain="fonts.gstatic.com"} 151.0
pihole_top_queries{domain="login.live.com"} 150.0
pihole_top_queries{domain="economy.roblox.com"} 149.0
pihole_top_queries{domain="ecsv2.roblox.com"} 140.0
pihole_top_queries{domain="android.googleapis.com"} 139.0
pihole_top_queries{domain="iweb13.mangapicgallery.com"} 137.0
pihole_top_queries{domain="youtubei.googleapis.com"} 135.0
pihole_top_queries{domain="launcher-public-service-prod06.ol.epicgames.com"} 134.0
pihole_top_queries{domain="i5.mangapicgallery.com"} 129.0
pihole_top_queries{domain="yt3.ggpht.com"} 128.0
pihole_top_queries{domain="i3.mangapicgallery.com"} 125.0
pihole_top_queries{domain="copilot.microsoft.com"} 124.0
pihole_top_queries{domain="i4.mangapicgallery.com"} 124.0
pihole_top_queries{domain="www.roblox.com"} 123.0
pihole_top_queries{domain="ooc-g2.tm-4.office.com"} 122.0
pihole_top_queries{domain="push.prod.netflix.com"} 117.0
pihole_top_queries{domain="library-service.live.use1a.on.epicgames.com"} 117.0
pihole_top_queries{domain="syd-efz.ms-acdc.office.com"} 117.0
pihole_top_queries{domain="accountsettings.roblox.com"} 116.0
pihole_top_queries{domain="i6.mangapicgallery.com"} 116.0
pihole_top_queries{domain="service-aggregation-layer-subs.juno.ea.com"} 116.0
pihole_top_queries{domain="i1.mangapicgallery.com"} 115.0
pihole_top_queries{domain="www.linkedin.com"} 114.0
# HELP pihole_top_ads pihole top ads
# TYPE pihole_top_ads gauge
pihole_top_ads{domain="optimizationguide-pa.googleapis.com"} 16199.0
pihole_top_ads{domain="teams.events.data.microsoft.com"} 14424.0
pihole_top_ads{domain="clienttoken.spotify.com"} 6100.0
pihole_top_ads{domain="s-0005-office.config.skype.com"} 3438.0
pihole_top_ads{domain="login5.spotify.com"} 3353.0
pihole_top_ads{domain="s-0005-teams.config.skype.com"} 2647.0
pihole_top_ads{domain="config.edge.skype.com"} 2520.0
pihole_top_ads{domain="mobile.events.data.microsoft.com"} 2469.0
pihole_top_ads{domain="self.events.data.microsoft.com"} 1503.0
pihole_top_ads{domain="config.teams.microsoft.com"} 1430.0
pihole_top_ads{domain="ecsv2.roblox.com"} 1310.0
pihole_top_ads{domain="diag.meethue.com"} 1231.0
pihole_top_ads{domain="ecs.office.com"} 1108.0
pihole_top_ads{domain="go.trouter.skype.com"} 1064.0
pihole_top_ads{domain="dpmupdates.indilogic.com"} 918.0
pihole_top_ads{domain="logs.netflix.com"} 588.0
pihole_top_ads{domain="ic3.events.data.microsoft.com"} 586.0
pihole_top_ads{domain="mira.config.skype.com"} 493.0
pihole_top_ads{domain="browser.events.data.microsoft.com"} 475.0
pihole_top_ads{domain="firebaseinstallations.googleapis.com"} 435.0
pihole_top_ads{domain="device-metrics-us-2.amazon.com"} 431.0
pihole_top_ads{domain="device-metrics-us.amazon.com"} 416.0
pihole_top_ads{domain="sdk.iad-03.braze.com"} 389.0
pihole_top_ads{domain="client-telemetry.roblox.com"} 358.0
pihole_top_ads{domain="prod-mediate-events.applovin.com"} 348.0
pihole_top_ads{domain="spclient.wg.spotify.com"} 298.0
pihole_top_ads{domain="beacons.gvt2.com"} 294.0
pihole_top_ads{domain="beacons.gcp.gvt2.com"} 292.0
pihole_top_ads{domain="beacons2.gvt2.com"} 263.0
pihole_top_ads{domain="beacons3.gvt2.com"} 262.0
pihole_top_ads{domain="beacons4.gvt2.com"} 250.0
pihole_top_ads{domain="beacons5.gvt3.com"} 241.0
pihole_top_ads{domain="us-teams.events.data.microsoft.com"} 235.0
pihole_top_ads{domain="beacons5.gvt2.com"} 234.0
pihole_top_ads{domain="userlocation.googleapis.com"} 226.0
pihole_top_ads{domain="w.sharethis.com"} 174.0
pihole_top_ads{domain="api-apac.bidmachine.io"} 158.0
pihole_top_ads{domain="v10.events.data.microsoft.com"} 145.0
pihole_top_ads{domain="apresolve.spotify.com"} 139.0
pihole_top_ads{domain="sfepodownload.mediatek.com"} 138.0
pihole_top_ads{domain="googleads.g.doubleclick.net"} 129.0
pihole_top_ads{domain="m365cdn.nel.measure.office.net"} 121.0
pihole_top_ads{domain="footprints-pa.googleapis.com"} 102.0
pihole_top_ads{domain="ade.googlesyndication.com"} 99.0
pihole_top_ads{domain="pin-river.data.ea.com"} 98.0
pihole_top_ads{domain="api.gameanalytics.com"} 87.0
pihole_top_ads{domain="sdk.split.io"} 87.0
pihole_top_ads{domain="1.viki.io"} 87.0
pihole_top_ads{domain="pagead2.googlesyndication.com"} 86.0
pihole_top_ads{domain="ms.applovin.com"} 83.0
pihole_top_ads{domain="www.googletagmanager.com"} 81.0
pihole_top_ads{domain="dealer.spotify.com"} 81.0
pihole_top_ads{domain="app-measurement.com"} 79.0
pihole_top_ads{domain="ms.applvn.com"} 79.0
pihole_top_ads{domain="pubads.g.doubleclick.net"} 74.0
pihole_top_ads{domain="locale.roblox.com"} 71.0
pihole_top_ads{domain="s.amazon-adsystem.com"} 71.0
pihole_top_ads{domain="mads.amazon-adsystem.com"} 71.0
pihole_top_ads{domain="c.amazon-adsystem.com"} 71.0
pihole_top_ads{domain="aax.amazon-adsystem.com"} 70.0
pihole_top_ads{domain="api.mixpanel.com"} 70.0
pihole_top_ads{domain="prod.ads.prod.webservices.mozgcp.net"} 68.0
pihole_top_ads{domain="firebase-settings.crashlytics.com"} 66.0
pihole_top_ads{domain="analytics.plex.tv"} 63.0
pihole_top_ads{domain="ad.doubleclick.net"} 62.0
pihole_top_ads{domain="tpc.googlesyndication.com"} 58.0
pihole_top_ads{domain="watson.events.data.microsoft.com"} 53.0
pihole_top_ads{domain="graph.facebook.com"} 52.0
pihole_top_ads{domain="api-partner.spotify.com"} 51.0
pihole_top_ads{domain="api.statsig.com"} 51.0
pihole_top_ads{domain="exo.nel.measure.office.net"} 49.0
pihole_top_ads{domain="ap.spotify.com"} 47.0
pihole_top_ads{domain="events.gfe.nvidia.com"} 45.0
pihole_top_ads{domain="telemetry.sdk.inmobi.com"} 45.0
pihole_top_ads{domain="a.nel.cloudflare.com"} 44.0
pihole_top_ads{domain="in.appcenter.ms"} 43.0
pihole_top_ads{domain="metrics.roblox.com"} 43.0
pihole_top_ads{domain="telemetry.gfe.nvidia.com"} 38.0
pihole_top_ads{domain="mobile-ap.spotify.com"} 38.0
pihole_top_ads{domain="api.flightproxy.skype.com"} 38.0
pihole_top_ads{domain="firebaselogging.googleapis.com"} 25.0
pihole_top_ads{domain="api.bidmachine.io"} 25.0
pihole_top_ads{domain="x.everestop.io"} 25.0
pihole_top_ads{domain="x.blueduckredapple.com"} 25.0
pihole_top_ads{domain="x.thecatmachine.com"} 25.0
pihole_top_ads{domain="mas-sdk.amazon.com"} 24.0
pihole_top_ads{domain="api.smoot.apple.com"} 23.0
pihole_top_ads{domain="graph.instagram.com"} 22.0
pihole_top_ads{domain="statsigapi.net"} 22.0
pihole_top_ads{domain="js-agent.newrelic.com"} 22.0
pihole_top_ads{domain="s.go-mpulse.net"} 20.0
pihole_top_ads{domain="gae2-dealer.spotify.com"} 17.0
pihole_top_ads{domain="as-api.asm.skype.com"} 16.0
pihole_top_ads{domain="s.youtube.com"} 14.0
pihole_top_ads{domain="api16-access-sg.pangle.io"} 14.0
pihole_top_ads{domain="cdp.cloud.unity3d.com"} 14.0
pihole_top_ads{domain="config.inmobi.com"} 14.0
pihole_top_ads{domain="ads.viralize.tv"} 14.0
pihole_top_ads{domain="stat.tiara.kakao.com"} 13.0
pihole_top_ads{domain="geller-pa.googleapis.com"} 13.0
# HELP pihole_forward_destinations pihole forward destinations
# TYPE pihole_forward_destinations gauge
pihole_forward_destinations{resolver="blocked|blocked"} 46.6
pihole_forward_destinations{resolver="cached|cached"} 22.83
pihole_forward_destinations{resolver="other|other"} 0.4
pihole_forward_destinations{resolver="rdns2.ihug.net#53|203.118.191.1#53"} 15.39
pihole_forward_destinations{resolver="rdns1.ihug.net#53|203.109.191.1#53"} 9.15
pihole_forward_destinations{resolver="one.one.one.one#53|1.1.1.1#53"} 2.99
pihole_forward_destinations{resolver="one.one.one.one#53|1.0.0.1#53"} 1.3
pihole_forward_destinations{resolver="dns.google#53|8.8.8.8#53"} 0.68
pihole_forward_destinations{resolver="dns.google#53|8.8.4.4#53"} 0.68
# HELP pihole_query_type pihole query type
# TYPE pihole_query_type gauge
pihole_query_type{query_type="A (IPv4)"} 58.46
pihole_query_type{query_type="AAAA (IPv6)"} 29.12
pihole_query_type{query_type="ANY"} 0.0
pihole_query_type{query_type="SRV"} 0.0
pihole_query_type{query_type="SOA"} 0.0
pihole_query_type{query_type="PTR"} 0.65
pihole_query_type{query_type="TXT"} 0.0
pihole_query_type{query_type="NAPTR"} 0.0
pihole_query_type{query_type="MX"} 0.0
pihole_query_type{query_type="DS"} 0.0
pihole_query_type{query_type="RRSIG"} 0.0
pihole_query_type{query_type="DNSKEY"} 0.0
pihole_query_type{query_type="NS"} 0.0
pihole_query_type{query_type="OTHER"} 0.0
pihole_query_type{query_type="SVCB"} 0.05
pihole_query_type{query_type="HTTPS"} 11.73
# HELP pihole_client_queries pihole client queries
# TYPE pihole_client_queries gauge
# HELP pihole_domains_being_blocked pihole domains being blocked
# TYPE pihole_domains_being_blocked gauge
pihole_domains_being_blocked 377346.0
# HELP pihole_dns_queries_today pihole dns queries today
# TYPE pihole_dns_queries_today gauge
pihole_dns_queries_today 134531.0
# HELP pihole_ads_blocked_today pihole ads blocked today
# TYPE pihole_ads_blocked_today gauge
pihole_ads_blocked_today 64665.0
# HELP pihole_ads_percentage_today pihole ads percentage today
# TYPE pihole_ads_percentage_today gauge
pihole_ads_percentage_today 48.06699
# HELP pihole_unique_domains pihole unique domains
# TYPE pihole_unique_domains gauge
pihole_unique_domains 7664.0
# HELP pihole_queries_forwarded pihole queries forwarded
# TYPE pihole_queries_forwarded gauge
pihole_queries_forwarded 37655.0
# HELP pihole_queries_cached pihole queries cached
# TYPE pihole_queries_cached gauge
pihole_queries_cached 31672.0
# HELP pihole_clients_ever_seen pihole clients ever seen
# TYPE pihole_clients_ever_seen gauge
pihole_clients_ever_seen 48.0
# HELP pihole_unique_clients pihole unique clients
# TYPE pihole_unique_clients gauge
pihole_unique_clients 42.0
# HELP pihole_dns_queries_all_types pihole dns queries all types
# TYPE pihole_dns_queries_all_types gauge
pihole_dns_queries_all_types 134531.0
# HELP pihole_reply_unknown pihole reply UNKNOWN
# TYPE pihole_reply_unknown gauge
pihole_reply_unknown 1104.0
# HELP pihole_reply_nodata pihole reply NODATA
# TYPE pihole_reply_nodata gauge
pihole_reply_nodata 11834.0
# HELP pihole_reply_nxdomain pihole reply NXDOMAIN
# TYPE pihole_reply_nxdomain gauge
pihole_reply_nxdomain 14764.0
# HELP pihole_reply_cname pihole reply CNAME
# TYPE pihole_reply_cname gauge
pihole_reply_cname 35430.0
# HELP pihole_reply_ip pihole reply IP
# TYPE pihole_reply_ip gauge
pihole_reply_ip 69767.0
# HELP pihole_reply_domain pihole reply DOMAIN
# TYPE pihole_reply_domain gauge
pihole_reply_domain 499.0
# HELP pihole_reply_rrname pihole reply RRNAME
# TYPE pihole_reply_rrname gauge
pihole_reply_rrname 0.0
# HELP pihole_reply_servfail pihole reply SERVFAIL
# TYPE pihole_reply_servfail gauge
pihole_reply_servfail 22.0
# HELP pihole_reply_refused pihole reply REFUSED
# TYPE pihole_reply_refused gauge
pihole_reply_refused 0.0
# HELP pihole_reply_notimp pihole reply NOTIMP
# TYPE pihole_reply_notimp gauge
pihole_reply_notimp 0.0
# HELP pihole_reply_other pihole reply OTHER
# TYPE pihole_reply_other gauge
pihole_reply_other 0.0
# HELP pihole_reply_dnssec pihole reply DNSSEC
# TYPE pihole_reply_dnssec gauge
pihole_reply_dnssec 0.0
# HELP pihole_reply_none pihole reply NONE
# TYPE pihole_reply_none gauge
pihole_reply_none 0.0
# HELP pihole_reply_blob pihole reply BLOB
# TYPE pihole_reply_blob gauge
pihole_reply_blob 1111.0
# HELP pihole_dns_queries_all_replies pihole dns queries all replies
# TYPE pihole_dns_queries_all_replies gauge
pihole_dns_queries_all_replies 134531.0
# HELP pihole_privacy_level pihole privacy level
# TYPE pihole_privacy_level gauge
pihole_privacy_level 0.0
# HELP pihole_status pihole status
# TYPE pihole_status gauge
pihole_status 1.0
# HELP pihole_gravity_last_updated pihole gravity last updated
# TYPE pihole_gravity_last_updated gauge
pihole_gravity_last_updated 1.717257283e+09
    
"""