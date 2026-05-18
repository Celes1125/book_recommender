export const environment = {
  production: true,
  firebaseConfig: {
    // El script set-env.js buscará estas cadenas de texto exactas 
    // y las reemplazará por los valores de Vercel
    apiKey: process.env['NG_APP_FIREBASE_API_KEY'],
    authDomain: process.env['NG_APP_FIREBASE_AUTH_DOMAIN'],
    projectId: process.env['NG_APP_FIREBASE_PROJECT_ID'],
    storageBucket: process.env['NG_APP_FIREBASE_STORAGE_BUCKET'],
    messagingSenderId: process.env['NG_APP_FIREBASE_MESSAGING_SENDER_ID'],
    appId: process.env['NG_APP_FIREBASE_APP_ID']
  },
  apiUrl: process.env['NG_APP_API_URL'],
  db_url: process.env['DATABASE_URL']
  

};