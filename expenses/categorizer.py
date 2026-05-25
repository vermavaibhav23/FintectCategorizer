from decimal import Decimal, InvalidOperation


MERCHANT_RULES = {
    "Food": [
        "barbeque nation",
        "behrouz",
        "burger king",
        "chaayos",
        "domino",
        "eatfit",
        "faasos",
        "freshmenu",
        "haldiram",
        "kfc",
        "mcdonald",
        "mcdonalds",
        "oven story",
        "pizza hut",
        "starbucks",
        "subway",
        "swiggy",
        "taco bell",
        "wow momo",
        "zomato",
    ],
    "Travel": [
        "air india",
        "akasa air",
        "blusmart",
        "cleartrip",
        "goibibo",
        "indigo",
        "irctc",
        "ixigo",
        "makemytrip",
        "meru",
        "nuego",
        "ola",
        "rapido",
        "redbus",
        "spicejet",
        "uber",
        "vistara",
        "yatra",
    ],
    "Shopping": [
        "ajio",
        "amazon",
        "croma",
        "decathlon",
        "firstcry",
        "flipkart",
        "hm",
        "h&m",
        "ikea",
        "lenskart",
        "lifestyle",
        "max fashion",
        "meesho",
        "myntra",
        "nykaa",
        "pantaloons",
        "reliance digital",
        "shoppers stop",
        "snapdeal",
        "tata cliq",
        "vijay sales",
        "westside",
    ],
    "Bills": [
        "act fibernet",
        "adani electricity",
        "airtel",
        "bescom",
        "bsnl",
        "broadband",
        "dth",
        "electricity",
        "fastag",
        "gas bill",
        "hathway",
        "idea",
        "jio",
        "mgl",
        "postpaid",
        "recharge",
        "tata play",
        "torrent power",
        "vodafone",
        "water bill",
    ],
    "Medical": [
        "1mg",
        "apollo",
        "apollo pharmacy",
        "aster",
        "care hospital",
        "fortis",
        "healthians",
        "lal pathlabs",
        "manipal hospital",
        "max healthcare",
        "medplus",
        "netmeds",
        "pharmeasy",
        "pharmacy",
        "practo",
        "thyrocare",
    ],
    "Groceries": [
        "bigbasket",
        "big bazaar",
        "blinkit",
        "dmart",
        "d mart",
        "fresh to home",
        "grofers",
        "jiomart",
        "licious",
        "more supermarket",
        "nature's basket",
        "reliance fresh",
        "spencer's",
        "star bazaar",
        "supermart",
        "zepto",
    ],
    "Entertainment": [
        "book my show",
        "bookmyshow",
        "cinépolis",
        "cinepolis",
        "hotstar",
        "inox",
        "netflix",
        "pvr",
        "sonyliv",
        "spotify",
        "zee5",
    ],
}

CATEGORY_RULES = {
    "Food": [
        "domino",
        "pizza",
        "restaurant",
        "swiggy",
        "zomato",
        "cafe",
        "coffee",
        "burger",
        "kfc",
        "mcdonald",
    ],
    "Travel": ["uber", "ola", "taxi", "metro", "flight", "train", "bus", "railway", "cab"],
    "Shopping": ["amazon", "flipkart", "myntra", "store", "mall", "fashion", "retail"],
    "Bills": ["electricity", "wifi", "mobile", "recharge", "broadband", "bill", "postpaid"],
    "Medical": ["pharmacy", "hospital", "clinic", "medicine", "apollo", "health"],
    "Groceries": ["grocery", "dmart", "bigbasket", "blinkit", "zepto", "mart", "supermarket"],
    "Entertainment": ["movie", "cinema", "bookmyshow", "netflix", "spotify", "game"],
}


def categorize_expense(text, merchant="", amount=None):
    haystack = f"{merchant} {text}".lower()

    for category, keywords in MERCHANT_RULES.items():
        if any(keyword in haystack for keyword in keywords):
            return category

    for category, keywords in CATEGORY_RULES.items():
        if any(keyword in haystack for keyword in keywords):
            return category

    try:
        parsed_amount = Decimal(str(amount or "0"))
    except (InvalidOperation, TypeError):
        parsed_amount = Decimal("0")

    if parsed_amount > Decimal("10000"):
        return "Shopping"

    return "Other"


def category_palette():
    return {
        "Food": "#2563eb",
        "Travel": "#0891b2",
        "Shopping": "#7c3aed",
        "Bills": "#dc2626",
        "Medical": "#16a34a",
        "Groceries": "#ea580c",
        "Entertainment": "#db2777",
        "Other": "#64748b",
    }
