# Use Node 20-slim as the base image
FROM node:20-slim

# Set work directory
WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the application code
COPY . .

# Expose the port Vite runs on (configured in vite.config.js as 5174)
EXPOSE 5174

# Command to run the application in dev mode with --host
CMD ["npm", "run", "dev", "--", "--host"]
