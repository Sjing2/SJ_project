import scrapy


class KonlpyTcSpider(scrapy.Spider):
    name = 'konlpy_tc'
    allowed_domains = ['example.com']
    start_urls = ['http://example.com/']

    def parse(self, response):
        pass
