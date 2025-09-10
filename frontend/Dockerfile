FROM node:20-alpine

WORKDIR /app

# Installer les dépendances système nécessaires
RUN apk add --no-cache libc6-compat

# Copier les fichiers de package pour le cache
COPY package*.json ./

# Nettoyer le cache et installer les dépendances
# Utiliser npm ci si package-lock.json existe et est valide, sinon npm install
RUN if [ -f package-lock.json ] && [ -s package-lock.json ]; then \
        npm ci --legacy-peer-deps --no-audit --no-fund; \
    else \
        npm install --legacy-peer-deps --no-audit --no-fund; \
    fi

# Copier le code source
COPY . .

# Variables d'environnement
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1
ENV WATCHPACK_POLLING=true

# Exposer le port
EXPOSE 3000

# Commande de développement avec hot reload
CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0"]