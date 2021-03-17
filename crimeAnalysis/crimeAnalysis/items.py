# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Field, Item


class CrimeanalysisItem(Item):

    date = Field()
    time = Field()
    location = Field()
    latLong = Field()
    title = Field()
    source = Field()
    crimeType = Field()