FROM node:20-alpine

WORKDIR /app

COPY frontend/package.json /app/

RUN npm install

COPY frontend/ /app/

EXPOSE 5173

CMD ["/app/entrypoint.sh"]
