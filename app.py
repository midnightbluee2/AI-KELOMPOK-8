"""
app.py

Entry point Smart Parking Dashboard.
Jalankan: python app.py
Buka: http://localhost:8050
"""

import dash
import dash_bootstrap_components as dbc

from layout import build_layout
from callbacks.run_callback import register_callbacks

app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.SLATE,
        dbc.icons.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
    ],
    title="Smart Parking",
)

app.layout = build_layout()
register_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True)