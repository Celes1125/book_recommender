import pandas as pd
import psycopg2
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv
import os

# English: Load environment variables from the .env file
# Español: Cargar variables de entorno desde el archivo .env
# Italiano: Carica le variabili d'ambiente dal file .env
load_dotenv()

# English: Construct absolute path to the CSV file
# Español: Construir la ruta absoluta al archivo CSV
# Italiano: Costruire il percorso assoluto al file CSV
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_dir, 'catalogo_cuveglio_estructurado.csv')

# English: 1. Load the data
# Español: 1. Cargar los datos
# Italiano: 1. Caricare i dati
try:
    df = pd.read_csv(
        csv_file_path,
        sep='|',
        quotechar='"',
        doublequote=True,
        on_bad_lines='warn'
    )
    print("CSV cargado exitosamente.")
except FileNotFoundError:
    print(f"Error: El archivo '{csv_file_path}' no fue encontrado.")
    exit()

# English: Data Cleaning and Preprocessing
# Español: Limpieza y Preprocesamiento de Datos
# Italiano: Pulizia e Pre-elaborazione dei Dati

# Convert 'anno' to numeric, coercing errors to NaN (which will be NULL in DB)
df['anno'] = pd.to_numeric(df['anno'], errors='coerce')

# English: 2. Load the sentence-transformers model
# Español: 2. Cargar el modelo de sentence-transformers
# Italiano: 2. Caricare il modello sentence-transformers
print("Cargando el modelo de sentence-transformers...")
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print("Modelo cargado.")

# English: 3. Generate the vectors for the synopses
# Español: 3. Generar los vectores para las sinopsis
# Italiano: 3. Generare i vettori per le sinossi
print("Generando vectores para las sinopsis...")
# English: Ensure the synopsis is a string
# Español: Asegurarse de que la sinopsis sea un string
# Italiano: Assicurarsi che la sinossi sia una stringa
df['synopsis'] = df['synopsis'].astype(str)
embeddings = model.encode(df['synopsis'].tolist(), show_progress_bar=True)
print(f"Se generaron {len(embeddings)} vectores.")

# English: 4. Connect to the database using the DATABASE_URL environment variable
# Español: 4. Conectarse a la base de datos usando la variable de entorno DATABASE_URL
# Italiano: 4. Connettersi al database utilizzando la variabile d'ambiente DATABASE_URL
try:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("La variable de entorno DATABASE_URL no está configurada.")
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    print("Conexión a la base de datos PostgreSQL exitosa.")
except psycopg2.OperationalError as e:
    print(f"Error al conectar a la base de datos: {e}")
    exit()

# English: Clear the table before populating to ensure a clean state
# Español: Vaciar la tabla antes de poblarla para asegurar un estado limpio
# Italiano: Svuotare la tabella prima di popolarla per garantire uno stato pulito
print("Vaciando la tabla 'books'...")
cur.execute("TRUNCATE TABLE books RESTART IDENTITY CASCADE;")
print("Tabla 'books' vaciada.")

# English: 5. Iterate and insert the data into the 'books' table
# Español: 5. Iterar e insertar los datos en la tabla 'books'
# Italiano: 5. Iterare e inserire i dati nella tabella 'books'
print("Insertando libros en la base de datos...")
for index, row in df.iterrows():
    book_id = row['id']
    title = row['titolo']
    author = row['autore']
    year = row['anno']
    synopsis = row['synopsis']
    collocazione = row['collocazione']
    # English: Convert to a list for psycopg2
    # Español: Convertir a lista para psycopg2
    # Italiano: Convertire in una lista per psycopg2
    embedding = embeddings[index].tolist() 

    try:
        cur.execute(
            """INSERT INTO books (id, titolo, autore, anno, synopsis, collocazione, embedding) VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (book_id, title, author, year, synopsis, collocazione, embedding)

        )
        print(f"Insertado: '{title}'")
    except Exception as e:
        print(f"Error al insertar '{title}': {e}")
        # English: Roll back the transaction in case of an error
        # Español: Revertir la transacción en caso de error
        # Italiano: Annullare la transazione in caso di errore
        conn.rollback() 
        cur.close()
        conn.close()
        exit()

# English: Commit the changes and close the connection
# Español: Confirmar los cambios y cerrar la conexión
# Italiano: Confermare le modifiche e chiudere la connessione
conn.commit()
cur.close()
conn.close()

print("\n¡Éxito! La base de datos 'recommender' ha sido poblada con los datos de los libros.")