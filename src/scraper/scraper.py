"""Scraper genérico y respetuoso para portales inmobiliarios.

Este módulo NO apunta a ningún portal concreto: cada portal cambia su HTML
con frecuencia y tiene sus propios términos de servicio. Antes de usarlo:

1. Lee robots.txt y los Términos de Servicio del portal elegido.
2. Rellena `parse_listing_html()` con los selectores CSS/XPath reales del portal.
3. Ajusta `request_delay_seconds` en config/settings.yaml a un valor respetuoso.

Incluye por defecto: rate limiting, User-Agent identificable y verificación
de robots.txt antes de cada descarga.
"""
from __future__ import annotations

import time
import urllib.robotparser
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


@dataclass
class Listing:
    fecha_publicacion: str | None
    precio: float | None
    superficie_m2: float | None
    habitaciones: int | None
    banos: int | None
    ciudad: str | None
    zona: str | None
    direccion: str | None
    tipo_inmueble: str | None
    url: str


class RespectfulScraper:
    """Cliente HTTP que respeta robots.txt y aplica rate limiting."""

    def __init__(self, base_url: str, user_agent: str, request_delay_seconds: float = 3.0,
                 respect_robots_txt: bool = True):
        self.base_url = base_url
        self.user_agent = user_agent
        self.request_delay_seconds = request_delay_seconds
        self.respect_robots_txt = respect_robots_txt
        self._robot_parser = self._load_robots_txt() if respect_robots_txt else None
        self._last_request_ts = 0.0

    def _load_robots_txt(self) -> urllib.robotparser.RobotFileParser:
        parsed = urlparse(self.base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp

    def _can_fetch(self, url: str) -> bool:
        if not self.respect_robots_txt or self._robot_parser is None:
            return True
        return self._robot_parser.can_fetch(self.user_agent, url)

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_ts
        wait = self.request_delay_seconds - elapsed
        if wait > 0:
            time.sleep(wait)
        self._last_request_ts = time.monotonic()

    def get(self, url: str) -> requests.Response | None:
        if not self._can_fetch(url):
            print(f"[scraper] Bloqueado por robots.txt, se omite: {url}")
            return None
        self._throttle()
        headers = {"User-Agent": self.user_agent}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response


def parse_listing_html(html: str, source_url: str) -> Listing:
    """Extrae los campos de un anuncio a partir de su HTML.

    IMPORTANTE: los selectores CSS de abajo son marcadores de posición.
    Debes inspeccionar el HTML real del portal elegido (con las herramientas
    de desarrollador del navegador) y sustituirlos por los correctos.
    """
    soup = BeautifulSoup(html, "lxml")

    def text_or_none(selector: str) -> str | None:
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else None

    return Listing(
        fecha_publicacion=text_or_none(".fecha-publicacion"),
        precio=_to_float(text_or_none(".precio")),
        superficie_m2=_to_float(text_or_none(".superficie")),
        habitaciones=_to_int(text_or_none(".habitaciones")),
        banos=_to_int(text_or_none(".banos")),
        ciudad=text_or_none(".ciudad"),
        zona=text_or_none(".zona"),
        direccion=text_or_none(".direccion"),
        tipo_inmueble=text_or_none(".tipo-inmueble"),
        url=source_url,
    )


def _to_float(value: str | None) -> float | None:
    if not value:
        return None
    cleaned = value.replace(".", "").replace(",", ".").replace("€", "").replace("m²", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def _to_int(value: str | None) -> int | None:
    if not value:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    return int(digits) if digits else None
