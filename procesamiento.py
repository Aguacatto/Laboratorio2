import pandas as pd

from scraper import obtener_libros

# 5.2 Obtener los datos extraidos (el scraping solo ocurre al llamar la funcion)
libros = obtener_libros()

# 5.3 Construir el DataFrame
df = pd.DataFrame(libros)

# 5.4 Verificar la informacion
print(df.head())
print(df.info())
print(df.shape)

columnas_esperadas = ["titulo", "precio", "disponibilidad", "calificacion"]
faltantes = [c for c in columnas_esperadas if c not in df.columns]
if faltantes:
    print(f"Faltan columnas: {faltantes}")
else:
    print(f"Columnas presentes: {list(df.columns)}")

# Paso 6. Limpieza
# Retirar espacios sobrantes (inicio, final y espacios repetidos internos)
df["titulo"] = df["titulo"].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
df["disponibilidad"] = df["disponibilidad"].astype("string").str.strip()

# Eliminar duplicados por titulo
filas_antes = len(df)
df = df.drop_duplicates(subset="titulo").reset_index(drop=True)
print(f"Duplicados eliminados: {filas_antes - len(df)}")

# Campo normalizado en minusculas para la busqueda
df["titulo_normalizado"] = df["titulo"].str.lower()

# Verificar tipos numericos de precio y calificacion
df["precio"] = pd.to_numeric(df["precio"], errors="coerce").astype("float64")
df["calificacion"] = pd.to_numeric(df["calificacion"], errors="coerce").astype("Int64")
print(df.dtypes)

# Paso 7. Indicadores y exportacion
cantidad = len(df)
precio_promedio = df["precio"].mean()
print(f"Cantidad de libros: {cantidad}")
print(f"Precio promedio: {precio_promedio:.2f}")

df.to_csv("libros.csv", index=False, encoding="utf-8")
print("Archivo libros.csv exportado.")
