FROM node:14
WORKDIR /var/app
COPY package.json package-lock.json /var/app/
RUN npm install
COPY src /var/app/
ENTRYPOINT ["node", "."]
