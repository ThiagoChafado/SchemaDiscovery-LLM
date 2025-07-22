# scripts/train_from_scratch.py
import torch
from torch.utils.data import Dataset, DataLoader
from tokenizers import ByteLevelBPETokenizer
from transformers import GPT2Config, GPT2LMHeadModel
from torch.optim import AdamW
import os
import pandas as pd # <-- Adicionar import do pandas

# --- Configuration ---
TRAINING_FILE_PATH = 'datasets/subset_1GB/training_data.txt'
TOKENIZER_PATH = './mini_gpt_tokenizer'
MODEL_SAVE_PATH = './mini_gpt_model'
MANIFEST_PATH = 'datasets/subset_1GB/manifest_subset.csv' 

# --- Treinamento do Tokenizer (VERSÃO MODIFICADA) ---
def train_tokenizer():
    """
    Trains a new BPE tokenizer directly from the individual JSON and schema
    files listed in the manifest, which is much more memory-efficient.
    """
    if os.path.exists(TOKENIZER_PATH):
        print(f"Tokenizer already found at {TOKENIZER_PATH}. Skipping training.")
        return
    
    print("Training a new tokenizer from individual files...")
    
    try:
        manifest = pd.read_csv(MANIFEST_PATH)
    except FileNotFoundError:
        print(f"Error: Manifest file not found at {MANIFEST_PATH}. Cannot train tokenizer.")
        # Se o manifesto não existe, o script não pode continuar.
        # Peça para o usuário gerar o manifesto primeiro.
        print("Please run schemaGenerator.py to create the manifest file.")
        exit() # Encerra o script se não puder treinar o tokenizer.

    # Crie uma lista com TODOS os caminhos de arquivos (JSONs e Schemas)
    all_file_paths = []
    for _, row in manifest.iterrows():
        all_file_paths.append(row['json_path'])
        all_file_paths.append(row['schema_path'])

    if not all_file_paths:
        print("No file paths found in manifest. Cannot train tokenizer.")
        exit()

    tokenizer = ByteLevelBPETokenizer()
    
    # Treine o tokenizer na lista de caminhos de arquivos
    tokenizer.train(files=all_file_paths, vocab_size=10_000, min_frequency=2,
                    special_tokens=["<|endoftext|>", "<|pad|>", "<|json|>", "<|schema|>"])
    
    os.makedirs(TOKENIZER_PATH, exist_ok=True)
    tokenizer.save_model(TOKENIZER_PATH)
    print(f"Tokenizer trained and saved to {TOKENIZER_PATH}")

# --- PyTorch Dataset (sem alterações) ---
class JSONSchemaDataset(Dataset):
    def __init__(self, tokenizer, file_path, block_size):
        self.tokenizer = tokenizer
        self.block_size = block_size
        self.examples = []

        print(f"Loading and tokenizing data from {file_path}...")
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        tokenized_text = tokenizer.encode(text)
        
        for i in range(0, len(tokenized_text) - block_size + 1, block_size):
            self.examples.append(tokenized_text[i:i + block_size])

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, i):
        return torch.tensor(self.examples[i], dtype=torch.long)

# --- Função Principal de Treinamento (sem alterações) ---
def train_mini_gpt():
    # 1. Treinar e carregar o tokenizer
    train_tokenizer()
    from transformers import GPT2Tokenizer
    tokenizer = GPT2Tokenizer.from_pretrained(TOKENIZER_PATH)
    if tokenizer.pad_token is None:
        tokenizer.add_special_tokens({'pad_token': '<|pad|>'})

    # 2. Definir a configuração de um modelo minúsculo
    config = GPT2Config(
        vocab_size=tokenizer.vocab_size,
        n_positions=128,
        n_embd=256,
        n_layer=4,
        n_head=4,
    )

    # 3. Instanciar o modelo com a configuração customizada
    model = GPT2LMHeadModel(config)
    print(f"Model created from scratch with {model.num_parameters():,} parameters.")
    model.resize_token_embeddings(len(tokenizer))

    # 4. Preparar o dataset e o DataLoader
    # AVISO: O arquivo training_data.txt AINDA é necessário para esta parte!
    if not os.path.exists(TRAINING_FILE_PATH):
        print(f"Error: {TRAINING_FILE_PATH} not found.")
        print("Please run prepare_data.py before running the training script.")
        exit()
        
    dataset = JSONSchemaDataset(tokenizer, TRAINING_FILE_PATH, block_size=128)
    data_loader = DataLoader(dataset, batch_size=4, shuffle=True)

    # 5. Configurar o otimizador e o loop de treinamento
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    model.to(device)
    
    optimizer = AdamW(model.parameters(), lr=1e-4)
    
    print("Starting training from scratch...")
    model.train()
    for epoch in range(3):
        print(f"--- Epoch {epoch + 1} ---")
        for i, batch in enumerate(data_loader):
            inputs = batch.to(device)
            labels = inputs.clone()
            
            outputs = model(inputs, labels=labels)
            loss = outputs.loss
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            if i % 100 == 0:
                print(f"  Step {i}, Loss: {loss.item()}")

    # 6. Salvar o modelo final
    print("Training finished!")
    model.save_pretrained(MODEL_SAVE_PATH)
    tokenizer.save_pretrained(MODEL_SAVE_PATH)
    print(f"Model and tokenizer saved to {MODEL_SAVE_PATH}")

if __name__ == '__main__':
    train_mini_gpt()