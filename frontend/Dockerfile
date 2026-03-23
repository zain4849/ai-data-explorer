# Start from a lightweight Node.js image.
# node:20-alpine = Node.js version 20 on a small Linux system.
# AS build names this stage build, so it can be referenced later.
FROM node:20-alpine AS build


# Sets the working folder inside the container to /app.
# All following commands will run inside this folder.
WORKDIR /app 

# Now every command that follows will run inside /app.

# Copies the package.json and package-lock.json files to the container in /app/package.json and /app/package-lock.json  .
COPY frontend/package.json frontend/package-lock.json* /app/

# Installs the dependencies.
RUN npm ci

# Copies the rest of the frontend code to the container in /app/frontend.
# This may include package.json again, but Docker just overwrites the file with the same content. So it's the same as before anyways.
COPY frontend/ /app 

# Structure of the container so far:
#  /app
#  ├─ package.json
#  ├─ package-lock.json
#  ├─ src/
#  │   └─ App.js
#  ├─ public/
#  │   └─ index.html
#  └─ vite.config.js

# Builds the frontend.
RUN npm run build
# Start from a lightweight Nginx image.
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

