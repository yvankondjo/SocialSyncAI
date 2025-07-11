FROM node:20-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps --ignore-scripts
COPY . .

ARG SUPABASE_URL
ARG SUPABASE_KEY

# Créer un .env.local avec les variables pour le build
RUN echo "SUPABASE_URL=$SUPABASE_URL" >> .env.local
RUN echo "SUPABASE_KEY=$SUPABASE_KEY" >> .env.local

CMD ["npm", "run", "dev"]