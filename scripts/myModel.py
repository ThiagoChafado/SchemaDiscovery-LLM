# scripts/myModel.py (ou train_from_scratch.py)
import torch
from torch.utils.data import Dataset, DataLoader
from tokenizers import ByteLevelBPETokenizer
from transformers import GPT2Config, GPT2LMHeadModel
from torch.optim import AdamW
import os
import pandas as pd


# Apontando para o subconjunto de dados
DATASETS_DIR = 'datasets/subset_1GB'
TRAINING_FILE_PATH = os.path.join(DATASETS_DIR, 'training_data.txt')
MANIFEST_PATH = os.path.join(DATASETS_DIR, 'manifest_subset.csv')

# --- Configuração de Checkpoints ---
TOKENIZER_PATH = './mini_gpt_tokenizer'
# A pasta de checkpoints será o local principal para salvar
CHECKPOINT_DIR = './training_checkpoints'
# Salvar a cada 5000 passos.
SAVE_EVERY_N_STEPS = 5000

# --- Treinamento do Tokenizer ---
def train_tokenizer():
    # Cria um vocabulário (tokenizer) do zero.
    # Em vez de usar um arquivo gigante, ele lê o `manifest_subset.csv` e aprende
    # as "palavras" (tokens) mais comuns diretamente dos arquivos JSON e de esquema individuais.
    # É muito mais eficiente em memória. Ele salva o tokenizer treinado para uso futuro.

    if os.path.exists(TOKENIZER_PATH):
        print(f"Tokenizer already found at {TOKENIZER_PATH}. Skipping training.")
        return
    print("Training a new tokenizer...")
    manifest = pd.read_csv(MANIFEST_PATH)
    all_file_paths = []
    for _, row in manifest.iterrows():
        all_file_paths.append(row['json_path'])
        all_file_paths.append(row['schema_path'])
    tokenizer = ByteLevelBPETokenizer()
    tokenizer.train(files=all_file_paths, vocab_size=10_000, min_frequency=2,
                special_tokens=["<|endoftext|>", "<|pad|>"]) # Manteve apenas os essenciais
    os.makedirs(TOKENIZER_PATH, exist_ok=True)
    tokenizer.save_model(TOKENIZER_PATH)
    print(f"Tokenizer trained and saved to {TOKENIZER_PATH}")

# --- PyTorch Dataset ---
    # Uma classe do PyTorch para carregar os dados.
    # 1. No início (`__init__`), ela lê o arquivo `training_data.txt` de uma vez.
    # 2. Tokeniza todo o texto usando o tokenizer que acabamos de treinar.
    # 3. Divide a longa sequência de tokens em blocos de tamanho fixo (`block_size`).
    #    Cada bloco se torna um exemplo de treinamento.
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

# --- Função Principal de Treinamento ---
    # 1. Chama `train_tokenizer()` para garantir que o vocabulário exista.
    # 2. Carrega o tokenizer treinado.
    # 3. **Criação do Modelo**: Define uma arquitetura de modelo (`GPT2Config`)
    #    muito pequena e customizada (poucas camadas, etc.).
    # 4. Usa essa configuração para instanciar um modelo `GPT2LMHeadModel` com
    #    pesos **aleatórios** (ou seja, "do zero").
    # 5. **Loop de Treinamento**:
    #    a. Carrega os dados em lotes (batches) usando a classe `JSONSchemaDataset`.
    #    b. Para cada lote, faz o passo de `forward` (o modelo tenta prever a próxima palavra).
    #    c. Calcula o erro (`loss`).
    #    d. Faz o passo de `backward` (calcula como ajustar os pesos para diminuir o erro).
    #    e. Atualiza os pesos do modelo (`optimizer.step()`).
    #    f. Repete isso para todos os dados por várias épocas.
    # 6. **Salva o Modelo:** Ao final, salva os pesos do modelo treinado para que ele
    #    possa ser carregado e usado para inferência no futuro.
def train_mini_gpt():
    train_tokenizer()
    from transformers import GPT2Tokenizer
    tokenizer = GPT2Tokenizer.from_pretrained(TOKENIZER_PATH)
    if tokenizer.pad_token is None:
        tokenizer.add_special_tokens({'pad_token': '<|pad|>'})

    # --- Lógica para carregar do checkpoint ---
    start_epoch = 0
    global_step = 0
    
    if os.path.exists(CHECKPOINT_DIR):
        print(f"Checkpoint found at {CHECKPOINT_DIR}. Resuming training.")
        # Carrega o modelo e a configuração do checkpoint
        model = GPT2LMHeadModel.from_pretrained(CHECKPOINT_DIR)
        
        # Carrega o estado do otimizador e o progresso
        try:
            checkpoint_data = torch.load(os.path.join(CHECKPOINT_DIR, 'training_state.pt'))
            start_epoch = checkpoint_data['epoch']
            global_step = checkpoint_data['global_step']
            print(f"Resuming from Epoch {start_epoch}, Global Step {global_step}")
        except FileNotFoundError:
            print("Warning: Model checkpoint found, but no 'training_state.pt'. Starting from epoch 0.")

    else:
        print("No checkpoint found. Starting training from scratch.")
        config = GPT2Config(
            vocab_size=tokenizer.vocab_size,
            n_positions=512,
            n_embd=320,
            n_layer=6,
            n_head=5,
        )
        model = GPT2LMHeadModel(config)
        model.resize_token_embeddings(len(tokenizer))

    print(f"Model loaded with {model.num_parameters():,} parameters.")

    dataset = JSONSchemaDataset(tokenizer, TRAINING_FILE_PATH, block_size=128)
    data_loader = DataLoader(dataset, batch_size=4, shuffle=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    model.to(device)
    
    optimizer = AdamW(model.parameters(), lr=1e-4)
    # Carrega o estado do otimizador se estiver no checkpoint
    if 'checkpoint_data' in locals():
        optimizer.load_state_dict(checkpoint_data['optimizer_state_dict'])

    print("Starting training loop...")
    model.train()
    for epoch in range(start_epoch, 5): # Loop começa do 'start_epoch'
        print(f"--- Epoch {epoch + 1} ---")
        for i, batch in enumerate(data_loader):
            # Lógica para pular passos já feitos nesta época (caso a restauração seja no meio de uma época)
            if global_step > 0 and (epoch * len(data_loader) + i) < global_step:
                continue

            inputs = batch.to(device)
            labels = inputs.clone()
            
            outputs = model(inputs, labels=labels)
            loss = outputs.loss
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            global_step += 1 # Incrementa o contador global de passos
            
            if global_step % 100 == 0:
                print(f"  Epoch {epoch + 1}, Step {global_step}, Loss: {loss.item()}")

            # --- Lógica para salvar o checkpoint ---
            if global_step % SAVE_EVERY_N_STEPS == 0:
                print(f"--- Saving checkpoint at step {global_step} ---")
                os.makedirs(CHECKPOINT_DIR, exist_ok=True)
                
                # Salva o modelo e o tokenizer
                model.save_pretrained(CHECKPOINT_DIR)
                tokenizer.save_pretrained(CHECKPOINT_DIR)
                
                # Salva o estado do otimizador e o progresso
                torch.save({
                    'epoch': epoch,
                    'global_step': global_step,
                    'optimizer_state_dict': optimizer.state_dict(),
                    'loss': loss.item(),
                }, os.path.join(CHECKPOINT_DIR, 'training_state.pt'))
                print("--- Checkpoint saved. ---")

    print("Training finished!")
    # O último checkpoint já é o modelo final
    print(f"Final model saved in {CHECKPOINT_DIR}")

if __name__ == '__main__':
    train_mini_gpt()