# Recomendador de Libros

[English](README.md) | [Italiano](README.it.md)

## Descripción

Esta aplicación actúa como un asistente de bibliotecario virtual, proporcionando recomendaciones de lectura personalizadas basadas en los gustos de un usuario. Al introducir el título de un libro que han disfrutado, los usuarios reciben cinco recomendaciones de libros similares del catálogo de la biblioteca.

La aplicación va más allá de la simple coincidencia de contenido, analizando el estilo, el género y otras características literarias para proporcionar recomendaciones de alta calidad. Cada recomendación va acompañada de un análisis detallado, que explica por qué se ha sugerido el libro, de forma similar al asesoramiento de un experto literario.

Esta herramienta fue desarrollada para complementar el papel del bibliotecario, en particular para responder a las solicitudes de los usuarios de libros similares a los que ya han leído y disfrutado, garantizando que las sugerencias estén disponibles en la colección de la biblioteca.

El universo de datos de la aplicación se basa en el catálogo de una biblioteca específica de un pueblo italiano, con una colección de 227 títulos de literatura para adultos.

## Características

*   **Recomendaciones personalizadas:** Obtén 5 recomendaciones de libros basadas en un solo título.
*   **Análisis en profundidad:** Comprende por qué se recomendó cada libro.
*   **Basado en el catálogo de la biblioteca:** Todos los libros recomendados están disponibles en la biblioteca local.
*   **Soporte de idiomas:** La interfaz y las recomendaciones se proporcionan in italiano.

## Tecnologías Utilizadas

*   **Frontend:** Angular
*   **Backend:** Python (Flask)

## Instalación

### Prerrequisitos

*   Node.js y npm
*   Python 3.12+ y pip

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

## Uso

### Ejecutar el backend

```bash
cd backend
source venv/bin/activate
flask run
```

### Ejecutar el frontend

```bash
cd frontend
ng serve
```

Abre tu navegador y ve a `http://localhost:4200/`.

## Contribuir

¡Las contribuciones son bienvenidas! Por favor, abre un issue o un pull request para cualquier cambio.

## Licencia

Todos los derechos reservados.

Copyright (c) 2025 María Celeste Colautti
