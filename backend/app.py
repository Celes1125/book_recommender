# Español: Empezamos importando todas las herramientas necesarias para nuestra aplicación.
# English: We start by importing all the necessary tools for our application.
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

# Español: Aquí nace nuestra aplicación Flask, el corazón de nuestro backend.
# English: Here our Flask application is born, the heart of our backend.
app = Flask(__name__)

# Español: Abrimos las puertas para que nuestros frontends puedan hablar con este backend.
# English: We open the doors so our frontends can talk to this backend.
CORS(app, origins=[
    "http://localhost:4200",
    "https://book-recommender-rosy.vercel.app",
    re.compile(r"^https://book-recommender-.*-celes-projects-b4460b91\.vercel\.app$")
], supports_credentials=True)

# Español: Cargamos las variables de entorno, nuestros pequeños secretos de configuración.
# English: We load the environment variables, our little configuration secrets.
load_dotenv()

# --- Inicialización de Firebase ---
# --- Firebase Initialization ---

# Español: Buscamos las credenciales de Firebase. Son la llave maestra para los servicios de Google.
# English: We look for the Firebase credentials. They are the master key to Google's services.
cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
if not cred_path:
    cred_path = os.path.join(os.path.dirname(__file__), "firebase_credentials.json")

try:
    # Español: Con las credenciales en mano, nos identificamos ante Firebase.
    # English: With the credentials in hand, we identify ourselves to Firebase.
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
    print("Firebase Admin SDK initialized successfully.")
except Exception as e:
    # Español: Si algo sale mal, lo sabremos y detendremos todo para no causar problemas.
    # English: If something goes wrong, we'll know and stop everything to avoid causing problems.
    print(f"Error initializing Firebase Admin SDK: {e}")
    exit(1)

# Español: Creamos nuestra lista de invitados VIP. Solo los emails en esta lista podrán usar la API.
# English: We create our VIP guest list. Only emails on this list will be able to use the API.
AUTHORIZED_EMAILS = os.getenv("AUTHORIZED_EMAILS", "").split(',')
if not AUTHORIZED_EMAILS or AUTHORIZED_EMAILS == [""]:
    print("WARNING: AUTHORIZED_EMAILS is not set or is empty. No users will be authorized.")
    AUTHORIZED_EMAILS = []

# --- Decorador de Autenticación ---
# --- Authentication Decorator ---

# Español: Este es nuestro portero. Una función que envuelve a otras para protegerlas.
# English: This is our bouncer. A function that wraps others to protect them.
def firebase_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Español: Primero, pedimos la identificación (el token de autorización).
        # English: First, we ask for identification (the authorization token).
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header missing."}), 401

        try:
            # Español: Verificamos que la identificación sea válida y no una falsificación.
            # English: We verify that the identification is valid and not a fake.
            id_token = auth_header.split(' ')[1]
            decoded_token = auth.verify_id_token(id_token)
            user_email = decoded_token.get('email')

            # Español: Comprobamos si el email del usuario está en nuestra lista VIP.
            # English: We check if the user's email is on our VIP list.
            if user_email and user_email in AUTHORIZED_EMAILS:
                # Español: ¡Adelante! El usuario está autorizado y puede pasar.
                # English: Welcome! The user is authorized and can proceed.
                request.current_user = decoded_token
                return f(*args, **kwargs)
            else:
                # Español: Acceso denegado. Este email no está en la lista.
                # English: Access denied. This email is not on the list.
                return jsonify({"error": "Unauthorized: Email not in whitelist."}, 403)
        except Exception as e:
            # Español: La identificación parece ser inválida o ha expirado.
            # English: The identification seems to be invalid or has expired.
            return jsonify({"error": f"Authentication failed: {e}"}), 401
    return decorated_function

# --- Configuración de la Base de Datos ---
# --- Database Configuration ---

# Español: Esta función crea un túnel seguro hacia nuestra base de datos PostgreSQL.
# English: This function creates a secure tunnel to our PostgreSQL database.
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

# Español: Despertamos a nuestro crítico literario de IA, Gemini, dándole su clave de API.
# English: We awaken our AI literary critic, Gemini, by giving it its API key.
gemini_api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=gemini_api_key)

# Español: Le damos a Gemini sus instrucciones: es un experto y debe hablar siempre en italiano.
# English: We give Gemini its instructions: it's an expert and must always speak Italian.
model = genai.GenerativeModel(
    'gemini-1.5-flash-latest',
    system_instruction="Sei un critico letterario esperto. Rispondi sempre e solo in italiano.")

# --- Rutas de la API ---
# --- API Routes ---

