#!/bin/bash

# Script para instalar dependências e pré-processar todos os dados do TCC.
# Este script deve ser executado a partir da pasta raiz do projeto.
# Use o comando: ./setup_and_preprocess.sh

# O comando 'set -e' garante que o script irá parar imediatamente se algum comando falhar.
set -e

echo "--- INICIANDO SETUP E PRÉ-PROCESSAMENTO ---"

# --- PASSO 1: Instalação das bibliotecas Python ---
echo "[PASSO 1/5] Instalando dependências Python via pip..."
pip install torch pandas transformers datasets kaggle peft bitsandbytes tokenizers
echo "[SUCESSO] Dependências instaladas."
echo ""

# --- PASSO 2: Verificação da API do Kaggle ---
echo "[PASSO 2/5] Verificando a configuração da API do Kaggle..."
if [ ! -f ~/.kaggle/kaggle.json ]; then
    echo "-------------------------------------------------------------"
    echo "!!! AÇÃO MANUAL NECESSÁRIA !!!"
    echo "O arquivo 'kaggle.json' não foi encontrado em ~/.kaggle/"
    echo "Por favor, siga estes passos:"
    echo "1. Vá para o seu perfil no site do Kaggle: https://www.kaggle.com/account"
    echo "2. Clique em 'Create New API Token' para baixar o arquivo kaggle.json."
    echo "3. Mova o arquivo para a pasta ~/.kaggle/. Comandos:"
    echo "   mkdir -p ~/.kaggle"
    echo "   mv ~/Downloads/kaggle.json ~/.kaggle/"
    echo "   chmod 600 ~/.kaggle/kaggle.json"
    echo "Depois de fazer isso, rode este script novamente."
    echo "-------------------------------------------------------------"
    exit 1
fi
echo "[SUCESSO] API do Kaggle configurada."
echo ""

# --- PASSO 3: Executar o Pipeline de Aquisição de Dados ---
# Baixa os arquivos JSON brutos do Kaggle.
echo "[PASSO 3/5] Executando o pipeline de aquisição de dados (pipelineGen.py)..."
python3 scripts/pipelineGen.py
echo "[SUCESSO] Aquisição de dados concluída."
echo ""

# --- PASSO 4: Gerar Esquemas e o Manifesto Principal ---
echo "[PASSO 4/5] Gerando esquemas e o manifesto principal (schemaGenerator.py)..."
# Apaga o manifesto antigo para garantir que um novo e limpo seja criado
rm -f datasets/manifest.csv
python3 scripts/schemaGeneration.py
echo "[SUCESSO] Geração de esquemas e manifesto concluída."
echo ""

# --- PASSO 5: Criar o Subconjunto de Dados e o Arquivo Final de Treinamento ---
echo "[PASSO 5/5] Criando subconjunto de dados e arquivo final de treinamento..."
# Cria o subconjunto de 1GB e seu respectivo manifesto
python3 scripts/createSubset.py
# Cria o arquivo training_data.txt para o subconjunto
python3 scripts/prepareData.py
echo "[SUCESSO] Subconjunto de dados e arquivo de treinamento prontos."
echo ""


echo "--- SETUP E PRÉ-PROCESSAMENTO CONCLUÍDOS! ---"
echo "Seu ambiente está pronto. Você já pode rodar o script de treinamento:"
echo "python3 scripts/train_from_scratch.py"
