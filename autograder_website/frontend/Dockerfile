FROM node:16 AS development

WORKDIR /node

COPY package*.json tsconfig.json ./

ARG NODE_ENV=development

ENV NODE_ENV=${NODE_ENV}

RUN npm install

WORKDIR /node/app

CMD ["npm", "run", "dev"]