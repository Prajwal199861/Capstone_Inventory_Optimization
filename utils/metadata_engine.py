"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : metadata_engine.py

Description :
Defines metadata templates for supported retail entities and provides
automatic column suggestion and validation.
=============================================================================
"""


class MetadataEngine:

    ENTITY_TEMPLATES = {

        "Sales": {
            "required": {
                "Transaction Date": [
                    "date",
                    "transaction_date",
                    "invoice_date",
                    "sale_date",
                    "order_date"
                ],
                "Product ID": [
                    "product_id",
                    "sku",
                    "item_id",
                    "productkey",
                    "product_key"
                ],
                "Quantity": [
                    "qty",
                    "quantity",
                    "units",
                    "sales_quantity"
                ]
            },
            "recommended": {
                # Revenue is recommended (not required): datasets
                # without a revenue column can still be forecast on
                # Quantity, and Revenue can be derived from the
                # Products selling price (Phase 2A DemandService).
                "Revenue": [
                    "sales",
                    "revenue",
                    "amount",
                    "total",
                    "sales_amount"
                ],
                "Store ID": [
                    "store_id",
                    "branch_id",
                    "store",
                    "storekey",
                    "store_key"
                ],
                "Customer ID": [
                    "customer_id",
                    "customer"
                ],
                "Promotion ID": [
                    "promotion_id",
                    "promo_id",
                    "promotion"
                ],
                "Discount": [
                    "discount",
                    "discount_amount"
                ]
            },
            "optional": {
                "Invoice Number": [
                    "invoice",
                    "invoice_no",
                    "bill_no",
                    "order_number",
                    "order_id"
                ],
                "Order ID": [
                    "order_id",
                    "order_number"
                ],
                "Payment Mode": [
                    "payment",
                    "payment_mode"
                ],
                "Currency": [
                    "currency"
                ]
            }
        },
        "Products": {
            "required": {
                "Product ID": [
                    "product_id",
                    "sku",
                    "productkey",
                    "product_key"
                ],
                "Product Name": [
                    "product_name",
                    "item_name",
                    "product"
                ]
            },
            "recommended": {

                "Category": [
                    "category"
                ],

                "Sub Category": [
                    "subcategory",
                    "sub_category"
                ],

                "Brand": [
                    "brand"
                ],

                "Cost Price": [
                    "cost",
                    "cost_price"
                ],

                "Selling Price": [
                    "price",
                    "selling_price",
                    "unit_price"
                ]

            },

            "optional": {

                "Supplier": [
                    "supplier",
                    "vendor"
                ],

                "Manufacturer": [
                    "manufacturer"
                ],

                "Weight": [
                    "weight"
                ],

                "Color": [
                    "color"
                ],

                "Size": [
                    "size"
                ]

            }

        },

        "Stores": {

            "required": {

                "Store ID": [
                    "store_id",
                    "branch_id"
                ],

                "Store Name": [
                    "store_name",
                    "branch_name",
                    "store"
                ]

            },

            "recommended": {

                "City": [
                    "city"
                ],

                "State": [
                    "state"
                ],

                "Country": [
                    "country"
                ],

                "Store Type": [
                    "store_type",
                    "type"
                ]

            },

            "optional": {

                "Manager": [
                    "manager"
                ],

                "Phone": [
                    "phone"
                ],

                "Email": [
                    "email"
                ],

                "Latitude": [
                    "latitude",
                    "lat"
                ],

                "Longitude": [
                    "longitude",
                    "lon",
                    "lng"
                ],

                "Open Date": [
                    "open_date",
                    "opening_date"
                ]

            }

        },

        "Inventory": {

            "required": {

                "Product ID": [
                    "product_id",
                    "sku"
                ],

                "Current Stock": [
                    "stock",
                    "inventory",
                    "current_stock"
                ]

            },

            "recommended": {

                "Warehouse": [
                    "warehouse"
                ],

                "Reorder Level": [
                    "reorder_level"
                ],

                "Safety Stock": [
                    "safety_stock"
                ],

                "Maximum Stock": [
                    "max_stock"
                ]

            },

            "optional": {

                "Batch Number": [
                    "batch"
                ],

                "Expiry Date": [
                    "expiry",
                    "expiry_date"
                ]

            }

        },

        "Calendar": {

            "required": {

                "Date": [
                    "date"
                ]

            },

            "recommended": {

                "Holiday": [
                    "holiday"
                ],

                "Weekend": [
                    "weekend"
                ],

                "Festival": [
                    "festival"
                ]

            },

            "optional": {

                "Month": [
                    "month"
                ],

                "Quarter": [
                    "quarter"
                ],

                "Year": [
                    "year"
                ]

            }

        },

        "Customers": {

            "required": {

                "Customer ID": [
                    "customer_id"
                ]

            },

            "recommended": {

                "Customer Name": [
                    "customer_name",
                    "customer"
                ],

                "Gender": [
                    "gender"
                ],

                "Age": [
                    "age"
                ]

            },

            "optional": {

                "Email": [
                    "email"
                ],

                "Phone": [
                    "phone"
                ],

                "City": [
                    "city"
                ]

            }

        },

        "Promotions": {

            "required": {

                "Promotion ID": [
                    "promotion_id"
                ]

            },

            "recommended": {

                "Promotion Name": [
                    "promotion_name"
                ],

                "Discount": [
                    "discount"
                ],

                "Start Date": [
                    "start_date"
                ],

                "End Date": [
                    "end_date"
                ]

            },

            "optional": {

                "Description": [
                    "description"
                ]

            }

        }

    }

    @classmethod
    def get_template(cls, entity_type: str):

        return cls.ENTITY_TEMPLATES.get(entity_type, {})

    @classmethod
    def suggest_columns(
            cls,
            entity_type: str,
            dataframe_columns: list[str]
    ):

        template = cls.get_template(entity_type)

        suggestions = {}

        used_columns = set()

        for section in ["required", "recommended", "optional"]:

            suggestions[section] = {}

            for business_field, keywords in template.get(section, {}).items():

                # Exact keyword matches are preferred over substring
                # matches, and columns not yet suggested for another
                # field are preferred over already-used ones, so two
                # fields do not silently claim the same column
                # (e.g. ProductKey for both Product ID and Product Name).
                exact = []

                partial = []

                for column in dataframe_columns:

                    column_lower = column.lower().replace(" ", "_")

                    if column_lower in keywords:

                        exact.append(column)

                    elif any(
                            keyword in column_lower
                            for keyword in keywords
                    ):
                        partial.append(column)

                candidates = exact + partial

                suggestion = next(

                    (
                        column
                        for column in candidates
                        if column not in used_columns
                    ),

                    candidates[0] if candidates else None

                )

                suggestions[section][business_field] = suggestion

                if suggestion is not None:

                    used_columns.add(suggestion)

        return suggestions

    @classmethod
    def validate_mapping(
            cls,
            entity_type: str,
            mapping: dict
    ):

        template = cls.get_template(entity_type)

        missing = []

        for field in template.get("required", {}):

            if field not in mapping or not mapping[field]:

                missing.append(field)

        return missing