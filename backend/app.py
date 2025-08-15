from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import numpy as np
from dotenv import load_dotenv
import os
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth
from functools import wraps

app = Flask(__name__)
CORS(app)
load_dotenv()

# --- Firebase Initialization ---
# Path to Firebase credentials. For production (e.g., Render), this is set via
# an environment variable. For local development, it defaults to a local file.
cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
if not cred_path:
    cred_path = os.path.join(os.path.dirname(__file__), "firebase_credentials.json")

try:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    print("Firebase Admin SDK initialized successfully.")
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")
    # English: Depending on your deployment, you might want to exit or handle this more gracefully
    # Español: Dependiendo de tu despliegue, podrías querer salir o manejar esto de forma más elegante
    # Italiano: A seconda della tua distribuzione, potresti voler uscire o gestire questo in modo più elegante
    exit(1)

# English: List of authorized emails (whitelist)
# Español: Lista de emails autorizados (lista blanca)
# Italiano: Elenco di email autorizzate (whitelist)
# English: IMPORTANT: In a production environment, load this from an environment variable or a secure configuration.
# Español: IMPORTANTE: En un entorno de producción, carga esto desde una variable de entorno o una configuración segura.
# Italiano: IMPORTANTE: In un ambiente di produzione, caricalo da una variabile d'ambiente o da una configurazione sicura.
AUTHORIZED_EMAILS = os.getenv("AUTHORIZED_EMAILS", "").split(',')
if not AUTHORIZED_EMAILS or AUTHORIZED_EMAILS == ['']:
    print("WARNING: AUTHORIZED_EMAILS is not set or is empty. No users will be authorized.")
    AUTHORIZED_EMAILS = [] # Ensure it's an empty list if not set

# --- Authentication Decorator ---
def firebase_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header missing."}), 401

        try:
            id_token = auth_header.split(' ')[1]
            decoded_token = auth.verify_id_token(id_token)
            uid = decoded_token['uid']
            user_email = decoded_token.get('email')

            if user_email and user_email in AUTHORIZED_EMAILS:
                # English: You can pass the user_id or email to the decorated function if needed
                # Español: Puedes pasar el user_id o email a la función decorada si es necesario
                # Italiano: Puoi passare l'user_id o l'email alla funzione decorata se necessario
                request.current_user = decoded_token
                return f(*args, **kwargs)
            else:
                return jsonify({"error": "Unauthorized: Email not in whitelist."}), 403
        except Exception as e:
            return jsonify({"error": f"Authentication failed: {e}"}), 401
    return decorated_function

# --- Database Configuration ---
# The connection is configured via the DATABASE_URL environment variable provided by Render.
def get_db_connection():
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("La variable de entorno DATABASE_URL no está configurada.")
        
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error al conectar con la base de datos: {e}")
        raise

gemini_api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel(
    'gemini-1.5-flash-latest',
    system_instruction="Sei un critico letterario esperto. Rispondi sempre e solo in italiano.")

@app.route('/recomend', methods=['POST'])
@firebase_auth_required
def recommend():
    conn = None
    try:
        data = request.get_json()
        if not data or 'titolo' not in data:
            return jsonify({"error": "El campo 'titolo' es requerido en el JSON."}), 400
        
        title = data['titolo']

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        search_pattern = f"%{title.strip()}%"
        cur.execute("SELECT id, titolo, embedding FROM books WHERE TRIM(titolo) ILIKE %s", (search_pattern,))
        matching_books = cur.fetchall()

        if not matching_books:
            return jsonify({"error": f"Nessun libro trovato che corrisponda a '{title}'."}), 404

        if len(matching_books) > 1:
            return jsonify({
                "message": "Trovati più libri. Seleziona quello corretto.",
                "options": [book['titolo'] for book in matching_books]
            }), 200

        the_book = matching_books[0]
        book_id = the_book['id']
        book_vector = the_book['embedding']
        
        query = """
            SELECT id, titolo, autore, synopsis, collocazione, anno
            FROM books 
            WHERE id != %s
            ORDER BY embedding <=> %s 
            LIMIT 5
        """
        cur.execute(query, (book_id, book_vector,))
        similar_books = cur.fetchall()

        results = [dict(book) for book in similar_books]

        cur.close()
        return jsonify(results), 200

    except psycopg2.OperationalError as e:
        return jsonify({"error": "Error de base de datos.", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Ha ocurrido un error interno en el servidor.", "details": str(e)}), 500
    finally:
        if conn is not None:
            conn.close()

@app.route('/deep_dive', methods=['POST'])
@firebase_auth_required
def deep_dive():
    conn = None
    try:
        data = request.get_json()
        if not data or 'titolo' not in data or 'recommendations' not in data:
            return jsonify({"error": "Los campos 'titolo' y 'recommendations' son requeridos."}), 400

        original_title = data['titolo']
        recommendations = data['recommendations']

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("SELECT synopsis FROM books WHERE LOWER(TRIM(titolo)) = LOWER(TRIM(%s))", (original_title,))
        original_book_result = cur.fetchone()

        if original_book_result is None:
            return jsonify({"error": f"Libro original con título '{original_title}' no encontrado."}), 404

        original_synopsis = original_book_result['synopsis']

        recommendations_text = "\n".join(
            [f" - Titolo: {rec['titolo']}, Sinossi: {rec['synopsis']}" for rec in recommendations]
        )

        prompt = f"""
Libro di riferimento: '{original_title}'
Sinossi di riferimento: {original_synopsis}

Libri consigliati:
{recommendations_text}

Analizza la somiglianza di ciascun libro consigliato con el libro de referencia, considerando stile, genere, trama, ambientazione e tono.
IMPORTANTE: Fornisci solo le analisi, separate dal delimitatore '|||'. Non includer los títulos de los libros en tu respuesta.
"""

        response = model.generate_content(prompt)
        
        analyses = response.text.split('|||')
        analysis_by_title = {}

        if len(analyses) == len(recommendations):
            for i, rec in enumerate(recommendations):
                analysis_by_title[rec['titolo']] = analyses[i].strip()
        else:
            print(f"Error: El número de análisis ({len(analyses)}) no coincide con el número de recomendaciones ({len(recommendations)}).")

        cur.close()
        return jsonify({"analysis": analysis_by_title})

    except psycopg2.OperationalError as e:
        return jsonify({"error": "Error de base de datos.", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Ha ocurrido un error interno en el servidor.", "details": str(e)}), 500
    finally:
        if conn is not None:
            conn.close()

@app.route('/suggest_titles', methods=['GET'])

def suggest_titles():
    conn = None
    try:
        search_query = request.args.get('query', '')
        if not search_query:
            return jsonify([])

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute("SELECT DISTINCT titolo FROM books WHERE TRIM(titolo) ILIKE %s ORDER BY titolo LIMIT 10", (f"%{search_query.strip()}%",))
        suggestions = [row['titolo'] for row in cur.fetchall()]
        
        cur.close()
        return jsonify(suggestions), 200

    except psycopg2.OperationalError as e:
        return jsonify({"error": "Error de base de datos.", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Ha ocurrido un error interno en el servidor.", "details": str(e)}), 500
    finally:
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)