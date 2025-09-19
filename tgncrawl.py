import scrapy
from urllib.parse import urljoin, urlparse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.pipelines.files import FilesPipeline


class PdfItem(scrapy.Item):
    file_urls = scrapy.Field()
    files = scrapy.Field()


class PreservePathFilesPipeline(FilesPipeline):
    """Guarda el PDF preservando la ruta de la URL."""
    def file_path(self, request, response=None, info=None, *, item=None):
        path = urlparse(request.url).path.lstrip("/").replace("..", "")
        return path or "archivo.pdf"


class TgnPdfSpider(CrawlSpider):
    name = "tgn"
    allowed_domains = ["tgn.com.ar", "www.tgn.com.ar"]
    start_urls = ["https://www.tgn.com.ar/"]

    # 👇 usar el nombre real del módulo, no '__main__'
    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "USER_AGENT": "Scrapy - TGN PDF crawler (contacto: tu@email)",
        "ITEM_PIPELINES": {f"{__name__}.PreservePathFilesPipeline": 1},
        "FILES_STORE": "downloads",
        "MEDIA_ALLOW_REDIRECTS": True,
        "CONCURRENT_REQUESTS": 8,
        "DOWNLOAD_DELAY": 0.25,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 0.5,
        "AUTOTHROTTLE_MAX_DELAY": 5,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 2.0,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 2,
        "DEPTH_LIMIT": 0,
        "HTTPCACHE_ENABLED": True,
        "HTTPCACHE_DIR": ".httpcache_tgn",
        "FILES_EXPIRES": 3650,
    }

    rules = (
        Rule(
            LinkExtractor(
                allow_domains=("tgn.com.ar", "www.tgn.com.ar"),
                unique=True,
            ),
            callback="parse_page",
            follow=True,
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_pdf_urls = set()

    def parse_page(self, response):
        # PDF directo por Content-Type
        ctype = response.headers.get(b"Content-Type", b"").decode("latin1").lower()
        if "application/pdf" in ctype:
            pdf_url = response.url
            if self._mark_seen(pdf_url):
                yield PdfItem(file_urls=[pdf_url])
            return

        # Enlaces que terminan en .pdf
        pdf_extractor = LinkExtractor(
            allow=r"\.pdf(\?.*)?$",
            allow_domains=("tgn.com.ar", "www.tgn.com.ar"),
            unique=True,
        )
        for link in pdf_extractor.extract_links(response):
            if self._mark_seen(link.url):
                yield PdfItem(file_urls=[link.url])

        # Fallback con selectores
        for href in response.css("a::attr(href)").getall():
            if not href:
                continue
            abs_url = urljoin(response.url, href)
            if not self._is_internal(abs_url):
                continue
            if abs_url.lower().endswith(".pdf") and self._mark_seen(abs_url):
                yield PdfItem(file_urls=[abs_url])

    def _is_internal(self, url: str) -> bool:
        return urlparse(url).netloc.lower().endswith("tgn.com.ar")

    def _mark_seen(self, url: str) -> bool:
        if url in self.seen_pdf_urls:
            return False
        self.seen_pdf_urls.add(url)
        return True
