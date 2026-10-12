# Notebooks del Sprint 1 (se ejecutan en local)

| Notebook | Historia | Qué hace |
|---|---|---|
| `01_HU02_EDA_BRISC.ipynb` | HU02 | Verifica la estructura del dataset, cuenta imágenes por clase, partición y plano (y las compara con el artículo), comprueba los pares imagen–máscara, mide el tamaño del tumor, revisa el manifest, genera gráficos y una galería, y guarda `eda_resumen.json`. |
| `02_HU03_particion_y_cargador.ipynb` | HU03 | Revisa archivos corruptos y pares, agrupa imágenes casi idénticas (dHash de 256 bits), parte entrenamiento/validación sin dividir grupos (la prueba oficial no se toca), guarda las listas de partición y prueba un cargador de datos. |

Ejecútalos en este orden. Scripts de apoyo: `descargar_brisc.py` y `ejecutar_sprint1.py`.

## Pasos (Windows, PowerShell o terminal de VS Code)
Desde la carpeta raíz del proyecto:

```bash
pip install -r requirements-probado.txt   # versiones exactas con las que se verificó (requirements.txt las deja sin fijar)
```

Desde esta carpeta (`03. Implementacion/Sprint 1 - Notebooks`):

```bash
python descargar_brisc.py
python ejecutar_sprint1.py
```

1. `descargar_brisc.py` baja BRISC 2025 (~280 MB) a `C:\Users\<tu usuario>\datasets\brisc2025`, **fuera de OneDrive** para no sincronizar ~15.000 imágenes. El dataset es público y se descarga sin iniciar sesión; si Kaggle pidiera autenticación, ejecuta una vez `kaggle auth login` (se abre el navegador; no hay que copiar ningún token). Si ya tienes el dataset en otra carpeta, define la variable de entorno `BRISC_ROOT` con esa ruta o escríbela en `BRISC_ROOT_MANUAL` (primera celda de código de cada notebook).
2. `ejecutar_sprint1.py` corre los dos notebooks y deja los resultados en `salida_sprint1/` (figuras, `eda_resumen.json`, `particion/`, `lote_de_prueba.png`) y copias con todas las salidas en `salida_sprint1/notebooks_ejecutados/`. Esa carpeta no se sube a Git (está en `.gitignore`); las cifras y figuras se llevan a la Revisión del Sprint y al Informe de Estado.
3. Alternativa: abrir los notebooks en VS Code (extensión Jupyter) y usar **Run All**.

Tarda unos minutos: calcula el hash de las 6.000 imágenes. No necesita GPU. PyTorch es opcional en el Sprint 1 (el cargador funciona con NumPy); desde el Sprint 2 hay que instalar la versión CUDA para usar la GPU, porque la versión por defecto en Windows es solo CPU.

## Qué se encontró al ejecutarlo con el dataset real
Los resultados completos están en `salida_sprint1/notebooks_ejecutados/`. Lo principal:

- **Conteos**: 6.000 imágenes (5.000 entrenamiento, 1.000 prueba). Los conteos por clase y partición coinciden con el artículo (diferencia 0). Los conteos por plano difieren levemente de la Tabla 2 del artículo (por ejemplo, entrenamiento axial 1.595 vs 1.550); se usan los observados.
- **Segmentación**: 4.793 pares imagen–máscara, como en el artículo. La clase *sin tumor* **no tiene máscara** (0 de 1.207), y ninguna máscara está vacía.
- **Máscaras**: no son estrictamente binarias (valores intermedios del 0 al 6 y algunos 250 por remuestreo); se binarizan con umbral > 127.
- **Tamaños**: hay 183 combinaciones de ancho × alto (512×512 en 4.881 imágenes; 369×369, 216×369 y otras). El cargador rellena a cuadrado sin deformar y luego redimensiona.
- **Tamaño del tumor**: ocupa en mediana entre 0,9 % (hipófisis) y 1,7 % (meningioma) de la imagen: el fondo domina, y eso condiciona la función de pérdida del Sprint 2.
- **Duplicados**: el manifest tiene 96 archivos de clasificación con SHA-256 repetido (duplicados exactos), 7 de ellos repartidos entre entrenamiento y prueba. Además, 113–123 de las 1.000 imágenes de prueba tienen un vecino casi idéntico en entrenamiento (según dHash y correlación de miniaturas): la prueba oficial puede estar levemente optimista.
- **Partición propia**: 3.999 entrenamiento / 1.001 validación / 1.000 prueba oficial, estratificada por clase y plano (20 % de validación en cada clase y plano), con 4.938 grupos de imágenes parecidas (el mayor, de 3).
- **Código de clase en el nombre**: el archivo usa `no` para *sin tumor* (el README del dataset dice `nt`).

## Decisiones técnicas que deja HU03
Tamaño de entrada `IMG_SIZE = 256`, relleno a cuadrado, normalización con media y desvío de ImageNet, interpolación bilineal para imágenes y *nearest* para máscaras, binarización de máscara > 127, validación del 20 % estratificada por clase y plano, semilla 42 y umbral de hash 16 (de 256 bits). El umbral se eligió midiendo la distancia al vecino más cercano en entrenamiento (con 64 bits y umbral 6 se formaba un grupo de 1.933 imágenes distintas, inútil). Se pueden cambiar en la primera celda del notebook 2.

## Limitaciones
- BRISC no trae ID de paciente: la agrupación por hash reduce, pero no elimina, la fuga entre entrenamiento y validación.
- Solo hay imágenes T1 con contraste.
- Licencia: CC BY 4.0 según los metadatos de Kaggle; hay que citar a los autores.
