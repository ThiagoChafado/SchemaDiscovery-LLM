# scripts/test_my_model.py
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import json

# --- Configuration ---
MODEL_PATH = 'training_checkpoints' # O modelo final é o último checkpoint

def testModel():
    print(f"Carregando modelo e tokenizer de '{MODEL_PATH}'...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        model = AutoModelForCausalLM.from_pretrained(MODEL_PATH)
    except OSError:
        print(f"ERRO: Modelo não encontrado em '{MODEL_PATH}'.")
        return
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()

    sampleJson = {
        "ID": 12513,
        "product": "pen",
        "Test": False,
        "price": 3.59
    }
    sampleJsonString = json.dumps(sampleJson, indent=4)

    instruction = "INSTRUÇÃO: Gere o esquema para o JSON a seguir."
    jsonHeader = "### JSON:"
    schemaHeader = "### Esquema:"
    prompt = (
        f"{instruction}\n"
        f"{jsonHeader}\n{sampleJsonString}\n"
        f"{schemaHeader}\n"
    )
    print("\n--- PROMPT DE ENTRADA ---")
    print(prompt)

    inputIds = tokenizer.encode(prompt, return_tensors='pt').to(device)
    print("\n--- Gerando Esquema... ---")
    
    outputIds = model.generate(
        inputIds,
        max_length=512,
        num_beams=5,
        early_stopping=True,
        pad_token_id=tokenizer.eos_token_id
    )

    fullGeneratedText = tokenizer.decode(outputIds[0], skip_special_tokens=True)
    try:
        schemaPartRaw = fullGeneratedText.split(schemaHeader)[1].strip()
        parsedSchema = json.loads(schemaPartRaw)
        prettySchema = json.dumps(parsedSchema, indent=4)
        print("\n--- Esquema Gerado (Formatado) ---")
        print(prettySchema)
    except (IndexError, json.JSONDecodeError) as e:
        print("\n--- Esquema Gerado (Bruto) ---")
        print(f"(Não foi possível formatar o JSON. Erro: {e})")
        print(fullGeneratedText[len(prompt):])

if __name__ == '__main__':
    testModel()