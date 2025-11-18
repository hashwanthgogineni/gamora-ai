FROM python:3.11-slim

# Install Godot
RUN apt-get update && apt-get install -y wget unzip && \
    wget https://github.com/godotengine/godot/releases/download/4.2.1-stable/Godot_v4.2.1-stable_linux.x86_64.zip && \
    unzip Godot_v4.2.1-stable_linux.x86_64.zip && \
    mv Godot_v4.2.1-stable_linux.x86_64 /usr/local/bin/godot && \
    chmod +x /usr/local/bin/godot && \
    rm -rf *.zip && apt-get clean

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
