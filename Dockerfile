# Dockerfile (versão corrigida com ambiente virtual)

# Começamos com uma base de sistema operacional moderna
FROM ubuntu:24.04

# Evita que o instalador faça perguntas interativas
ENV DEBIAN_FRONTEND=noninteractive

# Instala as ferramentas de sistema, o Python 3 e o pacote venv
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    python3.12-venv \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# --- NOVO: Criação do Ambiente Virtual ---
# 1. Cria um ambiente virtual na pasta /opt/venv
RUN python3 -m venv /opt/venv

# 2. Ativa o ambiente virtual para todos os comandos seguintes, adicionando-o ao PATH
ENV PATH="/opt/venv/bin:$PATH"

# Define um diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de requisitos para dentro do container
COPY requirements.txt .

# Instala todas as bibliotecas Python DENTRO do ambiente virtual
# Este comando agora funciona sem erro
RUN pip install --no-cache-dir -r requirements.txt

# Copia todos os seus scripts e dados para dentro do container
COPY . .

# Define o comando padrão para iniciar um terminal interativo
CMD ["/bin/bash"]
