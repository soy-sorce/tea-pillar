FROM node:22-alpine AS build

WORKDIR /app

ARG VITE_BACKEND_URL
ENV VITE_BACKEND_URL=${VITE_BACKEND_URL}

COPY package.json package-lock.json /app/
RUN npm ci

COPY . /app
RUN npm run build

FROM node:22-alpine

WORKDIR /app

RUN npm install -g serve

COPY --from=build /app/dist /app/dist

CMD ["serve", "-s", "dist", "-l", "8080"]