# Español: La ruta para encontrar recomendaciones. Solo usuarios autorizados pueden pasar.
# English: The route for finding recommendations. Only authorized users are allowed.
@app.route('/api/recomend', methods=['POST'])
@firebase_auth_required
def recommend():
    conn = None
    try:
        # Español: Obtenemos el título del libro que el usuario quiere usar como referencia.
        # English: We get the title of the book the user wants to use as a reference.
        data = request.get_json()
        if not data or 'titolo' not in data:
            return jsonify({"error": "El campo 'titolo' es requerido en el JSON."}, 400)
        
        title = data['titolo']

        # Español: Abrimos la conexión con la base de datos para buscar el libro.
        # English: We open the connection to the database to search for the book.
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Español: Buscamos libros que coincidan con el título que nos dieron.
        # English: We search for books that match the title we were given.
        search_pattern = f"%{title.strip()}%")
        cur.execute("SELECT id, titolo, embedding FROM books WHERE TRIM(titolo) ILIKE %s", (search_pattern,))
        matching_books = cur.fetchall()

        if not matching_books:
            return jsonify({"error": f"Nessun libro trovato che corrisponda a '{title}'."}), 404

        # Español: Si hay muchos resultados, le pedimos al usuario que sea más específico.
        # English: If there are too many results, we ask the user to be more specific.
        if len(matching_books) > 1:
            return jsonify({
                "message": "Trovati più libri. Seleziona quello corretto.",
                "options": [book['titolo'] for book in matching_books]
            }), 200

        # Español: Encontramos el libro exacto y tomamos su "vector embedding", que es como su ADN literario.
        # English: We found the exact book and take its "vector embedding", which is like its literary DNA.
        the_book = matching_books[0]
        book_id = the_book['id']
        book_vector = the_book['embedding']
        
        # Español: Usamos el ADN del libro para encontrar los 5 libros más similares en toda la base de datos.
        # English: We use the book's DNA to find the 5 most similar books in the entire database.
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
        # Español: Al final, siempre cerramos la conexión para ser ordenados.
        # English: In the end, we always close the connection to be tidy.
        if conn is not None:
            conn.close()

# Español: La ruta para un análisis profundo, donde la IA entra en acción.
# English: The route for a deep dive, where the AI comes into play.
@app.route('/api/deep_dive', methods=['POST'])
@firebase_auth_required
def deep_dive():
    conn = None
    try:
        # Español: Recibimos el libro original y las recomendaciones que encontramos antes.
        # English: We receive the original book and the recommendations we found earlier.
        data = request.get_json()
        if not data or 'titolo' not in data or 'recommendations' not in data:
            return jsonify({"error": "Los campos 'titolo' y 'recommendations' son requeridos."}, 400)

        original_title = data['titolo']
        recommendations = data['recommendations']

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Español: Buscamos la sinopsis del libro original para dársela a la IA como contexto.
        # English: We look for the original book's synopsis to give to the AI as context.
        cur.execute("SELECT synopsis FROM books WHERE LOWER(TRIM(titolo)) = LOWER(TRIM(%s))", (original_title,))
        original_book_result = cur.fetchone()

        if original_book_result is None:
            return jsonify({"error": f"Libro original con título '{original_title}' no encontrado."}, 404)

        original_synopsis = original_book_result['synopsis']

        # Español: Preparamos un texto con todas las recomendaciones para enviárselo a Gemini.
        # English: We prepare a text with all the recommendations to send to Gemini.
        recommendations_text = "\n".join(
            [f" - Titolo: {rec['titolo']}, Sinossi: {rec['synopsis']}" for rec in recommendations]
        )

        # Español: Creamos el "prompt": las instrucciones detalladas para que la IA haga su análisis.
        # English: We create the "prompt": the detailed instructions for the AI to perform its analysis.
        prompt = f"""
Libro di riferimento: '{original_title}'
Sinossi di riferimento: {original_synopsis}

Libri consigliati:
{recommendations_text}

Analizza la somiglianza di ciascun libro consigliato con el libro de referencia, considerando stile, genere, trama, ambientazione e tono.
IMPORTANTE: Fornisci solo le analisi, separate dal delimitatore '|||'. Non includer los títulos de los libros en tu respuesta.
"""

        # Español: Enviamos el prompt a Gemini y esperamos su experta opinión.
        # English: We send the prompt to Gemini and await its expert opinion.
        response = model.generate_content(prompt)
        
        # Español: Procesamos la respuesta de la IA para organizarla y enviarla de vuelta al usuario.
        # English: We process the AI's response to organize it and send it back to the user.
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

# Español: Una ruta de ayuda para sugerir títulos mientras el usuario escribe (autocomplete).
# English: A helper route to suggest titles as the user writes (autocomplete).
@app.route('/api/suggest_titles', methods=['GET'])
def suggest_titles():
    conn = None
    try:
        # Español: Tomamos lo que el usuario ha escrito hasta ahora.
        # English: We take what the user has written so far.
        search_query = request.args.get('query', '')
        if not search_query:
            return jsonify([])

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Español: Buscamos en la base de datos hasta 10 títulos que empiecen con esas letras.
        # English: We search the database for up to 10 titles that start with those letters.
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

# Español: ¡Luces, cámara, acción! Si ejecutamos este archivo directamente, la aplicación se pone en marcha.
# English: Lights, camera, action! If we run this file directly, the application starts.
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
