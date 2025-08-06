# scripts/simplify_schemas.py
import os
import json

# --- Configuração ---

# Pasta de entrada com seus esquemas complexos
INPUT_SCHEMAS_DIR = 'master_schemas'

# Nova pasta de saída para os esquemas simplificados
OUTPUT_SCHEMAS_DIR = 'master_schemas_minimal'

# Lista de palavras-chave ESTRUTURAIS que queremos manter.
# Todo o resto será descartado.
ALLOWED_KEYWORDS = {
    # Tipos e Estrutura Principal
    "type",
    "properties",
    "items",
    "required",
    
    # Estruturas Condicionais e de Referência
    "oneOf",
    "anyOf",
    "allOf",
    "$ref",
    "$defs",
    "definitions" # Usado em esquemas mais antigos
}

def simplify_schema(data):
    """
    Função recursiva que percorre um objeto de esquema e mantém
    apenas as palavras-chave estruturais permitidas.
    """
    if isinstance(data, dict):
        # Cria um novo dicionário contendo apenas as chaves permitidas
        new_dict = {}
        for key, value in data.items():
            if key in ALLOWED_KEYWORDS:
                # Se a chave é permitida, processa o valor recursivamente
                new_dict[key] = simplify_schema(value)
        return new_dict
    
    elif isinstance(data, list):
        # Se for uma lista, processa cada item recursivamente
        return [simplify_schema(item) for item in data]
    
    else:
        # Mantém valores que não são dicionários ou listas (ex: "string", "object")
        return data

def process_all_schemas():
    """
    Encontra todos os esquemas na pasta de entrada, os simplifica e
    salva na pasta de saída.
    """
    print(f"--- Iniciando a simplificação de esquemas ---")
    
    if not os.path.exists(INPUT_SCHEMAS_DIR):
        print(f"ERRO: A pasta de entrada '{INPUT_SCHEMAS_DIR}' não foi encontrada.")
        return
        
    os.makedirs(OUTPUT_SCHEMAS_DIR, exist_ok=True)
    
    schema_files = [f for f in os.listdir(INPUT_SCHEMAS_DIR) if f.endswith('.json')]
    print(f"Encontrados {len(schema_files)} esquemas para processar.")

    for filename in schema_files:
        input_path = os.path.join(INPUT_SCHEMAS_DIR, filename)
        output_path = os.path.join(OUTPUT_SCHEMAS_DIR, filename)
        
        print(f"  -> Processando: {filename}")
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                original_schema = json.load(f)
            
            # Chama a função principal de simplificação
            minimal_schema = simplify_schema(original_schema)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(minimal_schema, f, indent=4)
                
        except Exception as e:
            print(f"     ERRO ao processar o arquivo {filename}: {e}")
            
    print(f"\n[SUCESSO] Processo concluído!")
    print(f"Esquemas simplificados foram salvos em: '{OUTPUT_SCHEMAS_DIR}'")

if __name__ == '__main__':
    process_all_schemas()