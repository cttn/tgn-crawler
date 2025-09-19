# TGN PDF Spider

Este proyecto contiene un spider en **Python + Scrapy** que recorre todo el sitio web de [TGN (Transportadora de Gas del Norte)](https://www.tgn.com.ar) y descarga automáticamente todos los documentos **PDF** encontrados.

Los PDFs se guardan en una carpeta local (`downloads/` por defecto) respetando la misma estructura de rutas que tienen en el sitio.  

**Ejemplo:**

```
https://www.tgn.com.ar/assets/media/2025/03/2025-03-06-Hecho-Relevante.pdf
↓
downloads/assets/media/2025/03/2025-03-06-Hecho-Relevante.pdf
```

---

## ⚙️ Requisitos

- Python 3.9 o superior  
- [Scrapy](https://scrapy.org/)

Instalación recomendada en un entorno virtual:

```bash
python -m venv venv
source venv/bin/activate
pip install scrapy
```

---

## ▶️ Uso

Ejecutar el spider en la carpeta donde guardaste `tgn_pdf_spider.py`:

```bash
scrapy runspider tgn_pdf_spider.py -L INFO
```

Esto descargará todos los PDFs encontrados en `downloads/`.

### Personalizar carpeta de descargas

Podés cambiar el destino usando el parámetro `FILES_STORE`:

```bash
scrapy runspider tgn_pdf_spider.py -s FILES_STORE=/ruta/a/descargas -L INFO
```

---

## 🛠️ Configuración interna

El spider incluye ajustes personalizados:

- `ROBOTSTXT_OBEY = True` → respeta `robots.txt`.  
- `FILES_STORE = downloads` → carpeta por defecto de descargas.  
- `AUTOTHROTTLE` activado → evita sobrecargar el sitio.  
- `DEPTH_LIMIT = 0` → sin límite de profundidad (se recorre todo el sitio).  
- Evita duplicados: cada PDF se descarga una sola vez.  

---

## 📂 Estructura del repo

```
.
├── tgn_pdf_spider.py   # Spider principal
├── README.md           # Este archivo
└── downloads/          # Carpeta de salida (se crea al correr el spider)
```

---

## ✅ Notas

- El spider se limita al dominio `tgn.com.ar` y `www.tgn.com.ar`.  
- Sólo descarga PDFs (detectados por URL o Content-Type).  
- Es posible limitarlo a ciertas secciones o patrones editando la clase `TgnPdfSpider`.  
- Se incluye un `httpcache` local para evitar recrawlear innecesariamente en ejecuciones sucesivas.  

---

## 📜 Licencia

Este código se comparte bajo licencia MIT.  
Podés usarlo, modificarlo y distribuirlo libremente, siempre citando la fuente.
