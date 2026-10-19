# Laboratorio 2: Web Scraping, procesamiento y recuperación de información

Extracción de la primera página del catálogo <https://books.toscrape.com/>, limpieza y estructuración con Pandas, y un buscador de títulos con TF-IDF y similitud del coseno.

## Integrantes

- Vicente Palma
- Diego Alvarado
- Lucas Pinto

## Repositorio

<https://github.com/Aguacatto/Laboratorio2>

## Estructura

```
laboratorio2/
├── scraper.py          # Parte I: extracción con requests + BeautifulSoup
├── procesamiento.py    # Parte II: DataFrame, limpieza y exportación a libros.csv
├── buscador.py         # Parte III: índice TF-IDF y búsqueda por similitud del coseno
├── libros.csv          # Datos procesados (generados por procesamiento.py)
├── requirements.txt    # Dependencias congeladas con pip freeze
├── README.md
└── .gitignore          # Excluye .venv/ (no se versiona)
```

---

## 0. Preparación del entorno virtual

Comandos ejecutados (Windows, PowerShell, Python 3.14.3):

```powershell
# Paso 0.1: crear el entorno virtual dentro de la carpeta del proyecto
py -m venv .venv

# Paso 0.2: activar el entorno (comando usado en este laboratorio)
.venv\Scripts\Activate.ps1

# Paso 0.3: verificar que el intérprete pertenece al entorno virtual
python -c "import sys; print(sys.executable)"
# -> C:\Users\lucas\Documents\GitHub\Laboratorio2\.venv\Scripts\python.exe

python -m pip install --upgrade pip
python -m pip install requests beautifulsoup4 pandas scikit-learn
python -m pip freeze > requirements.txt
```

Otras formas de activar el entorno:

| Terminal | Comando |
|---|---|
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows CMD | `.venv\Scripts\activate.bat` |
| Git Bash | `source .venv/Scripts/activate` |
| Linux / macOS | `source .venv/bin/activate` |

> En PowerShell 5.1 el operador `>` guarda en UTF-16. Para que `requirements.txt` quede en texto plano se generó con `python -m pip freeze | Out-File -Encoding ascii requirements.txt` (mismo contenido).

**Paso 0.4: `.gitignore`.** Contiene la línea `.venv/` (además de `__pycache__/` y `*.pyc`). Se comprobó con `git status --short --ignored` que Git no incluye el entorno:

```
?? .gitignore
?? requirements.txt
!! .venv/
```

## Reproducir la ejecución desde un entorno virtual nuevo (Paso 14)

```powershell
git clone https://github.com/Aguacatto/Laboratorio2.git
cd Laboratorio2
py -m venv .venv                      # Linux/macOS: python3 -m venv .venv
.venv\Scripts\Activate.ps1            # Linux/macOS: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Orden de ejecución

```powershell
python scraper.py         # 1. (opcional) prueba la extracción: total y primeros 5 registros
python procesamiento.py   # 2. hace el scraping, limpia los datos y genera libros.csv
python buscador.py        # 3. pide una consulta y muestra los libros más similares
```

`procesamiento.py` importa `obtener_libros()` desde `scraper.py`. El scraping de `scraper.py` está protegido por `if __name__ == "__main__":`, así que importar el módulo no vuelve a hacer la petición. `buscador.py` solo necesita `libros.csv`.

---

## I. Extracción mediante Web Scraping (`scraper.py`)

Se pide **solo la primera página** con `requests.get(URL, timeout=10)` y se comprueba el código con `raise_for_status()`. Luego se analiza el HTML con `BeautifulSoup(respuesta.text, "html.parser")`.

Selectores obtenidos inspeccionando el HTML con las herramientas del navegador:

| Campo | Selector / atributo | Transformación |
|---|---|---|
| Contenedor de cada libro | `article.product_pod` | |
| `titulo` | atributo `title` de `h3 a` (el texto visible viene truncado, por ejemplo "A Light in the ...") | `strip()` |
| `precio` | `p.price_color` (texto `£51.77`) | regex `\d+(?:\.\d+)?` y luego `float` |
| `disponibilidad` | `p.availability` | se juntan los espacios y saltos de línea: `In stock` |
| `calificacion` | segunda clase de `p.star-rating` (`One` … `Five`) | diccionario a entero de 1 a 5 |

Notas:

- El servidor no declara `charset`, por lo que `requests` decodificaba el `£` como `Â£`. Se fuerza `respuesta.encoding = "utf-8"` y, además, el precio se extrae con una expresión regular que ignora el símbolo de moneda.
- **Gestión de elementos sin datos (Paso 4).** Cada campo se extrae con una función propia que retorna `None` si la etiqueta o el valor no existe, en lugar de lanzar `AttributeError`. Si un libro tiene campos faltantes, se imprime `Aviso: el libro N no tiene: ...` y el registro se guarda igual (con `None`). Si un libro produce un error inesperado, se informa y se pasa al siguiente con `continue`. La ejecución nunca se detiene por un elemento incompleto. En la ejecución real no apareció ningún aviso: los 20 libros tenían los cuatro campos.

Salida de `python scraper.py`:

```
Codigo de respuesta: 200
Total de libros extraidos: 20
Primeros cinco registros:
{'titulo': 'A Light in the Attic', 'precio': 51.77, 'disponibilidad': 'In stock', 'calificacion': 3}
{'titulo': 'Tipping the Velvet', 'precio': 53.74, 'disponibilidad': 'In stock', 'calificacion': 1}
{'titulo': 'Soumission', 'precio': 50.1, 'disponibilidad': 'In stock', 'calificacion': 1}
{'titulo': 'Sharp Objects', 'precio': 47.82, 'disponibilidad': 'In stock', 'calificacion': 4}
{'titulo': 'Sapiens: A Brief History of Humankind', 'precio': 54.23, 'disponibilidad': 'In stock', 'calificacion': 5}
```

## II. Procesamiento y estructuración (`procesamiento.py`)

Se construye el DataFrame con `pd.DataFrame(libros)` y se verifica (Paso 5.4):

```
                                  titulo  precio disponibilidad  calificacion
