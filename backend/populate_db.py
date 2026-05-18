import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from sentence_transformers import SentenceTransformer
mport os
from dotenv import load_dotenv  # Importante para leer el archivo .env local

# Carga las variables del archivo .env (solo funciona localmente, en Render se ignora)
load_dotenv()

def populate_database():
    # --- CONFIGURACIÓN ---
    csv_file = 'catalogo_cuveglio_estructurado.csv'
    model_name = 'paraphrase-multilingual-MiniLM-L12-v2'
    
    # URL de Supabase optimizada para redes que no soportan IPv6
    # Usamos el Connection Pooler (Supavisor) en el puerto 6543 que soporta IPv4
    # Host: aws-0-eu-central-1.pooler.supabase.com (Asumiendo región Frankfurt por la IP previa)
    # Usuario: postgres.ijqdjvutfcxzwjqzuwwn
   
    # La forma correcta de obtener la variable
    db_url = os.getenv("DATABASE_URL")

    try:
        # 1. Cargar y limpiar datos
        print(f"Leyendo {csv_file}...")
        df = pd.read_csv(csv_file, sep='|', quotechar='"', doublequote=True)
        
        # Limpieza básica
        df['anno'] = pd.to_numeric(df['anno'], errors='coerce').fillna(0).astype(int)
        df['synopsis'] = df['synopsis'].astype(str).replace('nan', 'Sinopsis no disponible.')
        
        # 2. Generar Embeddings
        print(f"Cargando modelo {model_name} (versión CPU)...")
        model = SentenceTransformer(model_name, device='cpu')
        print("Generando vectores (esto puede tardar unos minutos)...")
        embeddings = model.encode(df['synopsis'].tolist(), show_progress_bar=True)

        # 3. Conexión e Inserción
        print("Conectando a Supabase a través del Pooler (Soporta IPv4)...")
        with psycopg2.connect(db_url) as conn:
            with conn.cursor() as cur:
                # Limpiar tabla (TRUNCATE)
                print("Vaciando tabla public.books...")
                cur.execute("TRUNCATE TABLE public.books RESTART IDENTITY CASCADE;")

                # Preparar datos para inserción masiva
                data_to_insert = []
                for i, row in df.iterrows():
                    data_to_insert.append((
                        int(row['id']),
                        row['titolo'],
                        row['autore'],
                        row['synopsis'],
                        embeddings[i].tolist(),
                        row['collocazione'],
                        int(row['anno'])
                    ))

                # Inserción eficiente por lotes
                print(f"Insertando {len(data_to_insert)} registros en esquema public...")
                query = """
                    INSERT INTO public.books 
                    (id, titolo, autore, synopsis, embedding, collocazione, anno) 
                    VALUES %s
                """
                execute_values(cur, query, data_to_insert)
                
                print("¡Migración completada con éxito!")

    except Exception as e:
        print(f"ERROR CRÍTICO: {e}")
        print("\nNota: Si el error persiste, verifica en Supabase (Settings > Database) ")
        print("la URL de 'Connection Pooler' y asegúrate de que el modo sea 'Transaction'.")

if __name__ == "__main__":
    populate_database()
