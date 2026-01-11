import os
import json
import itertools

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "drug_interactions")

# ---------- LOAD JSON FILES ----------

def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)

INTERACTIONS = load_json("interactions.json")
INTERACTIONS_SPECIFIC = load_json("interactions_specific.json")
DRUG_CLASSES = load_json("drug_classes.json")
DRUG_FOOD = load_json("drug_food_interactions.json")
PATIENT_ALERTS = load_json("patient_alerts.json")


# ---------- HELPERS ----------

def normalize(name: str) -> str:
    return (
        name.lower()
        .strip()
        .replace(" ", "_")
        .replace("+", "_")
    )


# ---------- DRUG–DRUG INTERACTIONS ----------

def check_interaction(drugs):
    results = []
    normalized = [normalize(d) for d in drugs]

    for a, b in itertools.combinations(normalized, 2):
        key1 = f"{a}+{b}"
        key2 = f"{b}+{a}"

        rule = (
            INTERACTIONS_SPECIFIC.get(key1)
            or INTERACTIONS_SPECIFIC.get(key2)
            or INTERACTIONS.get(key1)
            or INTERACTIONS.get(key2)
        )

        if rule:
            results.append({
                "medicine1": a,
                "medicine2": b,
                "severity": rule.get("severity", "moderate"),
                "description": rule.get("description", ""),
                "recommendation": rule.get(
                    "recommendation",
                    "Consult a healthcare professional."
                )
            })

    return results


# ---------- PATIENT ALERTS (pregnancy / renal / liver) ----------

def get_patient_alerts(drugs, conditions):
    alerts = []

    for drug in drugs:
        d = normalize(drug)
        drug_class = DRUG_CLASSES.get(d)

        if not drug_class:
            continue

        for condition in conditions:
            rule = PATIENT_ALERTS.get(condition, {}).get(drug_class)
            if rule:
                alerts.append({
                    "drug": d,
                    "condition": condition,
                    "severity": "warning",
                    "message": rule
                })

    return alerts


# ---------- DRUG–FOOD ALERTS ----------

def get_food_interactions(drugs):
    alerts = []

    for drug in drugs:
        d = normalize(drug)
        rule = DRUG_FOOD.get(d)

        if rule:
            alerts.append({
                "drug": d,
                "food": rule.get("food"),
                "severity": rule.get("severity", "moderate"),
                "message": rule.get("description")
            })

    return alerts