0                   A Light in the Attic   51.77       In stock             3
1                     Tipping the Velvet   53.74       In stock             1
2                             Soumission   50.10       In stock             1
3                          Sharp Objects   47.82       In stock             4
4  Sapiens: A Brief History of Humankind   54.23       In stock             5
<class 'pandas.DataFrame'>
RangeIndex: 20 entries, 0 to 19
Data columns (total 4 columns):
 #   Column          Non-Null Count  Dtype
---  ------          --------------  -----
 0   titulo          20 non-null     str
 1   precio          20 non-null     float64
 2   disponibilidad  20 non-null     str
 3   calificacion    20 non-null     int64
dtypes: float64(1), int64(1), str(2)
memory usage: 772.0 bytes
None
(20, 4)
Columnas presentes: ['titulo', 'precio', 'disponibilidad', 'calificacion']
```

**Paso 6: limpieza.**

- Se retiran los espacios sobrantes de `titulo` (`str.strip()` y espacios internos repetidos) y de `disponibilidad`.
- Se eliminan duplicados por título con `drop_duplicates(subset="titulo")`. Resultado: `Duplicados eliminados: 0`.
- Se crea `titulo_normalizado` en minúsculas (`str.lower()`).
- Se verifican los tipos numéricos con `pd.to_numeric`: `precio` queda como `float64` y `calificacion` como `Int64`.

**Paso 7: indicadores y exportación.** Se exporta `libros.csv` con `index=False` y `encoding="utf-8"`. Columnas: `titulo, precio, disponibilidad, calificacion, titulo_normalizado`.

```
Cantidad de libros: 20
Precio promedio: 38.05
Archivo libros.csv exportado.
```

## III. Recuperación de información (`buscador.py`)

`buscador.py` contiene el código entregado en el Paso 10. Carga `libros.csv`, descarta los títulos vacíos y ajusta `TfidfVectorizer` sobre `titulo_normalizado`, lo que da una matriz de 20 títulos × 90 términos. Después calcula la similitud del coseno de la consulta contra cada título y muestra hasta `top_k` resultados con puntuación mayor que 0, de mayor a menor.

### Paso 11: dos consultas con palabras observadas en los títulos

**Consulta 1: `life`**

```
Ingrese una palabra o titulo: life
Scott Pilgrim's Precious Little Life (Scott Pilgrim #1) | Precio: 52.29 | Similitud: 0.2459
The Coming Woman: A Novel Based on the Life of the Infamous Feminist, Victoria Woodhull | Precio: 17.93 | Similitud: 0.2250
Our Band Could Be Your Life: Scenes from the American Indie Underground, 1981-1991 | Precio: 57.25 | Similitud: 0.2231
```

**Consulta 2: `the`**

```
Ingrese una palabra o titulo: the
The Coming Woman: A Novel Based on the Life of the Infamous Feminist, Victoria Woodhull | Precio: 17.93 | Similitud: 0.4181
The Boys in the Boat: Nine Americans and Their Epic Quest for Gold at the 1936 Berlin Olympics | Precio: 22.6 | Similitud: 0.3630
The Black Maria | Precio: 52.15 | Similitud: 0.3282
The Requiem Red | Precio: 22.65 | Similitud: 0.3282
Tipping the Velvet | Precio: 53.74 | Similitud: 0.3282
```

**Comparación del orden.**

- Con `life`, los 3 títulos que contienen la palabra la tienen una sola vez. Gana *Scott Pilgrim's...* porque tiene menos términos distintos (5, contra 12 y 14 de los otros), así que al normalizar el vector "life" pesa más. Los otros dos son títulos largos, con puntuaciones casi iguales (0.2250 y 0.2231).
- Con `the`, el término aparece en 10 de los 20 títulos y el límite `top_k=5` deja ver solo 5. El orden lo decide la frecuencia del término: *The Coming Woman...* y *The Boys in the Boat...* contienen "the" 3 veces cada uno. Gana el primero porque tiene menos palabras (14 contra 18), así que "the" pesa más en su vector. Los tres siguientes empatan en 0.3282: son títulos de 3 palabras y sus otras dos palabras aparecen una sola vez en la colección. Que una palabra vacía como "the" genere un ranking muestra que el buscador mide coincidencia de palabras, no relevancia real (ver Pregunta 6).

**Desafío: `buscar(consulta, top_k=3)`.** Se cambió temporalmente la línea `resultados = buscar(consulta)` por `resultados = buscar(consulta, top_k=3)` y se volvió a ejecutar:

```
Ingrese una palabra o titulo: the
The Coming Woman: A Novel Based on the Life of the Infamous Feminist, Victoria Woodhull | Precio: 17.93 | Similitud: 0.4181
The Boys in the Boat: Nine Americans and Their Epic Quest for Gold at the 1936 Berlin Olympics | Precio: 22.6 | Similitud: 0.3630
The Black Maria | Precio: 52.15 | Similitud: 0.3282
```

Con `the` (10 coincidencias posibles) devolvió exactamente 3 resultados, todos con similitud positiva. Con `life` (solo 3 coincidencias) devolvió los mismos 3 de antes. Se comprueba que el máximo es 3. Después se restauró la llamada original del Paso 10.

## IV. Validación: casos de prueba (Paso 12)

Cada prueba se ejecutó con el entorno virtual activo, corriendo `python buscador.py` y entregando la consulta por la entrada estándar (`printf '<consulta>\n' | python buscador.py` en Git Bash, equivalente a escribirla en el prompt). En los cuatro casos el proceso terminó con código de salida 0, sin excepciones.

| Caso | Consulta utilizada | Resultado observado | Estado |
|---|---|---|---|
| T1 | `life` | Se recuperaron 3 libros con similitud positiva, ordenados de mayor a menor: *Scott Pilgrim's Precious Little Life* (0.2459), *The Coming Woman...* (0.2250), *Our Band Could Be Your Life...* (0.2231). | Cumple |
| T2 | `zzxyz123` | Se mostró «No se encontraron coincidencias.» | Cumple |
| T3 | `LIFE` | Se obtuvo el mismo ranking que en T1: mismos 3 libros, mismo orden y mismas puntuaciones (0.2459, 0.2250, 0.2231). | Cumple |
| T4 | [vacía] | Se mostró «Ingrese una consulta no vacia.» seguido de «No se encontraron coincidencias.», sin excepción. | Cumple |

Salidas completas:

```
# T1
Ingrese una palabra o titulo: life
Scott Pilgrim's Precious Little Life (Scott Pilgrim #1) | Precio: 52.29 | Similitud: 0.2459
The Coming Woman: A Novel Based on the Life of the Infamous Feminist, Victoria Woodhull | Precio: 17.93 | Similitud: 0.2250
Our Band Could Be Your Life: Scenes from the American Indie Underground, 1981-1991 | Precio: 57.25 | Similitud: 0.2231

