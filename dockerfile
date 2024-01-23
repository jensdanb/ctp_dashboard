# Force platform to download proper wheel (with waved included).
# An alternative is to either download wheel manually or download and run waved separately.
FROM --platform=linux/amd64 python:3.10

# Create a project directory.
RUN mkdir /app
WORKDIR /app

# Install Python dependencies.
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

# Run your app.
CMD ["./wave/waved"]
CMD ["wave", "run", "src/web_app.py"]
