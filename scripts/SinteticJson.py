#!/usr/bin/env python3
import os
import json
import random
import time
from faker import Faker

fake = Faker()
OUTPUT_DIR = "datasets"

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
        "category": random.choice(["Electronic", "Food", "Clothes", "Books", "Furniture"]),
        "price": round(random.uniform(10, 2000), 2),
        "in_stock": random.choice([True, False]),
        "rating": round(random.uniform(1, 5), 1),
        "created_at": fake.date_this_decade().isoformat()
    }

def generate_transaction(transaction_id: int, person, products, max_items: int = 3):
    transaction = {
        "id": transaction_id,
        "person_id": person["id"],
        "date": fake.date_this_decade().isoformat(),
        "status": random.choice(["pending", "completed", "canceled"]),
        "payment_method": random.choice(["credit_card", "debit_card", "cash", "paypal"])
    }

    chosen_products = random.sample(products, k=random.randint(1, min(max_items, len(products))))

    transaction_items = []
    item_id = 1
    for product in chosen_products:
        quantity = random.randint(1, 5)
        item = {
            "id": item_id,
            "transaction_id": transaction_id,
            "product_id": product["id"],
            "quantity": quantity,
            "price": product["price"]
        }
        transaction_items.append(item)
        item_id += 1

    return transaction, transaction_items

def generate_json_array_by_size(size_mb: int, check_every: int = 50):
    """Gera um arquivo contendo um ARRAY JSON até atingir o tamanho em MB informado,
    seguindo o modelo relacional com persons, products, transactions e transaction_items.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    target_bytes = size_mb * 1024 * 1024
    file_path = os.path.join(OUTPUT_DIR, f"dataset_{size_mb}MB.json")

    if os.path.exists(file_path):
        os.remove(file_path)

    person_id = product_id = transaction_id = 1
    written = 0
    t0 = time.time()

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("[")
        first = True
        while True:
            person = generate_person(person_id)

            # Catálogo de produtos (cada transação escolhe os seus)
            products = [generate_product(product_id + i) for i in range(random.randint(2, 6))]
            product_id += len(products)

            transaction, items = generate_transaction(transaction_id, person, products)

            doc = {
                "person": person,
                "products": products,
                "transaction": transaction,
                "transaction_items": items
            }

            dumped = json.dumps(doc, ensure_ascii=False, separators=(',', ':'))
            if not first:
                f.write(",")
            f.write(dumped)

            first = False
            person_id += 1
            transaction_id += 1
            written += 1

            if written % check_every == 0:
                f.flush()
                os.fsync(f.fileno())
                size = os.path.getsize(file_path)
                elapsed = time.time() - t0
                print(f"[ARRAY] docs={written} tamanho={size/(1024*1024):.2f} MB estimado={elapsed:.1f}s")
                if size >= target_bytes:
                    break
        f.write("]")

    final_size = os.path.getsize(file_path) / (1024*1024)
    print(f"\n Gerado: {file_path}")
    print(f"  documentos: {written}")
    print(f"  tamanho final: {final_size:.2f} MB")

# Exemplo de uso:
generate_json_array_by_size(5)  # gera um JSON de ~5MB
