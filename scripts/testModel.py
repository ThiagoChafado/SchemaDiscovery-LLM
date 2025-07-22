
from transformers import GPT2Tokenizer, GPT2LMHeadModel

MODEL_PATH = './fine_tuned_model'

tokenizer = GPT2Tokenizer.from_pretrained(MODEL_PATH)
model = GPT2LMHeadModel.from_pretrained(MODEL_PATH)


test_json = """
{
    "id": 101,
    "name": "Laptop Pro",
    "in_stock": true,
    "price": 2500.00,
    "tags": ["electronics", "computer"]
}
"""


prompt = f"<|json|>{test_json}<|schema|>"

input_ids = tokenizer.encode(prompt, return_tensors='pt')
output = model.generate(
    input_ids,
    max_length=200, 
    num_beams=5,
    no_repeat_ngram_size=2,
    early_stopping=True
)

# Decode and print the result
generated_schema = tokenizer.decode(output[0], skip_special_tokens=True)
print("--- PROMPT ---")
print(prompt)
print("\n--- GENERATED SCHEMA ---")
print(generated_schema.split("<|schema|>")[1])