import os
import json
import random
from faker import Faker

fake = Faker()
# --- Configurações ---
OUTPUT_DIR = "datasets/sintetic"
# ---------------------

def generate_person(person_id: int):
    return {
        "id": person_id,
        "name": fake.name(),
        "email": fake.email() if random.random() > 0.2 else None,
        "age": random.randint(18, 80),
        "phone": fake.phone_number() if random.random() > 0.3 else None,
        "city": fake.city(),
        "state": fake.state_abbr(),
        "registered_at": fake.date_this_decade().isoformat()
    }

def generate_product(product_id: int):
    return {
        "id": product_id,
        "name": fake.word().capitalize(),
        "category": random.choice(["Eletronic", "Food", "Cloths", "Books", "Furniture"]),
        "price": round(random.uniform(10, 2000), 2),
        "in_stock": random.choice([True, False]),
        "rating": round(random.uniform(1, 5), 1),
        "created_at": fake.date_this_decade().isoformat()
    }

def generate_transaction(transaction_id: int, persons, products):
    person = random.choice(persons)
    items = []
    for _ in range(random.randint(1, 2)):  # máximo 2 itens pra não crescer demais
        product = random.choice(products)
        items.append({
            "product_id": product["id"],
            "quantity": random.randint(1, 3),
            "price": product["price"]
        })

    return {
        "id": transaction_id,
        "person_id": person["id"],
        "date": fake.date_this_decade().isoformat(),
        "status": random.choice(["pending", "completed", "canceled"]),
        "payment_method": random.choice(["credit_card", "debit_card", "cash", "paypal"]),
        "items": items
    }

def generate_database():
    # controlamos o tamanho para dar ~100 linhas, fica melhor para nao extrapolar o contexto
    num_persons = random.randint(5, 8)
    num_products = random.randint(5, 8)
    num_transactions = random.randint(5, 10)

    persons = [generate_person(i) for i in range(1, num_persons + 1)]
    products = [generate_product(i) for i in range(1, num_products + 1)]
    transactions = [generate_transaction(i, persons, products) for i in range(1, num_transactions + 1)]

    db = {
        "persons": persons,
        "products": products,
        "transactions": transactions
    }

    # remover None pra dar "sujeira"
    def clean_dict(d):
        return {k: v for k, v in d.items() if v is not None}

    db["persons"] = [clean_dict(p) for p in db["persons"]]
    db["products"] = [clean_dict(p) for p in db["products"]]
    db["transactions"] = [clean_dict(t) for t in db["transactions"]]

    return db

def generate_json_documents(size):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    total_size = 0
    i = 1
    while total_size < size * 1024 * 1024:
        db = generate_database()
        file_path = os.path.join(OUTPUT_DIR, f"database_{i}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        file_size = os.path.getsize(file_path)
        total_size += file_size

        print(f"Documento {i} salvo: {file_path} ({file_size} bytes)")
        i += 1

    print(f"\n{total_size // (1024 * 1024)} MB de documentos JSON foram salvos em '{OUTPUT_DIR}'.")

if __name__ == "__main__":
    generate_json_documents(5)  # exemplo: 5 mb
