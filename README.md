# 📌 SchemaDiscovery-LLM

Projeto de **TCC** voltado para a **extração de esquemas de coleções JSON** utilizando **LLMs (Large Language Models)**.  

---

## 📂 Estrutura de Diretórios

    - datasets # Conjunto de dados originais
    - processed # Dados processados
        - coleção_1
        - coleção_2
        - ...
    - saidastreinamentos # Resultados de treinamentos
    - scripts # Scripts auxiliares do projeto

---

## ⚙️ Pipeline do Projeto

1. **Entrada**: um arquivo JSON `J` representando múltiplos documentos.  
2. **Amostragem**: extração de `n` documentos de `J`, cada um com tamanho aproximado `T`, gerando os subconjuntos `j1, j2, ..., jn`.  
3. **LLM**: cada `ji` é utilizado como entrada em uma **IA Generativa**, que propõe esquemas `e1, e2, ..., en`.  
4. **Fusão (LLM)**: os esquemas gerados são fusionados, resultando em um esquema consolidado `E`.  
5. **Validação**: Valida os esquemas mestres fusionados com o **AJV**, um validador de JsonSchemas JavaScript
---

## 🚀 Objetivo

Comparar e avaliar a **eficácia de LLMs** na tarefa de extrair esquemas


---

## 👨‍💻 Autor

Thiago Chafado Almeida  
Curso de Ciência da Computação — UFFS Chapecó
