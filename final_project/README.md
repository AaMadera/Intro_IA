# Proyecto final: Habanero RAG

Este proyecto es un MVP educativo de RAG para consultar información agrícola sobre chile habanero. La interfaz está construida con Streamlit, la API con FastAPI, la recuperación vectorial con ChromaDB y los modelos de Google AI.

## Corpus inicial

El corpus incluido en [`pdfs_seed/`](./pdfs_seed/) contiene estos cuatro PDF:

- `2025_Manual-fertilizacion_GRC.pdf`
- `Agenda_Tecnica_Yucatan_2017.pdf`
- `Ficha-Tecnica-Chile-Hab_Balche.pdf`
- `Ficha-Tecnica-Chile-Hab_Kisin.pdf`

Estos cuatro documentos se conservan intencionalmente para este MVP porque, en conjunto, son extensos, coherentes y contienen varios miles de palabras sobre fertilización, cultivo, variedades y manejo del chile habanero. Esto es una excepción práctica a la guía general de usar cinco documentos para la actividad: no se agrega un quinto PDF porque el corpus actual ya ofrece evidencia suficiente y consistente para la demostración.

La indexación no ocurre automáticamente al iniciar los servicios. En la interfaz se debe pulsar **Indexar corpus inicial**. La API también permite solicitar la misma operación con `POST /ingest` usando `action=corpus`.

## Requisitos

- Python 3.12.
- [`uv`](https://docs.astral.sh/uv/).
- Docker y Docker Compose para ejecutar los dos servicios.
- Una clave de Google AI.

## Configuración local

Desde este directorio (`final_project/`), sincroniza el entorno bloqueado:

```bash
uv sync --locked
```

Crea el archivo local de variables a partir de la plantilla:

```bash
cp .env.example .env
```

Obtén `GOOGLE_API_KEY` en [Google AI Studio](https://aistudio.google.com/api-keys) y completa `.env`:

```dotenv
GOOGLE_API_KEY=pega_aqui_tu_clave_local
```

La configuración también acepta temporalmente el nombre `GEMINI_API_KEY`,
pero `GOOGLE_API_KEY` es el nombre recomendado y usado en la plantilla.

La clave es un secreto local. No la escribas en el código, capturas de pantalla, commits ni archivos compartidos. `.env`, los textos generados y la persistencia de Chroma están excluidos de Git.

La configuración predeterminada es:

| Variable | Valor | Uso |
| --- | --- | --- |
| `GOOGLE_EMBEDDING_MODEL` | `gemini-embedding-001` | Embeddings de documentos y preguntas |
| `GOOGLE_GENERATION_MODEL` | `gemini-2.0-flash` | Generación de respuestas en español |
| `CHUNK_SIZE` | `300` | Palabras por fragmento |
| `CHUNK_OVERLAP` | `60` | Palabras compartidas entre fragmentos |
| `TOP_K` | `4` | Evidencias recuperadas por defecto |
| `MIN_SCORE` | `0.35` | Umbral mínimo de evidencia |
| `CHROMA_PATH` | `./chroma` | Persistencia del índice vectorial |

El mismo modelo de embeddings se usa para indexar los fragmentos y para buscar preguntas. Si la mejor evidencia tiene una puntuación menor que `MIN_SCORE`, o no hay corpus indexado, la API se abstiene: devuelve un mensaje en español y no llama al modelo de generación.

## Ejecución con Docker Compose

Con `.env` configurado, ejecuta desde `final_project/`:

```bash
docker compose build
docker compose up
```

Compose valida que `GOOGLE_API_KEY` no esté vacía antes de iniciar la API. Si
falta la clave, copia `.env.example` a `.env`, agrega la clave de Google AI
Studio y vuelve a ejecutar `docker compose up`.

Para dejar los servicios en segundo plano usa `docker compose up -d`. Las URLs son:

- Streamlit: <http://localhost:8501>
- Documentación interactiva de FastAPI: <http://localhost:8000/docs>
- Estado de la API: <http://localhost:8000/health>

Detén los servicios con:

```bash
docker compose down
```

El volumen montado `chroma/` conserva el índice y `data/processed/` conserva los textos extraídos al detener o recrear los contenedores.

## Flujo de uso

1. Abre <http://localhost:8501>.
2. Pulsa **Indexar corpus inicial** y espera el resultado de documentos y fragmentos procesados.
3. Escribe una pregunta en español, por ejemplo: `¿Cómo se recomienda fertilizar el chile habanero?`.
4. Pulsa **Consultar**. La respuesta muestra citas numeradas `[1]`, `[2]` y sus fuentes, fragmentos y puntuaciones.
5. Para ampliar el corpus, carga archivos PDF, Markdown (`.md` o `.markdown`) o texto plano (`.txt`) y pulsa **Cargar documentos**.

La carga acepta varios archivos y los procesa mediante `POST /ingest`. Una pregunta se envía a `POST /query`; también se puede probar ambos endpoints desde <http://localhost:8000/docs>. La UI solo se comunica con FastAPI: no accede directamente a Google AI ni a ChromaDB.

## Procesamiento de documentos

Para un PDF, la API intenta primero usar `opendataloader-pdf` cuando está disponible. Si el comando no existe o falla, usa `pypdf` como fallback. El texto extraído se guarda como UTF-8 en `data/processed/` para poder inspeccionarlo. Los archivos Markdown y texto se leen directamente y también quedan representados en el área de datos procesados. Los PDF escaneados que no contienen texto extraíble están fuera del alcance de este MVP y producen un error visible por archivo.

Cada documento se divide en fragmentos de 300 palabras con un solapamiento de 60 palabras por defecto. El hash estable de la fuente evita crear duplicados al indexar de nuevo el mismo archivo. El índice de Chroma y los artefactos procesados se mantienen entre reinicios mediante las rutas persistentes del Compose.

## Pruebas y verificación

Ejecuta las pruebas y la comprobación de sintaxis con el entorno bloqueado:

```bash
uv sync --locked
uv run pytest -q
uv run python -m compileall app ui
```

Las pruebas cubren extracción y fallback de PDF, fragmentación, persistencia y deduplicación de Chroma, endpoints de salud/indexación/consulta, abstención, errores de la UI y configuración de Docker. Las pruebas automatizadas usan dobles para no necesitar una clave real; la demostración manual sí requiere `GOOGLE_API_KEY`.

## Evidencias

Consulta [`evidence/README.md`](./evidence/README.md) para la lista de capturas y comprobaciones manuales requeridas. Las evidencias deben mostrar respuestas citadas, la consulta equivalente en `/docs`, una abstención fuera de dominio y la persistencia tras reiniciar, sin revelar la clave ni incluir secretos en el repositorio.
