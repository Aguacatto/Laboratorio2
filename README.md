# Laboratorio 2 - Web Scraping, procesamiento y recuperación de información

## Integrantes

- Vicente Palma
- Diego Alvarado
- Lucas Pinto

## Repositorio

https://github.com/Aguacatto/Laboratorio2

## Archivos

- `scraper.py`: scraping de la primera página de books.toscrape.com
- `procesamiento.py`: pasa los datos a un DataFrame, los limpia y genera `libros.csv`
- `buscador.py`: buscador de títulos con TF-IDF y similitud del coseno
- `libros.csv`: los datos ya procesados
- `requirements.txt`: librerías del entorno
- `.gitignore`: para no subir la carpeta `.venv/`

## Entorno virtual

Lo hicimos en Windows con PowerShell y Python 3.14.3.

Crear el entorno:

```
py -m venv .venv
```

Activarlo (este es el comando que usamos):

```
.venv\Scripts\Activate.ps1
```

En CMD sería `.venv\Scripts\activate.bat`.

Para comprobar que el python es el del entorno:

```
python -c "import sys; print(sys.executable)"
```

Nos salió `C:\Users\lucas\Documents\GitHub\Laboratorio2\.venv\Scripts\python.exe`, así que estaba bien.

Instalar las librerías:

```
python -m pip install --upgrade pip
python -m pip install requests beautifulsoup4 pandas scikit-learn
python -m pip freeze > requirements.txt
```

Nota: en PowerShell el `>` guarda el archivo en UTF-16, por eso el requirements lo generamos con `python -m pip freeze | Out-File -Encoding ascii requirements.txt` para que quedara como texto normal. El contenido es el mismo.

En el `.gitignore` pusimos la línea `.venv/`. Con `git status --short --ignored` la carpeta aparece como `!! .venv/`, o sea ignorada, así que no se sube al repositorio.

## Cómo ejecutarlo desde cero (Paso 14)

