# Use an official Python runtime as a parent image
FROM python:3.11-slim

# First, update the package lists and install the essential build tools.
RUN apt-get update && apt-get install -y build-essential python3-dev

# Set the working directory in the container
WORKDIR /app

# --- THIS IS THE UPGRADE TO UV ---
# Install uv, the fast package installer, using pip.
RUN pip install uv
# --------------------------------

# Copy the requirements file into the container
COPY requirements.txt .

# --- THIS IS THE FIX ---
# Use uv to install packages. It's much faster than pip.
# The --system flag tells uv to install into the global site-packages,
# which is standard practice inside a Docker container.
RUN uv pip install --system --no-cache -r requirements.txt
# --------------------

# Copy the rest of the application's code
COPY ./app ./app
COPY ./firebase-credentials.json .

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
