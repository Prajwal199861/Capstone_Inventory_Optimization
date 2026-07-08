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

        # =====================================================================
        # SALES
        # =====================================================================

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
                    "item_id"
                ],

                "Quantity": [
                    "qty",
                    "quantity",
                    "units",
                    "sales_quantity"
                ],

                "Revenue": [
                    "sales",
                    "revenue",
                    "amount",
                    "total",
                    "sales_amount"
                ]

            },

            "recommended": {

                "Store ID": [
                    "store_id",
                    "branch_id",
                    "store"
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
                    "bill_no"
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

        # =====================================================================
        # PRODUCTS
        # =====================================================================

        "Products": {

            "required": {

                "Product ID": [
                    "product_id",
                    "sku"
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

        # =====================================================================
        # STORES
        # =====================================================================

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

        # =====================================================================
        # INVENTORY
        # =====================================================================

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

        # =====================================================================
        # CALENDAR
        # =====================================================================

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

        # =====================================================================
        # CUSTOMERS
        # =====================================================================

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

        # =====================================================================
        # PROMOTIONS
        # =====================================================================

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

        for section in ["required", "recommended", "optional"]:

            suggestions[section] = {}

            for business_field, keywords in template.get(section, {}).items():

                suggestions[section][business_field] = None

                for column in dataframe_columns:

                    column_lower = column.lower().replace(" ", "_")

                    if any(
                            keyword in column_lower
                            for keyword in keywords
                    ):
                        suggestions[section][business_field] = column
                        break

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