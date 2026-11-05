# Stage 1: build the React app into plain HTML/CSS/JS files
FROM node:22-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: serve those files with nginx (a small, fast web server)
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80

# Reading it: this is a two-stage build.
# Stage 1 has Node and all the build tools. It produces the finished website in a dist/ folder.
# Stage 2 starts fresh with just nginx, and copies in only dist/.
# So the final image is tiny, with no Node and no node_modules.
# npm ci is like npm install, but it installs exactly the versions in package-lock.json (version pinning again).
