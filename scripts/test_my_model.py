
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import json

# --- Configuration --- 
MODEL_PATH = 'training_checkpoints'

def test_model():
    """
    Loads the custom-trained model and uses it to generate a JSON schema
    from a sample JSON input.
    """
    print(f"Carregando modelo e tokenizer de '{MODEL_PATH}'...")
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        model = AutoModelForCausalLM.from_pretrained(MODEL_PATH)
    except OSError:
        print(f"ERRO: Modelo não encontrado em '{MODEL_PATH}'.")
        print("Verifique se o caminho está correto e se o treinamento foi concluído com sucesso.")
        return

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval() # Coloca o modelo em modo de avaliação (importante para inferência)

    # --- Crie aqui o JSON que você quer testar ---
    # Use um JSON que o modelo NUNCA viu durante o treinamento.
    sample_json = {
        "user_id": 123,
        "product": "Caneta",
        "in_stock": True,
        "price": 3.59
    }
    # Converte o dicionário Python para uma string JSON formatada
    sample_json_string = json.dumps(sample_json, indent=4)

    # --- Preparação do Prompt ---
    # O prompt deve ter exatamente o mesmo formato usado no treinamento
    prompt = f"<|json|>{sample_json_string}<|schema|>"

    print("\n--- JSON de Entrada ---")
    print(sample_json_string)

    # Tokeniza o prompt e o envia para o dispositivo (CPU ou GPU)
    input_ids = tokenizer.encode(prompt, return_tensors='pt').to(device)

    print("\n--- Gerando Esquema... ---")
    
    # --- Geração do Texto ---
    # model.generate() é a função que faz a mágica acontecer
    output_ids = model.generate(
        input_ids,
        max_length=128,          # Comprimento máximo da resposta
        num_beams=5,             # Usa "beam search" para melhores resultados
        early_stopping=True,     # Para de gerar quando o modelo acha que terminou
        repetition_penalty=1.5, # Penaliza repetições
        temperature=0.5,      # Deixa a saída mais focada
        pad_token_id=tokenizer.eos_token_id # Importante para geração com GPT
    )

    # Decodifica os tokens gerados de volta para texto
    full_generated_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)

    # --- Pós-processamento e Exibição ---
    try:
        # Extrai apenas a parte do esquema que foi gerada
        schema_part_raw = full_generated_text.split("<|schema|>")[1]
        
        # Tenta formatar o resultado como um JSON bonito
        parsed_schema = json.loads(schema_part_raw)
        pretty_schema = json.dumps(parsed_schema, indent=4)
        
        print("\n--- Esquema Gerado (Formatado) ---")
        print(pretty_schema)
    except (IndexError, json.JSONDecodeError) as e:
        # Se a formatação falhar, mostra o resultado bruto
        print("\n--- Esquema Gerado (Bruto) ---")
        print(f"(Não foi possível formatar o JSON. Erro: {e})")
        # Mostra o texto bruto gerado após o prompt
        print(full_generated_text[len(prompt):])


if __name__ == '__main__':
    test_model()