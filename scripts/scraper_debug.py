import requests
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN ---
BASE_URL = "https://retebibliotecaria.provincia.va.it/opac/search/lst?q=letteratura&home-lib=54&facets-materiale=1&facets-target=m"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def debug_scraper():
    """
    Esta función solo intentará descargar la primera página y nos mostrará lo que recibe.
    """
    try:
        print("Intentando conectar con la URL...")
        first_page_url = f"{BASE_URL}&start=0"
        response = requests.get(first_page_url, headers=HEADERS)

        # ### DEBUG 1: Imprimir el código de estado HTTP ###
        # 200 significa OK. 403 significa Prohibido. 503 significa Error del Servidor.
        print(f"Código de Estado HTTP recibido: {response.status_code}")

        # ### DEBUG 2: Imprimir los primeros 1000 caracteres del HTML ###
        # Esto nos permite ver si la página es la correcta o una de error.
        print("\n--- Inicio del HTML recibido (primeros 1000 caracteres) ---\n")
        print(response.text[:1000])
        print("\n--- Fin del HTML recibido ---\n")

        # El resto del código para que veas dónde falla
        print("Buscando el resumen de resultados en el HTML recibido...")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results_summary = soup.find('div', class_='results-summary')
        
        if not results_summary:
            print("\nRESULTADO DEL DEBUG: Efectivamente, no se pudo encontrar el 'div' con la clase 'results-summary'.")
            print("Revisa el HTML de arriba. ¿Se parece a la página de la biblioteca o a una página de error/CAPTCHA?")
        else:
            print("\nRESULTADO DEL DEBUG: ¡Éxito! Se encontró el resumen de resultados. El problema podría ser otro.")
            print(f"Texto encontrado: {results_summary.text.strip()}")

    except requests.exceptions.RequestException as e:
        print(f"Error de red al conectar con la página: {e}")
    except Exception as e:
        print(f"Ha ocurrido un error inesperado: {e}")

# --- EJECUTAR EL SCRIPT DE DEBUG ---
if __name__ == "__main__":
    debug_scraper()