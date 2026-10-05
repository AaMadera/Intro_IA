# Intro AI

This repo is to create answers to subject assessments, and for notes

## Assessments

1. Basic concepts of AI
    - [exercise 1](./01_basic_concepts_of_AI/01-answer.md)
2. Agents
     - [exercise 1](./02_agents/exercise-01/README.md)
     - [exercise 2](./02_agents/exercise-02/README.md)
3. Uninformed search
    - [exercise 1](./03_uninformed_search/exercise-01/README.md)
4. Informed Search
    - [exercise 1](./04_informed_search/exercise-01/README.md)
    - [exercise 2 (Optional)](./04_informed_search/exercise-02/README.md)

## Proyecto final: Habanero RAG

El proyecto final es un MVP de RAG en español para consultar información agrícola sobre chile habanero. Consulta la configuración completa, la decisión sobre el corpus, el flujo de Docker Compose, las URLs de la API/UI, las pruebas y el checklist de evidencias en el [README del proyecto final](./final_project/README.md).

Desde `final_project/`, configura `GOOGLE_API_KEY` en `.env` y ejecuta:

```bash
uv sync --locked
docker compose build
docker compose up
```

Abre Streamlit en <http://localhost:8501> y la documentación de FastAPI en <http://localhost:8000/docs>. Detén los servicios con `docker compose down` y ejecuta las pruebas con `uv run pytest -q`.

## Subject web site

- <https://sites.google.com/view/victoruccetina/curso-mia>
