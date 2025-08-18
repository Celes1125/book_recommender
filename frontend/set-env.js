
const fs = require('fs');
const path = require('path');

// Path to your environment file
const envFilePath = path.join(__dirname, 'src', 'environments', 'environment.prod.ts');

// Read the file
let envFileContent = fs.readFileSync(envFilePath, 'utf8');

// Find all process.env['...'] occurrences and replace them
const regex = /process\.env\['(.*?)'\]/g;
let match;
while ((match = regex.exec(envFileContent)) !== null) {
  const varName = match[1];
  const value = process.env[varName];

  if (value === undefined) {
    console.warn(`Warning: Environment variable ${varName} is not set.`);
    // Replace with a default value or handle as an error
    // For now, replacing with 'undefined' as a string to avoid breaking the build
    envFileContent = envFileContent.replace(match[0], `'undefined'`);
  } else {
    // Replace the placeholder with the actual value
    envFileContent = envFileContent.replace(match[0], `'${value}'`);
  }
}

// Write the file back
fs.writeFileSync(envFilePath, envFileContent, 'utf8');

console.log('Environment variables set for production.');
