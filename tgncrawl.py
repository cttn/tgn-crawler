import os
from urllib.parse import urljoin, urlparse

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class PdfItem(scrapy.Item):
    file_urls = scrapy.Field()   # requerido por FilesPipeline
    files = scrapy.Field()


class PreservePathFilesPipeline(scrapy.pipelines.files.FilesPipeline):
    """
    Pipeline que preserva la ruta del PDF según la URL.
    """
    def file_path(self, request, response=None, info=None, *, item=None):
        # Ej: https://www.tgn.com.ar/assets/media/2025/03/file.pdf
        parsed = urlparse(request.url)
        path = parsed.path.lstrip("/")  # assets/media/2025/03/file.pdf
        # Evitar directorios traversal raros
        path = path.replace("..", "")
        return path


class TgnPdfSpider(CrawlSpider):
    name = "tgn"
    allowed_domains = ["tgn.com.ar", "www.tgn.com.ar"]
    start_urls = ["https://www.tgn.com.ar/"]

    # Ajustes locales al spider (no hace falta settings.py separado)
    custom_settings = {
        # Respeto de robots
        "ROBOTSTXT_OBEY": True,
        # User-Agent claro
        "USER_AGENT": "Scrapy - TGN PDF crawler (contacto: example@example.com)",
        # Pipeline para descargar archivos
        "ITEM_PIPELINES": {
            "__main__.PreservePathFilesPipeline": 1,
        },
        # Dónde guardar (podés override con -s FILES_STORE=...)
        "FILES_STORE": "downloads",
        # Seguir redirects de archivos
        "MEDIA_ALLOW_REDIRECTS": True,
        # Concurrencia conservadora
        "CONCURRENT_REQUESTS": 8,
        "DOWNLOAD_DELAY": 0.25,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 0.5,
        "AUTOTHROTTLE_MAX_DELAY": 5,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 2.0,
        # Reintentos básicos
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 2,
        # Profundidad sin límite (ajustá si querés acotar)
        "DEPTH_LIMIT": 0,
        # Permitir cache de disco para no repetir requests cuando relances
        "HTTPCACHE_ENABLED": True,
        "HTTPCACHE_DIR": ".httpcache_tgn",
        # Evitar guardar HTML enorme en disco (descargamos solo PDFs)
        # FilesPipeline sólo guarda los binarios solicitados por file_urls
    }

    # Seguir todos los enlaces internos
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
        # Para evitar emitir el mismo PDF muchas veces
        self.seen_pdf_urls = set()

    def parse_page(self, response):
        """
        Para cada página HTML:
        - si es un PDF devuelto directamente, lo descarga.
        - extrae enlaces que terminen en .pdf y crea items.
        """
        # 1) Si la respuesta ya es un PDF (Content-Type)
        ctype = response.headers.get("Content-Type", b"").decode("latin1").lower()
        if "application/pdf" in ctype:
            pdf_url = response.url
            if self._mark_seen(pdf_url):
                yield PdfItem(file_urls=[pdf_url])
            return  # nada más que hacer

        # 2) Si es HTML, extraigamos <a href="...pdf">
        # Usamos LinkExtractor específico para PDFs
        pdf_extractor = LinkExtractor(
            allow=r"\.pdf(\?.*)?$",
            allow_domains=("tgn.com.ar", "www.tgn.com.ar"),
            unique=True,
        )
        for link in pdf_extractor.extract_links(response):
            pdf_url = link.url
            if self._mark_seen(pdf_url):
                yield PdfItem(file_urls=[pdf_url])

        # 3) A veces hay PDFs con mayúsculas o sin .pdf en URL pero son PDFs.
        # Buscamos anchors manualmente y normalizamos.
        for href in response.css("a::attr(href)").getall():
            if not href:
                continue
            abs_url = urljoin(response.url, href)
            if not self._is_internal(abs_url):
                continue
            # Heurística por extensión
            if abs_url.lower().endswith(".pdf"):
                if self._mark_seen(abs_url):
                    yield PdfItem(file_urls=[abs_url])
            # Heurística adicional: rutas típicas de TGN para documentos
            elif "/assets/media/" in abs_url and any(abs_url.lower().endswith(ext) for ext in [".pdf", ".PDF"]):
                if self._mark_seen(abs_url):
                    yield PdfItem(file_urls=[abs_url])

    def _is_internal(self, url: str) -> bool:
        netloc = urlparse(url).netloc.lower()
        return netloc.endswith("tgn.com.ar")

    def _mark_seen(self, url: str) -> bool:
        if url in self.seen_pdf_urls:
            return False
        self.seen_pdf_urls.add(url)
        return True

