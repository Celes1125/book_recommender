// Este script se utiliza para inyectar variables de entorno en el archivo de configuración de producción de Angular (environment.prod.ts).
// Lee el archivo `environment.prod.ts`, busca marcadores de posición con el formato `process.env['NOMBRE_VARIABLE']`,
// y los reemplaza con los valores reales de las variables de entorno disponibles en el sistema (cargadas desde un archivo .env).
// Esto es crucial para mantener la seguridad y la portabilidad de la aplicación, permitiendo que secretos como claves de API
// se configuren en el entorno de despliegue (por ejemplo, un contenedor Docker) en lugar de estar codificados en el código fuente.

require('dotenv').config();
const fs = require('fs');
const path = require('path');

// Path to your environment file
const envFilePath = path.join(__dirname, 'src', 'environments', 'environment.prod.ts');

console.log(`Reading environment file from: ${envFilePath}`);

// Read the file
let envFileContent = fs.readFileSync(envFilePath, 'utf8');

// Define the regular expression to find all process.env['...'] occurrences
const regex = /process\.env\['(.*?)'\]/g;

// Use the replacer function to substitute all matches at once
const newEnvFileContent = envFileContent.replace(regex, (match, varName) => {
  const value = process.env[varName];

  if (value !== undefined) {
    console.log(`Replacing ${varName} with its value.`);
    // Replace the placeholder with the actual value, properly quoted
    return `'${value}'`;
  } else {
    console.warn(`Warning: Environment variable ${varName} is not set. Replacing with 'undefined'.`);
    // Replace with the string 'undefined' to avoid breaking the build
    return `'undefined'`;
  }
});

// Write the modified content back to the file
fs.writeFileSync(envFilePath, newEnvFileContent, 'utf8');

console.log('Successfully set environment variables for production.');