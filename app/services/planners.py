"""The three planners. Each one has its own form fields and AI focus."""

PLANNERS = {
    "home": {
        "title": "Home interior budget planner",
        "short": "Furnish or decorate rooms within a budget.",
        "focus": "Home interior and decoration: furniture, lighting, fans, decor and furnishings.",
        "requirements_hint": "e.g. 4 ceiling fans, 4 lights, 1 dining table",
        "extra": [
            {"name": "rooms", "label": "Rooms", "placeholder": "Living room, bedroom"},
            {"name": "style", "label": "Style you like", "placeholder": "Modern, minimal, traditional"},
        ],
        "allow_image": False,
    },
    "party": {
        "title": "Party budget planner",
        "short": "Plan decor, food and extras for an event.",
        "focus": "Party and event planning: decor, food and drinks, return gifts, entertainment and supplies.",
        "requirements_hint": "e.g. balloon decor, cake, snacks for guests, return gifts",
        "extra": [
            {"name": "guests", "label": "Number of guests", "placeholder": "30"},
            {"name": "theme", "label": "Theme or occasion", "placeholder": "Birthday, superhero theme"},
        ],
        "allow_image": False,
    },
    "jewellery": {
        "title": "Jewellery budget planner",
        "short": "Find pieces that fit an occasion and a budget.",
        "focus": "Jewellery shopping: necklaces, earrings, bangles, rings and sets in gold, silver, diamond or imitation.",
        "requirements_hint": "e.g. a necklace and earrings set for a wedding",
        "extra": [
            {"name": "occasion", "label": "Occasion", "placeholder": "Wedding, festival, daily wear"},
            {"name": "metal", "label": "Metal or material", "placeholder": "Gold, silver, imitation"},
        ],
        "allow_image": True,
    },
}
