def apply_rules(entities):
    rules = {
        "DATE": lambda x: True if len(x) >= 6 else False,
        "MONEY": lambda x: x.replace(".", "", 1).isdigit()
    }

    validated = []
    for ent in entities:
        rule = rules.get(ent["label"])
        if rule:
            ent["valid"] = rule(ent["text"])
        else:
            ent["valid"] = None
        validated.append(ent)

    return validated