```
git clone https://github.com/Aguacatto/Laboratorio2.git
cd Laboratorio2
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Orden de ejecución:

1. `python scraper.py` (opcional, es para ver que la extracción funciona)
2. `python procesamiento.py` (hace el scraping, limpia los datos y genera `libros.csv`)
3. `python buscador.py` (pide una palabra y muestra los libros encontrados)

`procesamiento.py` importa `obtener_libros()` desde `scraper.py`. Como el scraper tiene el `if __name__ == "__main__":`, al importarlo no se vuelve a ejecutar todo solo.

## Parte I - Web Scraping

En `scraper.py` se hace `requests.get(URL, timeout=10)`, se revisa el código de respuesta con `raise_for_status()` y el HTML se analiza con BeautifulSoup. Solo se usa la primera página, sin paginación.

Revisando la página con el inspector del navegador sacamos los selectores:

- cada libro está en un `article.product_pod`
- título: el atributo `title` del `h3 a` (el texto del link viene cortado, por ejemplo "A Light in the ...")
- precio: `p.price_color`, y se pasa a float
- disponibilidad: `p.availability`
- calificación: viene como clase en `p.star-rating` (por ejemplo `star-rating Three`), y con un diccionario la pasamos a un número del 1 al 5

Un problema que tuvimos es que el precio salía como `Â£51.77`, porque la página no dice qué codificación usa. Lo arreglamos con `respuesta.encoding = "utf-8"` y además sacamos el número con una expresión regular, así el símbolo de la moneda no molesta.

**Datos faltantes (Paso 4):** cada campo se saca con una función que devuelve `None` si no encuentra el elemento, así el programa no se cae. Si a un libro le falta algo se imprime un aviso y el libro se guarda igual con ese campo en `None`. Si un libro da otro error, se avisa y se sigue con el siguiente. En nuestra ejecución no salió ningún aviso, los 20 libros tenían todos los datos.

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

## Parte II - Procesamiento

En `procesamiento.py` se arma el DataFrame con `pd.DataFrame(libros)` y se revisa con `head()`, `info()` y `shape`:

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

Tiene las 4 columnas que se pedían: titulo, precio, disponibilidad y calificacion.

Limpieza (Paso 6):

- se sacan los espacios de más en `titulo` y `disponibilidad`
- se eliminan los duplicados por título (no había ninguno: `Duplicados eliminados: 0`)
- se crea `titulo_normalizado` con el título en minúsculas
- con `pd.to_numeric` se verifica que `precio` sea float y `calificacion` entero

Después se calculan los indicadores y se exporta `libros.csv` sin índice y en UTF-8 (Paso 7):

```
Cantidad de libros: 20
Precio promedio: 38.05
Archivo libros.csv exportado.
```

## Parte III - Buscador

`buscador.py` tiene el código que venía en el Paso 10. Lee `libros.csv`, crea el índice TF-IDF con la columna `titulo_normalizado` (quedaron 90 palabras en el vocabulario) y muestra hasta 5 libros con similitud mayor a 0, de mayor a menor.

### Paso 11: dos consultas

Probamos con `life` y con `the`, que son palabras que vimos en los títulos.

`life`:

```
Ingrese una palabra o titulo: life
Scott Pilgrim's Precious Little Life (Scott Pilgrim #1) | Precio: 52.29 | Similitud: 0.2459
The Coming Woman: A Novel Based on the Life of the Infamous Feminist, Victoria Woodhull | Precio: 17.93 | Similitud: 0.2250
Our Band Could Be Your Life: Scenes from the American Indie Underground, 1981-1991 | Precio: 57.25 | Similitud: 0.2231
```

`the`:

```
Ingrese una palabra o titulo: the
The Coming Woman: A Novel Based on the Life of the Infamous Feminist, Victoria Woodhull | Precio: 17.93 | Similitud: 0.4181
The Boys in the Boat: Nine Americans and Their Epic Quest for Gold at the 1936 Berlin Olympics | Precio: 22.6 | Similitud: 0.3630
The Black Maria | Precio: 52.15 | Similitud: 0.3282
The Requiem Red | Precio: 22.65 | Similitud: 0.3282
Tipping the Velvet | Precio: 53.74 | Similitud: 0.3282
```

Comparando el orden:

- Con `life` salen los 3 títulos que tienen esa palabra, y cada uno la tiene una sola vez. Primero sale el de Scott Pilgrim porque tiene menos palabras distintas (5, contra 12 y 14 de los otros), entonces "life" pesa más en ese título. Los otros dos quedan casi iguales.
- Con `the` hay 10 títulos que la tienen, pero solo se muestran 5 por el `top_k=5`. "The Coming Woman" y "The Boys in the Boat" tienen "the" 3 veces cada uno, y gana el primero porque es más corto (14 palabras contra 18). Los otros tres empatan en 0.3282 porque son títulos de 3 palabras. Esto muestra que el buscador solo cuenta palabras y no sabe qué es relevante, porque "the" no aporta nada a la búsqueda.

### Desafío: top_k=3

Cambiamos `resultados = buscar(consulta)` por `resultados = buscar(consulta, top_k=3)` y probamos con `the`:

```
Ingrese una palabra o titulo: the
The Coming Woman: A Novel Based on the Life of the Infamous Feminist, Victoria Woodhull | Precio: 17.93 | Similitud: 0.4181
The Boys in the Boat: Nine Americans and Their Epic Quest for Gold at the 1936 Berlin Olympics | Precio: 22.6 | Similitud: 0.3630
The Black Maria | Precio: 52.15 | Similitud: 0.3282
```

Salieron solo 3 aunque había 10 coincidencias, todos con similitud positiva, así que funciona. Con `life` salieron los mismos 3 de antes porque solo hay 3 títulos con esa palabra. Después dejamos la llamada como estaba en el código original.

## Parte IV - Pruebas (Paso 12)

Ejecutamos `python buscador.py` con el entorno activado. Para hacerlo más rápido le pasamos la consulta con `printf` desde Git Bash (por ejemplo `printf 'life\n' | python buscador.py`), que es lo mismo que escribirla en la terminal. Ninguna prueba tiró error.

| Caso | Consulta utilizada | Resultado observado | Estado |
|---|---|---|---|
| T1 | life | Salieron 3 libros con similitud positiva y ordenados de mayor a menor: Scott Pilgrim's Precious Little Life (0.2459), The Coming Woman (0.2250) y Our Band Could Be Your Life (0.2231). | Cumple |
| T2 | zzxyz123 | Se mostró «No se encontraron coincidencias.» | Cumple |
| T3 | LIFE | Salió el mismo ranking que en T1, con los mismos libros, orden y puntajes. | Cumple |
| T4 | [vacía] | Se mostró «Ingrese una consulta no vacia.» y después «No se encontraron coincidencias.», sin error. | Cumple |

Salidas:

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

### Problemas que encontramos

- En T4 salen dos mensajes. `buscar()` imprime «Ingrese una consulta no vacia.» y devuelve una lista vacía, y después el main imprime «No se encontraron coincidencias.» porque ve la lista vacía. Igual cumple, pero el segundo mensaje sobra. Se podría arreglar revisando si la consulta está vacía antes de llamar a `buscar()`.
- Con `the` hay tres libros empatados en 0.3282. El orden entre esos tres lo decide `argsort()`, no tiene que ver con cuál es más relevante.
- La primera vez probamos T4 en PowerShell con `"" | python buscador.py` y no salía el mensaje de consulta vacía. Revisando vimos que PowerShell agrega un carácter invisible (BOM) al principio del texto, y como `strip()` no lo borra, la consulta no quedaba vacía. Escribiendo la consulta a mano o usando Git Bash funciona bien, así que no es un problema del código.

## Paso 13 - Evidencias

- Libros extraídos: 20
- Precio promedio: £38.05 (el más barato cuesta £13.99 y el más caro £57.25)
- Búsqueda 1: `life` (es la misma de T1)
- Búsqueda 2: `scott pilgrim`

```
Ingrese una palabra o titulo: scott pilgrim
Scott Pilgrim's Precious Little Life (Scott Pilgrim #1) | Precio: 52.29 | Similitud: 0.8770
```

Acá la similitud es 0.8770, mucho más alta que con `life`, porque las dos palabras solo están en ese título y además aparecen dos veces.

## Preguntas

### Pregunta 1: ¿Para qué sirve BeautifulSoup y cómo se diferencia de requests?

requests sirve para hacer la petición HTTP a la página y traer el HTML (con timeout, código de estado, etc.), pero lo trae como un texto, no entiende la estructura de la página. BeautifulSoup sirve para analizar ese HTML y armar un árbol donde se pueden buscar etiquetas por clase o atributo, con `find`, `select` o `select_one`. O sea, requests descarga la página y BeautifulSoup la lee para sacar los datos. Por eso se usan juntos.

### Pregunta 2: ¿Qué riesgo existe al depender de selectores HTML específicos si el sitio cambia?

Si el sitio cambia el nombre de una clase o la estructura del HTML, los selectores dejan de encontrar los elementos. Puede pasar que el programa se caiga (por ejemplo un `AttributeError` al hacer `.get_text()` sobre `None`), que no se extraiga ningún libro y no salga ningún error, o lo peor, que el selector encuentre otra cosa y se guarden datos malos sin que nadie se dé cuenta. Por eso en el scraper manejamos los `None`, mostramos avisos y revisamos el total y los primeros registros. También ayudaría tener los selectores en un solo lugar para cambiarlos fácil, o usar una API si el sitio tiene una.

### Pregunta 3: ¿Por qué normalizar los títulos antes de implementar la búsqueda?

Para que una misma palabra escrita de distinta forma se tome como la misma. Si no se normaliza, "Life" y "life", o un título con espacios de más, podrían quedar como términos distintos y la búsqueda no encontraría títulos que sí tienen la palabra. Como la consulta también se pasa a minúsculas en `buscar()`, los dos lados quedan iguales, y eso es lo que se ve en T3 (`LIFE` da lo mismo que `life`). TfidfVectorizer igual pasa todo a minúsculas por defecto, pero tener la columna normalizada deja el proceso más claro y no depende de esa opción. El título original queda en `titulo` para mostrarlo en los resultados.

### Pregunta 4: ¿Qué función cumple fit_transform() sobre los títulos y por qué se usa transform() para la consulta?

`fit_transform()` hace dos cosas con los títulos. El fit aprende el vocabulario (cada palabra distinta es una columna, en nuestro caso 90) y calcula el IDF de cada palabra según en cuántos títulos aparece. El transform convierte cada título en su vector TF-IDF. Así queda la matriz de 20 x 90.

Para la consulta se usa solo `transform()` porque tiene que quedar en el mismo espacio que los títulos, con el mismo vocabulario y los mismos IDF, si no no se pueden comparar con la similitud del coseno. Si usáramos `fit_transform()` con la consulta, se crearía un vocabulario nuevo solo con esas palabras y las dimensiones no calzarían con la matriz. Las palabras que no están en el vocabulario se ignoran, por eso `zzxyz123` queda como un vector de puros ceros y no encuentra nada (T2).

### Pregunta 5: Si dos libros obtienen similitudes de 0.75 y 0.20 para la misma consulta, ¿cuál se muestra primero? ¿Qué indica una puntuación cercana a cero?

Primero se muestra el de 0.75, porque los resultados se ordenan de mayor a menor similitud (`argsort()[::-1]`). En T1 pasa lo mismo, el de 0.2459 sale antes que el de 0.2250.

Una puntuación cercana a cero significa que el título tiene muy poco en común con la consulta, por ejemplo comparte una palabra poco importante o la palabra queda "diluida" en un título muy largo. Si es exactamente 0 es porque no comparten ninguna palabra, y el código no muestra esos resultados (`if puntuaciones[i] <= 0: break`). Eso sí, esto es solo por palabras: un puntaje bajo no quiere decir que el significado sea distinto.

### Pregunta 6: ¿Qué limitación tiene buscar solo por palabras presentes en títulos mediante TF-IDF? Proponga una mejora concreta.

La limitación es que solo encuentra palabras exactas, y los títulos tienen pocas palabras. No reconoce plurales, errores de tipeo, sinónimos ni otros idiomas. Lo probamos con nuestros datos:

- `story` no encuentra "Mesaerion: The Best Science Fiction Stories" (singular contra plural)
- `lif` (mal escrito) no encuentra los títulos con "Life"
- `vida` no encuentra nada, aunque hay títulos con "Life"
- `the` sí da resultados con puntajes altos, aunque es una palabra que no dice nada

Además, si un libro trata de algo pero no lo dice en el título, nunca va a aparecer en la búsqueda.

Mejora: usar n-gramas de caracteres en el vectorizador.

```python
vectorizador = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
```

Así se comparan pedazos de 3 a 5 letras en vez de palabras completas, y la búsqueda aguanta plurales y errores de tipeo. Lo probamos con el mismo `libros.csv`:

- `story` encuentra "Sapiens: A Brief History of Humankind" (0.2875) y "Mesaerion: The Best Science Fiction Stories" (0.1387)
- `lif` encuentra los 3 títulos que tienen "Life"

El problema es que también encuentra cosas que no tienen que ver, como "story" con "History". Se podría complementar usando `stop_words="english"` para que palabras como "the" no cuenten, agregando la descripción o la categoría de cada libro al índice, o usando embeddings para que encuentre sinónimos.
