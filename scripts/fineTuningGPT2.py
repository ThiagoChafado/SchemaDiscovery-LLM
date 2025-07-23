import torch
# AutoTokenizer e AutoModelForCausalLM: Classes flexíveis que podem carregar
# qualquer modelo compatível da família GPT, como o 'distilgpt2'.
# LoraConfig, get_peft_model: As ferramentas da biblioteca PEFT para implementar o LoRA.
from transformers import (
    AutoTokenizer, # Usar AutoTokenizer para mais flexibilidade
    AutoModelForCausalLM, # Usar AutoModel para carregar com bitsandbytes
    TextDataset,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments
)
from peft import LoraConfig, get_peft_model 
import os

MODEL_NAME = "distilgpt2" 
TRAINING_FILE_PATH = 'datasets/training_data.txt'
OUTPUT_DIR = './results_lora'
FINE_TUNED_MODEL_PATH = './fine_tuned_model_lora'

JSON_START_TOKEN = "<|json|>"
SCHEMA_START_TOKEN = "<|schema|>"

  # --- 1. Carregamento do Tokenizer ---
    # `AutoTokenizer.from_pretrained(MODEL_NAME)`: Baixa o tokenizer que foi
    # originalmente treinado com o distilgpt2. Ele já "entende" a língua inglesa.
    # `tokenizer.add_special_tokens(...)`: Adicionamos nossos marcadores
    # (<|json|>, <|schema|>) ao vocabulário existente para que o modelo aprenda nossa tarefa.

    # --- 2. Carregamento e Otimização do Modelo ---
    # `AutoModelForCausalLM.from_pretrained(...)`: Baixa o modelo distilgpt2
    # com seus 82 milhões de parâmetros já treinados.
    #
    # Parâmetros Chave para Economia de Memória:
    # `load_in_8bit=True`: Esta é a "Quantização". Ele carrega o modelo usando
    # números de 8 bits em vez de 32 bits, reduzindo o uso de memória do modelo em ~75%.
    # `device_map='auto'`: Ajuda a gerenciar a alocação de memória.

    # `model.resize_token_embeddings(len(tokenizer))`: Atualiza a camada de entrada do
    # modelo para que ele reconheça os novos tokens que adicionamos.

    # --- 3. Configuração do LoRA ---
    # `LoraConfig(...)`: Cria a "planta" do nosso "chip de performance".
    # `r=8`: Define o quão complexo (e grande) será o nosso "chip". 8 é um valor
    # pequeno e eficiente.
    # `task_type="CAUSAL_LM"`: Informa ao LoRA que estamos adaptando um modelo
    # de linguagem causal (que prevê a próxima palavra), como o GPT.

    # --- 4. Aplicação do LoRA no Modelo ---
    # `model = get_peft_model(model, lora_config)`: Este é o passo mágico.
    # Ele "congela" todos os 82 milhões de parâmetros do distilgpt2 e injeta
    # as pequenas camadas LoRA treináveis no modelo.
    # `model.print_trainable_parameters()`: Mostra a prova do sucesso da técnica.
    # Ele exibirá que, em vez de 82 milhões, estamos treinando apenas algumas
    # centenas de milhares de parâmetros (~0.2% do total).

    # --- 5. Preparação dos Dados e do Treinador ---
    # `TextDataset(...)` e `DataCollatorForLanguageModeling(...)`: Carregam
    # o mesmo arquivo `training_data.txt` e o preparam em lotes, da mesma
    # forma que no script de treinamento do zero.
    # `TrainingArguments(...)`: Configura os parâmetros do treinamento, como
    # número de épocas, tamanho do lote e, crucialmente, a acumulação de gradientes
    # para economizar memória.
    # `Trainer(...)`: Inicializa o "treinador" da Hugging Face, que automatiza
    # todo o loop de treinamento para nós.

    # --- 6. Treinamento e Salvamento ---
    # `trainer.train()`: Inicia o processo de fine-tuning. Durante este passo,
    # apenas os pesos do "chip" LoRA são atualizados. O motor principal do GPT-2 permanece intocado.
    # `trainer.save_model(...)`: Ao final, salva apenas os pesos do adaptador LoRA.
    # O resultado é uma pasta de modelo muito pequena (poucos megabytes), em vez
    # dos centenas de megabytes do modelo original completo.

def fineTuneModelWithLoRA(device):
    print(f"Starting LoRA fine-tuning for model: {MODEL_NAME}")

    # 1. Load tokenizer e adicione os tokens especiais
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    special_tokens_dict = {'additional_special_tokens': [JSON_START_TOKEN, SCHEMA_START_TOKEN]}
    tokenizer.add_special_tokens(special_tokens_dict)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 2. Load model com quantização em 8-bits para economizar memória
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        load_in_8bit=True,
        device_map='auto', # Distribui o modelo automaticamente (útil para GPU)
    )
    model.resize_token_embeddings(len(tokenizer))

    # 3. Defina a configuração do LoRA
    lora_config = LoraConfig(
        r=8, # A dimensão do "chip". 8 é um bom valor inicial.
        lora_alpha=32, # Parâmetro de escala
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )

    # 4. Aplique o LoRA ao modelo
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # 5. Crie o dataset
    train_dataset = TextDataset(
        tokenizer=tokenizer,
        file_path=TRAINING_FILE_PATH,
        block_size=32  #Diminuir o tamanho do bloco para reduzir o uso de memória
    )
    
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False
    )
    
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        overwrite_output_dir=True,
        num_train_epochs=3,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        # fp16=True, # Não é necessário com bitsandbytes
        logging_steps=100,
        save_total_limit=2,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=train_dataset,
    )

    # Corrigir um bug do PEFT com o Trainer
    model.config.use_cache = False

    print("Training with LoRA is starting. This should be much lighter on memory.")
    trainer.train()
    print("Training finished!")

    print(f"Saving fine-tuned LoRA model to {FINE_TUNED_MODEL_PATH}")
    trainer.save_model(FINE_TUNED_MODEL_PATH)
    tokenizer.save_pretrained(FINE_TUNED_MODEL_PATH)

if __name__ == '__main__':
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    fineTuneModelWithLoRA(device)