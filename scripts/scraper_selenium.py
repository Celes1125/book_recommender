import requests
from bs4 import BeautifulSoup
import re
import csv
import time
from urllib.parse import urljoin

# Importaciones para Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIGURACIÓN ---
MAIN_PAGE_URL = "https://retebibliotecaria.provincia.va.it/opac/search/lst?q=letteratura&home-lib=54&facets-materiale=1&facets-target=m"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def scrape_finalisimo():
    libros_extraidos = []
    book_id_counter = 1

    print("Iniciando el navegador Chromium...")
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless") # Recomiendo dejarlo activado. Si quieres ver la ventana, ponle un '#' delante.
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    
    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        print(f"Navegando a: {MAIN_PAGE_URL}")
        driver.get(MAIN_PAGE_URL)

        try:
            print("Buscando banner de cookies...")
            accept_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.ID, "c-p-bn")))
            accept_button.click()
            print("Banner de cookies aceptado.")
            time.sleep(1)
        except Exception:
            print("Banner de cookies no encontrado o ya aceptado.")
        
        page_num = 1
        while True:
            print(f"\n--- Procesando Página {page_num} ---")
            
            try:
                # ### CAMBIO CRÍTICO Y FINAL: Esperar a los resultados mismos ###
                # Esperamos a que al menos un elemento con la clase 'record' esté presente en el DOM.
                # Esta es la prueba definitiva de que el JavaScript ha cargado los datos.
                print("Esperando a que los resultados de los libros se carguen en la página...")
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.record"))
                )
                print("¡Resultados cargados! Extrayendo datos...")
            except Exception:
                print("La espera ha fallado después de 30 segundos. No se encontraron resultados. Terminando.")
                break

            html_completo = driver.page_source
            soup = BeautifulSoup(html_completo, 'html.parser')
            
            book_records = soup.select('div.record')
            if not book_records:
                print("Contenedor de resultados vacío. Terminando.")
                break

            for record in book_records:
                try:
                    title_tag = record.find('h4', class_='record-title')
                    if not title_tag or not title_tag.a: continue

                    titolo = title_tag.a.text.strip()
                    detail_link = urljoin(MAIN_PAGE_URL, title_tag.a['href'])
                    
                    print(f"  - {titolo[:60]}...")
                    
                    author_tag = record.find('div', class_='record-authors')
                    autore = author_tag.a.text.strip() if author_tag and author_tag.a else "N/A"
                    
                    publication_tag = record.find('div', class_='record-publication')
                    year_match = re.search(r'\b(\d{4})\b', publication_tag.text) if publication_tag else None
                    anno = year_match.group(1) if year_match else "N/A"
                    
                    collocazione_tag = record.find('div', class_='record-shelfmark')
                    collocazione = collocazione_tag.text.strip().replace('Collocazione:', '').strip() if collocazione_tag else "N/A"
                    
                    synopsis = "Sinopsis no disponible."
                    try:
                        detail_response = session.get(detail_link, timeout=10)
                        if detail_response.ok:
                            detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                            synopsis_div = detail_soup.find('div', class_='abstract-text')
                            if synopsis_div:
                                synopsis = synopsis_div.text.strip()
                    except requests.RequestException:
                        print(f"    Error de red al obtener sinopsis para {titolo}")

                    libros_extraidos.append({
                        'id': book_id_counter, 'titolo': titolo, 'autore': autore, 'anno': anno,
                        'synopsis': synopsis, 'collocazione': collocazione,
                    })
                    book_id_counter += 1
                except Exception as e:
                    print(f"    ERROR al procesar una fila: {e}")
                    continue

            try:
                # Usamos find_elements para comprobar si el botón existe sin causar un error
                next_buttons = driver.find_elements(By.CSS_SELECTOR, "a.freccia-dx")
                if next_buttons:
                    print("Pasando a la siguiente página...")
                    driver.execute_script("arguments[0].click();", next_buttons[0])
                    page_num += 1
                    time.sleep(3) 
                else:
                    print("No se encontró el botón 'Siguiente'. Scraping finalizado.")
                    break
            except Exception:
                print("No se pudo hacer clic en 'Siguiente'. Scraping finalizado.")
                break
    finally:
        print("\nCerrando el navegador...")
        driver.quit()
        
        if libros_extraidos:
            nombre_archivo = 'catalogo_finalisimo.csv'
            print(f"Guardando {len(libros_extraidos)} libros en '{nombre_archivo}'...")
            with open(nombre_archivo, mode='w', newline='', encoding='utf-8-sig') as file_csv:
                writer = csv.writer(file_csv, delimiter='|', quoting=csv.QUOTE_ALL)
                writer.writerow(['id', 'titolo', 'autore', 'anno', 'synopsis', 'collocazione'])
                for libro in libros_extraidos:
                    writer.writerow(list(libro.values()))
            print("¡ÉXITO TOTAL!")

if __name__ == "__main__":
    scrape_finalisimo()