# AstroPy en Español — Blog con Quarto

Blog de astronomia computacional para hispanohablantes con
conocimientos basicos de Python.

## Estructura del proyecto

```
astropy-blog/
|
├── _quarto.yml                 <- Configuracion principal del sitio
├── index.qmd                   <- Pagina de inicio
├── sobre.qmd                   <- Pagina "Sobre el blog"
├── requirements.txt            <- Dependencias de Python
│
├── posts/
│   ├── basico/                 <- Secciones 01 a 05
│   │   ├── 01-introduccion.qmd
│   │   ├── 02-unidades.qmd
│   │   ├── 03-tiempo.qmd
│   │   ├── 04-coordenadas.qmd
│   │   └── 05-tablas.qmd
│   │
│   ├── intermedio/             <- Secciones 06 a 11
│   │   ├── 06-fits.qmd
│   │   ├── 07-wcs.qmd
│   │   ├── 08-fotometria.qmd
│   │   ├── 09-visualizacion.qmd
│   │   ├── 10-estadistica.qmd
│   │   └── 11-catalogos.qmd
│   │
│   └── avanzado/              <- Secciones 12 a 17
│       ├── 12-espectroscopia.qmd
│       ├── 13-cosmologia.qmd
│       ├── 14-orbital.qmd
│       ├── 15-series-temporales.qmd
│       ├── 16-extensiones.qmd
│       └── 17-pipeline.qmd
│
├── assets/
│   ├── css/
│   │   └── estilo-blog.scss    <- Estilos personalizados (colores, fuentes)
│   ├── images/                 <- Imagenes de portada de cada seccion
│   └── logos/                  <- Logo del blog y favicon
│
├── data/                       <- Archivos de datos de ejemplo (.fits, .csv)
├── notebooks/                  <- Notebooks de desarrollo y pruebas
└── scripts/
    └── plantilla_post.qmd      <- Plantilla para crear nuevas secciones
```

## Inicio rapido

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/astropy-blog.git
cd astropy-blog

# 2. Instalar dependencias de Python
pip install -r requirements.txt

# 3. Instalar Quarto (si no lo tienes)
#    Descarga desde: https://quarto.org/docs/get-started/

# 4. Previsualizar el blog localmente (se abre en el navegador)
quarto preview

# 5. Publicar en GitHub Pages
quarto publish gh-pages
```

## Crear una nueva seccion

```bash
# Copia la plantilla al nivel correspondiente
cp scripts/plantilla_post.qmd posts/basico/nueva-seccion.qmd

# Abre el archivo y edita el encabezado YAML y el contenido
# Luego previsualiza con:
quarto preview posts/basico/nueva-seccion.qmd
```

## Convenciones de codigo

- Todos los bloques tienen comentarios explicativos linea a linea
- Se usa `# ──` para separar secciones dentro de un bloque de codigo
- Cada `import` incluye un comentario indicando para que se usa
- Los ejercicios siempre tienen solucion comentada al final
