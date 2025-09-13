# 📌 SchemaDiscovery-LLM

Projeto de **TCC** voltado para a **extração de esquemas de coleções JSON** utilizando **LLMs (Large Language Models)**.  

---

## 📂 Estrutura de Diretórios

├── datasets # Conjunto de dados originais
├── processed # Dados processados
│ ├── coleção_1
│ ├── coleção_2
│ └── ...
├── SaidasGemma3 # Saídas geradas pelo modelo Gemma
├── saidastreinamentos # Resultados de treinamentos
├── schema_documents # Documentos de esquemas extraídos
└── scripts # Scripts auxiliares do projeto

---

## ⚙️ Pipeline do Projeto

1. **Entrada**: um arquivo JSON `J` representando múltiplos documentos.  
2. **Amostragem**: extração de `n` documentos de `J`, cada um com tamanho aproximado `T`, gerando os subconjuntos `j1, j2, ..., jn`.  
3. **LLM**: cada `ji` é utilizado como entrada em uma **IA Generativa**, que propõe esquemas `e1, e2, ..., en`.  
4. **Fusão (LLM)**: os esquemas gerados são fusionados, resultando em um esquema consolidado `E`.  
5. **Ferramenta Tradicional**: os mesmos subconjuntos `ji` são processados por uma API de extração de esquemas (ex.: **Genson**), gerando `eg1, eg2, ..., egn`.  
6. **Fusão (Tradicional)**: os esquemas extraídos via ferramenta são fusionados em `Eg`.  
7. **Comparação**: comparação entre `E` (LLM) e `Eg` (tradicional), utilizando uma métrica de similaridade a ser definida.  

---

## 🚀 Objetivo

Comparar e avaliar a **eficácia de LLMs** frente a ferramentas tradicionais de extração de esquemas JSON, propondo métricas de análise e benchmarks.

---

## 📌 Status

- [ ] Definição da métrica de comparação  
- [ ] Implementação da fusão de esquemas  
- [ ] Integração com APIs externas (ex.: Genson)  
- [ ] Avaliação experimental  

---

## 👨‍💻 Autor

Thiago Chafado Almeida  
Curso de Ciência da Computação — UFFS Chapecó 