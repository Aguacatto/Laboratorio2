import re

import requests
from bs4 import BeautifulSoup

URL = "https://books.toscrape.com/"

# La calificacion viene como clase CSS en ingles: <p class="star-rating Three">
CALIFICACIONES = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def extraer_titulo(libro):
    enlace = libro.select_one("h3 a")
    if enlace is None:
        return None
    # El texto visible puede venir truncado ("A Light in the ..."); el atributo
    # title contiene el titulo completo.
    titulo = enlace.get("title") or enlace.get_text()
    titulo = titulo.strip()
    return titulo or None


def extraer_precio(libro):
    etiqueta = libro.select_one("p.price_color")
    if etiqueta is None:
        return None
    # Se conservan solo digitos y punto para evitar problemas con el simbolo de
    # la moneda (por ejemplo "£51.77" o "Â£51.77" segun la codificacion).
    coincidencia = re.search(r"\d+(?:\.\d+)?", etiqueta.get_text())
    if coincidencia is None:
        return None
    return float(coincidencia.group())


def extraer_disponibilidad(libro):
    etiqueta = libro.select_one("p.availability")
    if etiqueta is None:
        return None
    texto = " ".join(etiqueta.get_text().split())
    return texto or None


def extraer_calificacion(libro):
    etiqueta = libro.select_one("p.star-rating")
    if etiqueta is None:
        return None
    for clase in etiqueta.get("class", []):
        if clase in CALIFICACIONES:
            return CALIFICACIONES[clase]
    return None


def obtener_libros():
    """Descarga la primera pagina del catalogo y retorna una lista de diccionarios."""
    respuesta = requests.get(URL, timeout=10)
    respuesta.raise_for_status()
    print(f"Codigo de respuesta: {respuesta.status_code}")
    # El servidor no declara charset; se fuerza UTF-8 para leer bien el HTML.
    respuesta.encoding = "utf-8"

    soup = BeautifulSoup(respuesta.text, "html.parser")
    articulos = soup.select("article.product_pod")

    libros = []
    for posicion, libro in enumerate(articulos, start=1):
        # Si un elemento no existe, su campo queda como None y se continua con
        # el resto del catalogo en lugar de detener la ejecucion.
        try:
            registro = {
                "titulo": extraer_titulo(libro),
                "precio": extraer_precio(libro),
                "disponibilidad": extraer_disponibilidad(libro),
                "calificacion": extraer_calificacion(libro),
            }
        except Exception as error:
            print(f"Aviso: no se pudo procesar el libro {posicion}: {error}")
            continue

        faltantes = [campo for campo, valor in registro.items() if valor is None]
        if faltantes:
            print(f"Aviso: el libro {posicion} no tiene: {', '.join(faltantes)}")
        libros.append(registro)

    return libros


if __name__ == "__main__":
    libros = obtener_libros()
    print(f"Total de libros extraidos: {len(libros)}")
    print("Primeros cinco registros:")
    for registro in libros[:5]:
        print(registro)
