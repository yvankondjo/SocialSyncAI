FROM node:20-alpine

# On définit le répertoire de travail standard pour l'application
WORKDIR /app

# On copie d'abord les fichiers de dépendances pour mettre en cache cette étape
COPY package*.json ./
RUN npm install --legacy-peer-deps --ignore-scripts

# Ensuite, on copie le reste du code.
# Cette couche ne sera reconstruite que si vos fichiers de code source changent.
COPY . .

# Variables d'environnement pour le build
ARG SUPABASE_URL
ARG SUPABASE_KEY
RUN echo "SUPABASE_URL=$SUPABASE_URL" >> .env.local
RUN echo "SUPABASE_KEY=$SUPABASE_KEY" >> .env.local

CMD ["npm", "run", "dev"]