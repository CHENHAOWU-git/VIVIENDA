"""Cliente para la API oficial de Idealista (developers.idealista.com).

Vía de acceso recomendada frente al scraping de HTML: es la forma que
Idealista autoriza explícitamente para obtener datos de anuncios.

Pasos previos:
1. Solicita acceso en https://developers.idealista.com/access-request
   (piden nombre, email y una breve descripción del proyecto).
2. Te envían `apikey` y `secret`. Guárdalos como variables de entorno,
   NUNCA los subas al repo:
       $env:IDEALISTA_API_KEY = "..."
       $env:IDEALISTA_API_SECRET = "..."
3. El plan gratuito tiene una cuota mensual de peticiones muy limitada
   (históricamente unos pocos cientos de búsquedas/mes) — revisa tu cuota
   actual en el panel de desarrollador antes de diseñar el pipeline.
"""
from __future__ import annotations

import base64
import os
import time

import requests

TOKEN_URL = "https://api.idealista.com/oauth/token"
SEARCH_URL = "https://api.idealista.com/3.5/{country}/search"


class IdealistaAPIError(RuntimeError):
    pass


class IdealistaClient:
    def __init__(self, api_key: str | None = None, secret: str | None = None):
        self.api_key = api_key or os.environ.get("IDEALISTA_API_KEY")
        self.secret = secret or os.environ.get("IDEALISTA_API_SECRET")
        if not self.api_key or not self.secret:
            raise IdealistaAPIError(
                "Faltan credenciales. Define IDEALISTA_API_KEY e IDEALISTA_API_SECRET "
                "como variables de entorno (ver docstring del módulo)."
            )
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    def _get_token(self) -> str:
        if self._token and time.monotonic() < self._token_expires_at:
            return self._token

        credentials = base64.b64encode(f"{self.api_key}:{self.secret}".encode()).decode()
        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        response = requests.post(TOKEN_URL, headers=headers, data={"grant_type": "client_credentials", "scope": "read"})
        response.raise_for_status()
        payload = response.json()
        self._token = payload["access_token"]
        self._token_expires_at = time.monotonic() + payload.get("expires_in", 3600) - 60
        return self._token

    def search(self, country: str = "es", operation: str = "sale", property_type: str = "homes",
               center: str | None = None, distance: int | None = None, location_id: str | None = None,
               max_items: int = 50, num_page: int = 1, extra_params: dict | None = None) -> dict:
        """Busca anuncios. Debes indicar `center` ("lat,lon") + `distance` (metros)
        o `location_id` (código de ubicación de Idealista) para acotar la zona.
        """
        token = self._get_token()
        params = {
            "operation": operation,
            "propertyType": property_type,
            "maxItems": max_items,
            "numPage": num_page,
        }
        if center:
            params["center"] = center
        if distance:
            params["distance"] = distance
        if location_id:
            params["locationId"] = location_id
        if extra_params:
            params.update(extra_params)

        response = requests.post(
            SEARCH_URL.format(country=country),
            headers={"Authorization": f"Bearer {token}"},
            params=params,
        )
        response.raise_for_status()
        return response.json()


def listing_to_row(item: dict) -> dict:
    """Convierte un elemento de `elementList` de la respuesta de búsqueda al
    esquema de columnas usado en el resto del proyecto (ver
    config/settings.yaml -> columnas_esperadas)."""
    return {
        "fecha_publicacion": None,  # la API no siempre expone la fecha; anota la fecha de extracción si la necesitas
        "precio": item.get("price"),
        "superficie_m2": item.get("size"),
        "habitaciones": item.get("rooms"),
        "banos": item.get("bathrooms"),
        "ciudad": item.get("municipality"),
        "zona": item.get("district") or item.get("neighborhood"),
        "direccion": item.get("address"),
        "tipo_inmueble": item.get("propertyType"),
        "url": item.get("url"),
    }
