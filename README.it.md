# Book Recommender

[English](README.md) | [Español](README.es.md)

## Descrizione

Questa applicazione funge da assistente bibliotecario virtuale, fornendo consigli di lettura personalizzati basati sui gusti di un utente. Inserendo il titolo di un libro che hanno apprezzato, gli utenti ricevono cinque consigli di libri simili dal catalogo della biblioteca.

L'applicazione va oltre la semplice corrispondenza dei contenuti, analizzando lo stile, il genere e altre caratteristiche letterarie per fornire consigli di alta qualità. Ogni raccomandazione è accompagnata da un'analisi dettagliata, che spiega perché il libro è stato suggerito, simile alla consulenza di un esperto letterario.

Questo strumento è stato sviluppato per integrare il ruolo del bibliotecario, in particolare per rispondere alle richieste degli utenti di libri simili a quelli che hanno già letto e apprezzato, garantendo che i suggerimenti siano disponibili nella collezione della biblioteca.

L'universo dei dati dell'applicazione si basa sul catalogo di una specifica biblioteca di un paese italiano, con una collezione di 227 titoli di letteratura per adulti.

## Caratteristiche

*   **Consigli personalizzati:** Ottieni 5 consigli di libri basati su un unico titolo.
*   **Analisi approfondita:** Comprendi perché ogni libro è stato consigliato.
*   **Basato sul catalogo della biblioteca:** Tutti i libri consigliati sono disponibili nella biblioteca locale.
*   **Supporto multilingue:** L'interfaccia e i consigli sono forniti in italiano.

## Stack tecnologico

*   **Frontend:** Angular
*   **Backend:** Python (Flask)

## Installazione

### Prerequisiti

*   Node.js e npm
*   Python 3.12+ e pip

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

## Utilizzo

### Esecuzione del backend

```bash
cd backend
source venv/bin/activate
flask run
```

### Esecuzione del frontend

```bash
cd frontend
ng serve
```

Apri il tuo browser e vai su `http://localhost:4200/`.

## Contribuire

I contributi sono benvenuti! Si prega di aprire un problema o un pull request per eventuali modifiche.

## Licenza

Tutti i diritti riservati.

Copyright (c) 2025 María Celeste Colautti
