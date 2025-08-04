#!/bin/bash

# Script para iniciar o ambiente de desenvolvimento Docker do TCC.
# Ele executa o comando 'docker run' com todas as configurações necessárias.

echo "--- Iniciando o ambiente de desenvolvimento Docker para o TCC ---"
echo "Montando a pasta atual '$(pwd)' para '/app' dentro do container..."
echo "Você terá um terminal interativo. Para sair, digite 'exit'."
echo "--------------------------------------------------------------------"

docker run -it --rm \
  -v $(pwd):/app \
  -v ~/.kaggle/kaggle.json:/root/.kaggle/kaggle.json:ro \
  --name tcc-container \
  tcc-ambiente
