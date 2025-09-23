#!/usr/bin/env python3
import os
import json
import random
import argparse
import sys
from faker import Faker
import time

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
        "category": random.choice(["Eletronic", "Food", "Cloths", "Books", "Furniture"]),
        "price": round(random.uniform(10, 2000), 2),
        "in_stock": random.choice([True, False]),
        "rating": round(random.uniform(1, 5), 1),
        "created_at": fake.date_this_decade().isoformat()
    }

def generate_transaction(transaction_id: int, person, product):
    return {
        "id": transaction_id,
        "person_id": person["id"],
        "date": fake.date_this_decade().isoformat(),
        "status": random.choice(["pending", "completed", "canceled"]),
        "payment_method": random.choice(["credit_card", "debit_card", "cash", "paypal"]),
        "product_id": product["id"],
        "quantity": random.randint(1, 3),
        "price": product["price"]
    }

def generate_documents_by_size(target_size_mb: int,
                               output_filename: str,
                               check_every: int = 50,
                               jsonl: bool = False):
    """
    Gera um arquivo contendo um array JSON (ou JSONL se jsonl=True) até atingir
    target_size_mb. check_every define a frequência (em docs) de verificar o tamanho em disco.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    target_bytes = target_size_mb * 1024 * 1024
    file_path = os.path.join(OUTPUT_DIR, output_filename)

    # Remove arquivo anterior se existir
    if os.path.exists(file_path):
        os.remove(file_path)

    person_id = 1
    product_id = 1
    transaction_id = 1
    written = 0
    t0 = time.time()

    # JSONL mode: um JSON por linha, começando por '{'
    if jsonl:
        with open(file_path, "w", encoding="utf-8") as f:
            while True:
                person = generate_person(person_id)
                product = generate_product(product_id)
                transaction = generate_transaction(transaction_id, person, product)
                doc = {"person": person, "product": product, "transaction": transaction}
                f.write(json.dumps(doc, ensure_ascii=False, separators=(',', ':'), default=str) + "\n")

                person_id += 1; product_id += 1; transaction_id += 1
                written += 1

                if written % check_every == 0:
                    f.flush()
                    os.fsync(f.fileno())
                    size = os.path.getsize(file_path)
                    print(f"[JSONL] docs={written} size={size/(1024*1024):.2f} MB")
                    if size >= target_bytes:
                        break
    else:
        # JSON array mode: write '[' then objects separated by ',' then ']'
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("[")
            first = True
            while True:
                person = generate_person(person_id)
                product = generate_product(product_id)
                transaction = generate_transaction(transaction_id, person, product)
                doc = {"person": person, "product": product, "transaction": transaction}

                dumped = json.dumps(doc, ensure_ascii=False, separators=(',', ':'), default=str)
                if not first:
                    f.write(",")
                f.write(dumped)

                person_id += 1; product_id += 1; transaction_id += 1
                written += 1
                first = False

                if written % check_every == 0:
                    f.flush()
                    os.fsync(f.fileno())
                    size = os.path.getsize(file_path)
                    elapsed = time.time() - t0
                    print(f"[ARRAY] docs={written} size={size/(1024*1024):.2f} MB elapsed={elapsed:.1f}s")
                    if size >= target_bytes:
                        break

            f.write("]")  # fecha o array

    final_size = os.path.getsize(file_path) / (1024*1024)
    print(f"\n✔ Gerado: {file_path}")
    print(f"  documentos: {written}")
    print(f"  tamanho final: {final_size:.2f} MB")

def parse_args():
    p = argparse.ArgumentParser(description="Gerador sintético por tamanho (MB)")
    p.add_argument("size_mb", type=int, help="tamanho alvo em MB do arquivo gerado")
    p.add_argument("--out", "-o", default=None, help="nome do arquivo de saída (opcional)")
    p.add_argument("--jsonl", action="store_true", help="gera JSONL (um objeto por linha) em vez de array")
    p.add_argument("--check-every", type=int, default=50, help="verifica tamanho a cada N documentos (padrão=50)")
    return p.parse_args()

if __name__ == "__main__":
    args = parse_args()
    size_mb = args.size_mb
    filename = args.out if args.out else f"dataset_{size_mb}MB.jsonl" if args.jsonl else f"dataset_{size_mb}MB.json"
    generate_documents_by_size(size_mb, filename, check_every=args.check_every, jsonl=args.jsonl)
