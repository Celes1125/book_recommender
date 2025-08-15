# Usa una imagen oficial de Python como base. 
# La etiqueta "slim" es una versión ligera, ideal para producción.
FROM python:3.11-slim

# Establece el directorio de trabajo dentro del contenedor.
WORKDIR /app

# Copia solo el archivo de requisitos primero.
# Esto aprovecha el sistema de caché de Docker: si no cambias los requisitos,
# no se volverán a instalar las librerías en cada construcción.
COPY requirements.txt .

# Instala las dependencias de Python.
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de tu backend al directorio de trabajo del contenedor.
COPY . .

# El comando para ejecutar tu aplicación cuando el contenedor se inicie.
# Usamos Gunicorn, que es un servidor WSGI de nivel de producción para Python.
# Flask por sí solo no es para producción.
# Render nos dará un puerto en la variable de entorno $PORT, que suele ser 10000.
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]