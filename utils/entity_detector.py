"""
=============================================================================
Entity Detector
=============================================================================
"""


class EntityDetector:

    ENTITY_RULES = {

        "Sales": [
            "sales",
            "sale",
            "transaction",
            "invoice",
            "order"
        ],

        "Products": [
            "product",
            "products",
            "item",
            "items",
            "sku"
        ],

        "Inventory": [
            "inventory",
            "stock"
        ],

        "Stores": [
            "store",
            "stores",
            "shop",
            "branch"
        ],

        "Customers": [
            "customer",
            "customers",
            "client"
        ],

        "Calendar": [
            "calendar",
            "holiday",
            "date"
        ],

        "Promotions": [
            "promotion",
            "offer",
            "discount"
        ],

        "Suppliers": [
            "supplier",
            "vendor"
        ]

    }

    @staticmethod
    def detect(filename: str) -> str:

        filename = filename.lower()

        for entity, keywords in EntityDetector.ENTITY_RULES.items():

            for keyword in keywords:

                if keyword in filename:

                    return entity

        return "Custom"