import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import os
import google.generativeai as genai
import firebase_admin
from firebase_admin import credentials, auth
from functools import wraps

app = Flask(__name__)

# Configuración de CORS
CORS(app, origins=[
    "http://localhost:4200",
    "https://book-recommender-rosy.vercel.app",
    re.compile(r"^https://book-recommender-.*-celes-projects-b4460b91\.vercel\.app$")
], supports_credentials=True)

load_dotenv()

# --- Inicialización de Firebase ---
cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
if not cred_path:
    cred_path = os.path.join(os.path.dirname(__file__), "firebase_credentials.json")

try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    print("Firebase Admin SDK initialized successfully.")
except Exception as e:
    print(f"Error initializing Firebase Admin SDK: {e}")
    exit(1)

AUTHORIZED_EMAILS = os.getenv("AUTHORIZED_EMAILS", "").split(',')
if not AUTHORIZED_EMAILS or AUTHORIZED_EMAILS == [""]:
    AUTHORIZED_EMAILS = []

# --- Decorador de Autenticación (Corregido y verificado) ---
def firebase_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header missing."}), 401
        try:
            id_token = auth_header.split(' ')[1]
            decoded_token = auth.verify_id_token(id_token)
            user_email = decoded_token.get('email')
            if user_email and user_email in AUTHORIZED_EMAILS:
                request.current_user = decoded_token
                return f(*args, **kwargs)
            else:
                return jsonify({"error": "Unauthorized: Email not in whitelist."}), 403
        except Exception as e:
            return jsonify({"error": f"Authentication failed: {e}"}), 401
    return decorated_function

# --- Configuración de la Base de Datos ---
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

# --- Configuración de Gemini ---
gemini_api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)
for m in genai.list_models():
    print(m.name)

# CORRECCIÓN: Usamos el modelo activo y correcto 'gemini-1.5-flash'
model = genai.GenerativeModel(
    model_name='gemini-3.5-flash',
    system_instruction="Sei un critico letterario esperto. Rispondi sempre e solo in italiano."
)

# --- Rutas de la API ---

@app.route('/api/recomend', methods=['POST'])
@firebase_auth_required
def recommend():
    conn = None
    try:
        data = request.get_json()
        if not data or 'titolo' not in data:
            return jsonify({"error": "El campo 'titolo' es requerido."}), 400
        
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
    except Exception as e:
        return jsonify({"error": "Error interno.", "details": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/deep_dive', methods=['POST'])
@firebase_auth_required
def deep_dive():
    conn = None
    try:
        data = request.get_json()
        if not data or 'titolo' not in data or 'recommendations' not in data:
            return jsonify({"error": "Campos requeridos faltantes."}), 400

        original_title = data['titolo']
        recommendations = data['recommendations']

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT synopsis FROM books WHERE LOWER(TRIM(titolo)) = LOWER(TRIM(%s))", (original_title,))
        original_book_result = cur.fetchone()

        if not original_book_result:
            return jsonify({"error": "Libro original no encontrado."}), 404

        original_synopsis = original_book_result['synopsis']
        recommendations_text = "\n".join(
            [f" - Titolo: {rec['titolo']}, Sinossi: {rec['synopsis']}" for rec in recommendations]
        )

        prompt = f"""
Libro di riferimento: '{original_title}'
Sinossi di riferimento: {original_synopsis}

Libri consigliati:
{recommendations_text}

Analizza la somiglianza di ciascun libro consigliato con il libro di riferimento, considerando stile, genere, trama, ambientazione e tono.
IMPORTANTE: Fornisci solo le analisi, separate dal delimitatore '|||'. Non includere i titoli dei libri.
"""

        # Generamos el contenido usando el SDK estándar limpio
        response = model.generate_content(prompt)
        
        analyses = response.text.split('|||')
        analysis_by_title = {}

        for i, rec in enumerate(recommendations):
            if i < len(analyses):
                analysis_by_title[rec['titolo']] = analyses[i].strip()
            else:
                analysis_by_title[rec['titolo']] = "Analisi non disponibile."

        cur.close()
        return jsonify({"analysis": analysis_by_title})
    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}")
        return jsonify({"error": "Error en Gemini.", "details": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/suggest_titles', methods=['GET'])
def suggest_titles():
    conn = None
    try:
        search_query = request.args.get('query', '')
        if not search_query: return jsonify([])
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT DISTINCT titolo FROM books WHERE TRIM(titolo) ILIKE %s ORDER BY titolo LIMIT 10", (f"%{search_query.strip()}%",))
        suggestions = [row['titolo'] for row in cur.fetchall()]
        cur.close()
        return jsonify(suggestions), 200
    except Exception as e:
        return jsonify({"error": "Error.", "details": str(e)}), 500
    finally:
        if conn: conn.close()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)