# --- Etapa 1: Build ---
FROM node:20 AS build
WORKDIR /app
# Habilita pnpm vía corepack
RUN corepack enable
# Copia manifests
COPY package.json pnpm-lock.yaml ./
# Instala dependencias exactas del lockfile
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm run build -- --configuration production

# --- Etapa 2: Serve ---
FROM nginx:alpine
COPY --from=build /app/dist/frontend /usr/share/nginx/html
EXPOSE 80
