import json
import time
from openai import OpenAI
import ijson
import gc
from decimal import Decimal

# --- CONFIGURAÇÕES ---
CLIENTE_OPENAI = OpenAI(base_url="http://localhost:1234/v1", api_key="not-needed")
NOME_DO_MODELO = "gemma:2b" 
ARQUIVO_ENTRADA = 'datasets/twitter_reduzido.json'
ARQUIVO_SAIDA = 'datasets/esquemas_extraidos.txt'
# --- FIM DAS CONFIGURAÇÕES ---

def contar_objetos_no_json(arquivo_entrada):
    """
    Conta de forma eficiente o número de objetos em uma lista JSON
    sem carregar o arquivo inteiro na memória.
    """
    print(f"Iniciando a contagem de objetos em '{arquivo_entrada}'...")
    try:
        with open(arquivo_entrada, 'rb') as f:
            # ijson.items encontra cada objeto na lista ('item')
            # sum(1 for _ in objetos) itera sobre eles e conta sem armazená-los
            contador = sum(1 for _ in ijson.items(f, 'item'))
        print(f"Contagem finalizada. Total de objetos encontrados: {contador}")
        return contador
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{arquivo_entrada}' não encontrado para contagem.")
        return 0
    except Exception as e:
        print(f"ERRO durante a contagem: {e}")
        return 0

def decimal_converter(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def extrair_esquema_de_objeto(objeto_json, tentativas_max=3, tempo_espera=5):
    try:
        objeto_str = json.dumps(
            objeto_json,
            ensure_ascii=False,
            indent=2,
            default=decimal_converter
        )
    except TypeError as e:
        print(f"  -> ERRO: Não foi possível serializar o objeto para JSON. Erro: {e}")
        return f"ERRO DE SERIALIZAÇÃO: {e}"

    prompt = (
        "Give me the JSON Schema for this JSON Object. Only the schema, without further explanation.\n\n"
        f"JSON Object:\n{objeto_str}\n\nSchema:"
    )

    tentativas = 0
    while tentativas < tentativas_max:
        try:
            completion = CLIENTE_OPENAI.chat.completions.create(
                model=NOME_DO_MODELO,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            esquema = completion.choices[0].message.content
            return esquema.strip()
        except Exception as e:
            tentativas += 1
            print(f"  -> Tentativa {tentativas}/{tentativas_max} falhou. Erro: {e}. Aguardando {tempo_espera}s...")
            time.sleep(tempo_espera)
            if tentativas == tentativas_max:
                print(f"  -> ERRO: Não foi possível processar o objeto após {tentativas_max} tentativas.")
                return f"ERRO AO PROCESSAR OBJETO: {e}"
    return None

def processar_arquivo_json_grande(arquivo_entrada, arquivo_saida, total_objetos):
    """
    Processa o arquivo JSON em streaming e extrai os esquemas.
    """
    print(f"\nIniciando a extração de esquemas de {total_objetos} objetos...")
    print(f"Os resultados serão salvos em '{arquivo_saida}'.")
    
    contador_processado = 0
    with open(arquivo_entrada, 'rb') as f_in, \
         open(arquivo_saida, 'w', encoding='utf-8') as f_out:
        
        objetos = ijson.items(f_in, 'item')

        for obj in objetos:
            contador_processado += 1
            print(f"\nProcessando objeto {contador_processado} de {total_objetos}...")

            esquema = extrair_esquema_de_objeto(obj)
            
            if esquema:
                f_out.write(f"--- Esquema para o Objeto #{contador_processado} ---\n")
                f_out.write(esquema)
                f_out.write("\n\n")
                f_out.flush()
                print(f"  -> Esquema #{contador_processado} salvo com sucesso.")
    
    print(f"\n--- Processamento Concluído! ---")
    print(f"Foram processados {contador_processado} objetos.")


if __name__ == "__main__":
    # 1. Primeiro, apenas conta os objetos
    total_objetos = contar_objetos_no_json(ARQUIVO_ENTRADA)

    # 2. Se encontrou objetos, inicia o processamento com o LLM
    if total_objetos > 0:
        # Pergunta ao usuário se deseja continuar
        resposta = input(f"Deseja iniciar o processamento dos {total_objetos} objetos com o LLM? (s/n): ").lower()
        if resposta == 's':
            processar_arquivo_json_grande(ARQUIVO_ENTRADA, ARQUIVO_SAIDA, total_objetos)
        else:
            print("Processamento cancelado pelo usuário.")
    else:
        print("Nenhum objeto encontrado ou erro na leitura. O processamento com o LLM não será iniciado.")