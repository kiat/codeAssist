FROM node:17 as base

WORKDIR /app

COPY package*.json ./

# Add new node_modules to path
ENV PATH /app/node_modules/.bin:$PATH


# Test stage
FROM base as test

RUN npm ci --silent

COPY . .


# Prod stage
FROM base as prod

RUN npm ci --silent

COPY . .

EXPOSE 3000
CMD ["npm", "start"]