# T2
Ingrese una palabra o titulo: zzxyz123
No se encontraron coincidencias.

# T3
Ingrese una palabra o titulo: LIFE
Scott Pilgrim's Precious Little Life (Scott Pilgrim #1) | Precio: 52.29 | Similitud: 0.2459
The Coming Woman: A Novel Based on the Life of the Infamous Feminist, Victoria Woodhull | Precio: 17.93 | Similitud: 0.2250
Our Band Could Be Your Life: Scenes from the American Indie Underground, 1981-1991 | Precio: 57.25 | Similitud: 0.2231

# T4
Ingrese una palabra o titulo:
Ingrese una consulta no vacia.
No se encontraron coincidencias.
```

### Problemas detectados

1. **Mensaje redundante en T4.** `buscar()` imprime «Ingrese una consulta no vacia.» y retorna `[]`. Luego el bloque principal ve la lista vacía e imprime también «No se encontraron coincidencias.». No es un error (hay mensaje informativo y no hay excepción), pero el segundo mensaje sobra. Se corregiría revisando si la consulta está vacía en el bloque principal antes de llamar a `buscar()`.
2. **Empates en el ranking.** En la consulta `the`, tres títulos tienen exactamente 0.3282. El orden entre ellos lo decide `argsort()` y no responde a ningún criterio de relevancia.
3. **Entrada por tubería en PowerShell 5.1.** Al probar T4 con `"" | python buscador.py`, PowerShell antepone el carácter invisible BOM (`U+FEFF`). `str.strip()` no lo elimina, así que la consulta no se detectaba como vacía y solo se mostraba «No se encontraron coincidencias.». Escribiendo la consulta a mano en la terminal, o con `printf` en Git Bash, el comportamiento es el esperado (tabla anterior). El código no tiene la falla. Es un efecto de cómo PowerShell envía el texto, pero conviene saberlo al automatizar pruebas.

## Paso 13: evidencias

- **Cantidad de libros extraídos:** 20 (primera página, sin duplicados).
- **Precio promedio:** £38.05 (mínimo £13.99, máximo £57.25).
- **Ejemplo de búsqueda 1:** `life` → 3 resultados (ver T1).
- **Ejemplo de búsqueda 2:** `scott pilgrim`

```
Ingrese una palabra o titulo: scott pilgrim
Scott Pilgrim's Precious Little Life (Scott Pilgrim #1) | Precio: 52.29 | Similitud: 0.8770
```

Con dos términos que solo aparecen en ese título, y "scott" y "pilgrim" repetidos dos veces en él, la similitud sube a 0.8770. Una sola palabra común como `life` llega apenas a 0.2459.

---

## Respuestas

### Pregunta 1: ¿Para qué sirve BeautifulSoup y cómo se diferencia de requests?

`requests` es un cliente HTTP. Hace la petición al servidor (GET), maneja el `timeout`, los encabezados y el código de estado, y entrega el contenido como texto (`respuesta.text`). No entiende la estructura del HTML: para `requests` es solo una cadena de caracteres.

`BeautifulSoup` es un analizador (parser) de HTML/XML. Toma ese texto y construye un árbol navegable de etiquetas, que se puede recorrer y consultar con `find`, `select` y `select_one`, por etiqueta, clase o atributo. Así se extrae, por ejemplo, el atributo `title` de `h3 a` o la clase de `p.star-rating`. BeautifulSoup no descarga nada.

En resumen, `requests` **obtiene** la página y `BeautifulSoup` la **interpreta**. Se usan juntos.

### Pregunta 2: ¿Qué riesgo existe al depender de selectores HTML específicos si el sitio cambia?

El scraper queda acoplado a la estructura actual de la página. Si el sitio renombra clases (por ejemplo `price_color`), cambia etiquetas o reorganiza el HTML, los selectores dejan de encontrar elementos. Puede pasar lo siguiente:

- `select_one` retorna `None` y el código falla con `AttributeError` al hacer `.get_text()`.
- `select` retorna una lista vacía y se extraen 0 libros sin que haya un error visible.
- **Lo más peligroso:** el selector sigue encontrando algo, pero es otro dato, y se guardan valores incorrectos sin aviso.

Como es un fallo silencioso, hay que validar. En este laboratorio cada campo retorna `None` si no existe, se imprime un aviso por libro incompleto y se revisan el total y los primeros registros. Otras mitigaciones: preferir atributos estables, centralizar los selectores, probar el scraper periódicamente o usar una API oficial si existe.

### Pregunta 3: ¿Por qué normalizar los títulos antes de implementar la búsqueda?

Para que el mismo término escrito de distintas formas se trate como una sola palabra. Sin normalizar, "Life", "life" y "LIFE" o un título con espacios extra podrían quedar como entradas distintas del vocabulario, y una consulta no encontraría títulos que sí la contienen. Además, la consulta se normaliza igual (`strip().lower()`), así que ambos lados quedan comparables. Eso es lo que verifica T3: `LIFE` y `life` producen el mismo ranking.

Un campo `titulo_normalizado` explícito también hace el proceso reproducible e independiente de la herramienta. Por defecto `TfidfVectorizer` ya pasa a minúsculas, pero no hay que depender de esa opción. La normalización también ayuda a detectar duplicados y a descartar títulos vacíos antes de construir el índice. El título original se conserva en `titulo` para mostrarlo en los resultados.

### Pregunta 4: ¿Qué función cumple `fit_transform()` sobre los títulos y por qué se usa `transform()` para la consulta?

`fit_transform()` hace dos cosas sobre la colección de títulos:

1. **fit:** aprende el vocabulario (cada término distinto pasa a ser una columna, 90 en este caso) y calcula el IDF de cada término según en cuántos títulos aparece.
2. **transform:** convierte cada título en su vector TF-IDF. El resultado es `matriz_tfidf`, de 20 × 90.

Para la consulta se usa solo `transform()`, para representarla **en el mismo espacio vectorial** que los títulos: el mismo vocabulario, el mismo orden de columnas y los mismos pesos IDF aprendidos de la colección. Solo así tiene sentido compararla con `cosine_similarity`. Si se hiciera `fit_transform()` con la consulta, se aprendería un vocabulario nuevo de una sola frase. Las dimensiones no coincidirían con la matriz (o la comparación no tendría sentido) y se perdería el IDF de la colección. Los términos que no están en el vocabulario simplemente se ignoran: `zzxyz123` produce un vector de ceros, y por eso T2 no tiene coincidencias.

### Pregunta 5: Si dos libros obtienen similitudes de 0.75 y 0.20 para la misma consulta, ¿cuál se muestra primero? ¿Qué indica una puntuación cercana a cero?

Se muestra primero el de **0.75**. Las puntuaciones se ordenan de mayor a menor con `argsort()[::-1]`, así que el título más similar a la consulta aparece arriba. En T1 pasa lo mismo: 0.2459 aparece antes que 0.2250.

Una puntuación **cercana a cero** indica que el título comparte muy poco con la consulta. Puede compartir solo un término poco distintivo o tener ese término "diluido" entre muchas otras palabras, así que es una coincidencia débil y poco relevante. Una puntuación **igual a 0** significa que no comparten ningún término del vocabulario. El código descarta esos casos (`if puntuaciones[i] <= 0: break`). La medida es léxica: una puntuación baja no dice que los significados sean distintos, solo que comparten pocas palabras.

### Pregunta 6: ¿Qué limitación tiene buscar solo por palabras presentes en títulos mediante TF-IDF? Proponga una mejora concreta.

La búsqueda solo encuentra **coincidencias exactas de palabras** en textos muy cortos. No entiende significado ni variantes. Lo comprobamos con los datos reales:

| Consulta | Qué se esperaría | Resultado actual |
|---|---|---|
| `story` | *Mesaerion: The Best Science Fiction **Stories**...* | «No se encontraron coincidencias.» (singular ≠ plural) |
| `lif` (error de tipeo) | Los títulos con "Life" | «No se encontraron coincidencias.» |
| `vida` (otro idioma / sinónimo) | Los títulos con "Life" | «No se encontraron coincidencias.» |
| `the` (palabra vacía) | Nada útil | Puntuaciones altas (0.41) para títulos con muchos "the" |

Además, un título tiene pocas palabras. Un libro relevante cuyo título no contiene el término de búsqueda (porque el tema está en su descripción o categoría) nunca aparece.

**Mejora concreta: vectorizar por n-gramas de caracteres.**

```python
vectorizador = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
```

Así se indexan trozos de 3 a 5 letras dentro de cada palabra en vez de palabras completas, y la búsqueda tolera plurales, palabras parciales y errores de tipeo. Se probó sobre el mismo `libros.csv`:

- `story` → *Sapiens: A Brief Hi**story** of Humankind* (0.2875) y *Mesaerion: The Best Science Fiction **Stor**ies...* (0.1387). Antes no había resultados.
- `lif` → los 3 títulos con "Life" (0.1261, 0.1017, 0.1008). Antes no había resultados.

Desventaja: aparecen coincidencias parciales poco deseadas ("story" encuentra "History"). Por eso conviene combinarla con estas otras mejoras:

- `stop_words="english"` en el análisis por palabras, para que "the" no influya.
- Indexar también la categoría y la descripción de cada libro (desde su página de detalle).
- Para sinónimos u otros idiomas ("vida" → "life"), usar embeddings semánticos en lugar de TF-IDF.
