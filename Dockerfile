# Usar uma imagem base com Python
FROM python:3.9-slim

# Atualizar pacotes e instalar dependências necessárias
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Adicionar o PATH do Chromium para o ChromeDriver encontrá-lo
ENV PATH="/usr/lib/chromium-browser/:${PATH}"

# Instalar dependências do Python
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copiar o código para o diretório de trabalho
COPY . /app
WORKDIR /app

# Definir a variável de ambiente para o Flask
ENV FLASK_APP=app.py

# Comando para iniciar a aplicação
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
