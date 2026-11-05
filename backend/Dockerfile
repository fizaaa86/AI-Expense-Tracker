# Recipe for the backend container
FROM python:3.12-slim

WORKDIR /app

# Install the libraries first. Docker remembers (caches) this step,
# so rebuilding after a code change doesn't reinstall everything.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Then copy in the code
COPY . .

EXPOSE 8000
CMD ["fastapi", "run", "main.py", "--port", "8000"]
