CUISINE_AFFINITY = {
    # Tier 1: Alta afinidad con embutidos (0.80-1.00)
    "alemana": 1.0, "german": 1.0,
    "hamburguesas": 1.0, "burgers": 1.0,
    "pizza": 0.95, "pizzeria": 0.95,
    "italiana": 0.90, "italian": 0.90,
    "sandwiches": 0.90, "deli": 0.95,
    "comida rapida": 0.85, "fast food": 0.85,
    "americana": 0.85, "american": 0.85,
    "parrilla": 0.85, "grill": 0.85, "asado": 0.85,
    "pub": 0.80, "bar": 0.80,
    "desayuno": 0.80, "breakfast": 0.80, "brunch": 0.80,

    # Tier 2: Afinidad moderada (0.50-0.75)
    "internacional": 0.70, "fusion": 0.65,
    "hotel": 0.65,
    "boliviana": 0.60, "comida nacional": 0.60,
    "espanola": 0.60, "spanish": 0.60,
    "mexicana": 0.55, "latin": 0.55,
    "mediterranea": 0.55,
    "francesa": 0.50,

    # Tier 3: Baja afinidad (0.05-0.45)
    "cafeteria": 0.45, "cafe": 0.40,
    "peruana": 0.40,
    "china": 0.30, "japonesa": 0.30,
    "sushi": 0.25, "thai": 0.25,
    "india": 0.20, "bakery": 0.20, "pasteleria": 0.15,
    "vegetariana": 0.10, "vegana": 0.05,
}

ZONE_SCORES = {
    "Calacoto": 15.0,
    "San Miguel": 14.0,
    "Zona Sur": 14.0,
    "Achumani": 13.0,
    "Irpavi": 12.0,
    "Obrajes": 11.0,
    "Cota Cota": 11.0,
    "Sopocachi": 10.0,
    "Miraflores": 8.0,
    "Centro": 6.0,
}

PRICE_SCORES = {
    "$$$$": 10.0,
    "$$$": 8.0,
    "$$": 6.0,
    "$": 3.0,
}

DEFAULT_ZONE_SCORE = 7.0
DEFAULT_PRICE_SCORE = 5.0
DEFAULT_CUISINE_AFFINITY = 0.50
