# Use a Node.js base image
FROM node:18-alpine

# Set the working directory
WORKDIR /app

# Copy package.json and install dependencies
# Using 'npm ci' is a best practice for reproducible builds
COPY package.json ./
COPY package-lock.json ./
RUN npm ci

# Copy the rest of the application source code
COPY . .

# Expose the port React runs on and define the run command
EXPOSE 3000
CMD ["npm", "start"]