import os, sys, scrapy, geocoder, json
from multiprocessing import Process, Queue
from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor

#from crimeAnalysis.items import CrimeanalysisItem

class crimeSpider(scrapy.Spider):

    name = "crimes"
    start_urls = ["https://www.berlin.de/polizei/polizeimeldungen/"]

    crimeTypes = {
        'Mord': ['Mord','Tötung','Tötungsdelikt','Totschlag','ums Leben gekommen','tot','getötet','verstorben'],
        'Körperverletzung': ['Körperverletzung','Schwerverletzter','Schwerverletzte','Schwerverletztem','Schwerverletzten','verletzt','schwer verletzt','Angriff','angegriffen','geschlagen'],
        'Betrug': ['Betrug'],
        'Raub': ['Raub','Raubüberfall','Diebstahl','Einbruch','Einbrecher','raubte','geraubt','ausgeraubt','Wohnungseinbruch'],
        'Brandstiftung': ['Brandstiftung','Brand','Hausbrand','Kellerbrand','angezündet','ausgebrannt','brannte','brannten'],
        'Geiselnahme': ['Geiselnahme'],
        'Vandalismus': ['Vandalismus','beschädigt','beschmiert'],
        'Nötigung': ['Nötigung','Freiheitsdelikt','Drohung','Zwang','Unterlassung'],
        'Vergewaltigung': ['Vergewaltigung','vergewaltigt'],
        'Unterschlagung': ['Unterschlagung'],
        'Geldfälschung': ['Geldfälschung','Falschgeld'],
        'Landesverrat': ['Landesverrat','Staatsgeheimnissen'],
        'Verschleppung': ['vermisst','Verschleppung',''],
        'Rassenangriff': ['Hakenkreuze','Nazisymbole','Hitlergruß','antisemitisch'],
        'Verkehrsunfall': ['Verkehrsunfall','Fahrzeug','Auto','Bus','Bahn','Fahrzeugfahrer','Fahrzeugfahrerin','E-Scooter','Unfall']
    }

    def __init__(self):
        self.name = 'crimes'

    def parse(self, response):

        reports = response.xpath("//li[@class='row-fluid']")

        crimeType = []

        for report in reports:

            title = report.xpath(".//div[@class='span10 cell text']/a/text()").get()
            location = report.xpath(".//span[@class='category']/text()").get()
            latLong = geocoder.mapbox(location, key='pk.eyJ1IjoiYXNha2FrdXNoZXYiLCJhIjoiY2tmd25uZW9uMDFobTJxcndkdGNkYmwyZSJ9.Lm3qs2XtCG34WVXNOhWHgw')

            for word in title.split():

                for key in crimeSpider.crimeTypes:

                    if word in crimeSpider.crimeTypes[key]:

                        crimeType.append(key)

            if len(crimeType) == 0:
                crimeType = ['Keine Angabe']

            yield {
                'title': title,
                'location': location,
                'date': report.xpath(".//div[@class='span2 cell date']/text()").get().split()[0],
                'time': report.xpath(".//div[@class='span2 cell date']/text()").get().split()[1],
                'latLong': latLong.latlng,
                'crimeType': crimeType,
                'link': report.xpath(".//div[@class='span10 cell text']/a/@href").extract()
            }

            crimeType = []

    def run(self):

        if os.path.exists("{0}.json".format(self.name)):
            os.remove("{0}.json".format(self.name))

        def f(q):

            try:
                runner = CrawlerRunner(settings={'FEED_FORMAT' : 'json', 'FEED_URI' : "crimes.json"})
                deferred = runner.crawl(crimeSpider)
                deferred.addBoth(lambda _: reactor.stop())
                reactor.run()
                q.put(None)

            except Exception as e:
                q.put(e)

        q = Queue()
        p = Process(target=f, args=(q,))
        p.start()
        result = q.get()
        p.join()

        if result is not None:
            raise result