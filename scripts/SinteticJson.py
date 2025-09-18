import os
import json
import random
from faker import Faker
fake = Faker()
# --- Configurações ---
OUTPUT_DIR =  "datasets/"
QUANTITY = 1000  # número de objetos que serão gerados
# ---------------------

# --- Geradores de objetos ---


def generate_person():
    return {
        "id": random.randint(1, 999999),
        "name": fake.name() if random.random() > 0.1 else None,
        "email": fake.email() if random.random() > 0.2 else None,
        "age": random.choice([random.randint(18, 80), None]),
        "phone": fake.phone_number() if random.random() > 0.3 else None,
        "address": {
            "street": fake.street_name() if random.random() > 0.1 else None,
            "city": fake.city(),
            "state": fake.state_abbr(),
            "postcode": fake.postcode(),
            "country": fake.country(),
        } if random.random() > 0.2 else None,
        "job": fake.job() if random.random() > 0.3 else None,
        "company": fake.company() if random.random() > 0.4 else None,
        "bio": fake.text(max_nb_chars=200) if random.random() > 0.5 else None,
        "website": fake.url() if random.random() > 0.4 else None,
        "social_profiles": {
            "twitter": f"https://twitter.com/{fake.user_name()}" if random.random() > 0.5 else None,
            "linkedin": f"https://linkedin.com/in/{fake.user_name()}" if random.random() > 0.5 else None,
            "facebook": f"https://facebook.com/{fake.user_name()}" if random.random() > 0.5 else None,
        } if random.random() > 0.3 else None
        
    }

def generate_product():
    return {
        "id": fake.ean13(),
        "prodname": fake.word(),
        "price": float(round(random.uniform(5, 5000), 2)),
        "stock": random.choice([random.randint(0, 1000), None]),
        "category": random.choice(["Eletrônicos", "Alimentos", "Roupas", None]),
        "description": fake.sentence() if random.random() > 0.2 else None,
        "tags": [fake.word() for _ in range(random.randint(1, 5))] if random.random() > 0.3 else None,
        "dimensions": {
            "length": round(random.uniform(1, 100), 2),
            "width": round(random.uniform(1, 100), 2),
            "height": round(random.uniform(1, 100), 2),
        } if random.random() > 0.4 else None,
        "weight": round(random.uniform(0.1, 50), 2) if random.random() > 0.4 else None,
        "manufacturer": fake.company() if random.random() > 0.2 else None,
        "warranty_years": random.choice([0, 1, 2, 3, None]),
        "release_date": fake.date_this_decade().isoformat() if random.random() > 0.3 else None,
        "rating": round(random.uniform(1, 5), 1) if random.random() > 0.5 else None,
        "reviews": [fake.sentence() for _ in range(random.randint(0, 10))] if random.random() > 0.5 else None,
        "available": random.choice([True, False, None])
    }

def generate_location():
    return {
        "id": random.randint(1000, 9999),
        "street": fake.street_name() if random.random() > 0.1 else None,
        "city": fake.city(),
        "state": fake.state_abbr(),
        "postcode": fake.postcode(),
        "latitude": float(fake.latitude()) if random.random() > 0.2 else None,
        "longitude": float(fake.longitude()) if random.random() > 0.2 else None,
        "country": fake.country(),
        "timezone": fake.timezone() if random.random() > 0.3 else None,
        "building_number": fake.building_number() if random.random() > 0.4 else None,
        "complement": fake.secondary_address() if random.random() > 0.5 else None,
        "neighborhood": fake.city_suffix() if random.random() > 0.3 else None,
        "county": fake.city() if random.random() > 0.4 else None,
        "region": fake.state() if random.random() > 0.2 else None,
        "population": random.choice([random.randint(1000, 1000000), None]),
        "elevation": round(random.uniform(0, 3000), 2) if random.random() > 0.5 else None,
        "area_km2": round(random.uniform(1, 10000), 2) if random.random() > 0.5 else None
    }

def generate_transaction():
    return {
        "id": random.randint(10000, 99999),
        "value": round(random.uniform(50, 2000), 2),
        "currency": random.choice(["BRL", "USD", "EUR"]),
        "date": fake.date_this_decade().isoformat(),
        "status": random.choice(["pending", "completed", "canceled"]),
        "payment_method": random.choice(["credit_card", "debit_card", "paypal", "bank_transfer"]),
        "customer_id": random.randint(1, 999999),
        "items": [
            {
                "product_id": fake.ean13(),
                "quantity": random.randint(1, 5),
                "price": round(random.uniform(5, 500), 2)
            } for _ in range(random.randint(1, 5))
        ] if random.random() > 0.2 else None,
        "shipping_address": {
            "street": fake.street_name(),
            "city": fake.city(),
            "state": fake.state_abbr(),
            "postcode": fake.postcode(),
            "country": fake.country(),
        } if random.random() > 0.3 else None,
        "billing_address": {
            "street": fake.street_name(),
            "city": fake.city(),
            "state": fake.state_abbr(),
            "postcode": fake.postcode(),
            "country": fake.country(),
        } if random.random() > 0.3 else None,
        "discount_code": fake.word() if random.random() > 0.5 else None 
        
    }

def generate_event():
    return {
        "id": random.randint(100000, 999999),
        "name": fake.sentence(nb_words=3),
        "date": fake.date_this_century().isoformat(),
        "city": fake.city(),
        "participants": [fake.name() for _ in range(random.randint(1, 5))],
        "location": {
            "venue": fake.company() if random.random() > 0.2 else None,
            "address": fake.street_name() if random.random() > 0.3 else None,
            "latitude": fake.latitude() if random.random() > 0.4 else None,
            "longitude": fake.longitude() if random.random() > 0.4 else None,
        } if random.random() > 0.3 else None,
        "description": fake.text(max_nb_chars=200) if random.random() > 0.5 else None,
        "type": random.choice(["conference", "meetup", "workshop", "webinar", None]),
        "organizer": fake.company() if random.random() > 0.2 else None,
        "website": fake.url() if random.random() > 0.4 else None,
        "tickets_sold": random.choice([random.randint(0, 1000), None]),
        "is_virtual": random.choice([True, False, None])
    }




# Lista de geradores
GENERATORS = [
    generate_person,
    generate_product,
    generate_location,
    generate_transaction,
    generate_event,
]


# --- Função principal ---
def generate_json_documents(quantity=1000):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for i in range(1, quantity + 1):
        generator = random.choice(GENERATORS)
        json_object = generator()

        # remove chaves None para simular "sujeira"
        json_object = {k: v for k, v in json_object.items() if v is not None}

        file_path = os.path.join(OUTPUT_DIR, f"data_{i}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(json_object, f, ensure_ascii=False, indent=2)

        if i % 200 == 0:
            print(f"{i} documentos gerados...")

    print(f"\n {quantity} documentos JSON individuais foram salvos em '{OUTPUT_DIR}'.")


if __name__ == "__main__":
    generate_json_documents(1000)  


