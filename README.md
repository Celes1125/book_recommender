# Book Recommender

[Italiano](README.it.md) | [Español](README.es.md)

## Description

This application acts as a virtual librarian assistant, providing personalized reading recommendations based on a user's tastes. By entering the title of a book they have enjoyed, users receive five recommendations for similar books from the library's catalog.

The application goes beyond simple content matching, analyzing style, genre, and other literary characteristics to provide high-quality recommendations. Each recommendation is accompanied by a detailed analysis, explaining why the book has been suggested, similar to the advice of a literary expert.

This tool was developed to complement the role of the librarian, particularly in responding to user requests for books similar to those they have already read and enjoyed, ensuring that the suggestions are available in the library's collection.

The application's data universe is based on the catalog of a specific library in an Italian town, with a collection of 227 adult literature titles.

## Features

*   **Personalized recommendations:** Get 5 book recommendations based on a single title.
*   **In-depth analysis:** Understand why each book was recommended.
*   **Based on the library's catalog:** All recommended books are available in the local library.
*   **Language support:** The interface and recommendations are provided in Italian.

## Tech Stack

*   **Frontend:** Angular
*   **Backend:** Python (Flask)

## Installation

### Prerequisites

*   Node.js and npm
*   Python 3.12+ and pip

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

## Usage

### Running the backend

```bash
cd backend
source venv/bin/activate
flask run
```

### Running the frontend

```bash
cd frontend
ng serve
```

Open your browser and go to `http://localhost:4200/`.

## Contributing

Contributions are welcome! Please open an issue or a pull request for any changes.

## License

All Rights Reserved.

Copyright (c) 2025 María Celeste Colautti