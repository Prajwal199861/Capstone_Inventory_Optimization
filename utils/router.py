"""
=============================================================================
Router
=============================================================================
"""

from pages.Dashboard import dashboard


def route(page: str):

    routes = {

        "Dashboard": dashboard

    }

    if page in routes:

        routes[page]()