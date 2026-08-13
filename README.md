# Foodies — Restaurant QR Menu (starter build)

## What's built so far
- Home page with two entry points: Owner and Customer
- Full SQL schema (schema.sql) covering owners, menu items, orders, order_items,
  visits, and restaurant_settings — designed for everything we planned:
  veg/non-veg, weekly menu, offers, GST, service charge, analytics
- Working owner registration + login (passwords hashed, sessions handled)
- Route structure ready for: /owner/dashboard, /menu (customer, reads
  restaurant_id + table from the QR URL)

## How to run it yourself
1. Install dependencies:
   pip install -r requirements.txt

2. Run the app:
   python app.py

   First run auto-creates foodies.db from schema.sql.

3. Open http://127.0.0.1:5000 in your browser.

## Project structure
foodies/
├── app.py                  <- Flask app + routes
├── schema.sql               <- full database design
├── requirements.txt
├── templates/
│   ├── index.html            <- home page (owner/customer split)
│   ├── owner_register.html
│   ├── owner_login.html
│   ├── owner_dashboard.html   <- stub, next to build
│   └── menu.html              <- stub, next to build
└── static/
    ├── css/style.css          <- shared design system
    ├── css/forms.css
    └── js/script.js           <- cart logic goes here next

## Next steps (in order)
1. Owner dashboard: add/edit/delete menu items, veg/non-veg, weekly vs daily
2. Customer menu page: fetch items via /api/menu, veg/non-veg/both filters,
   food cards with image + prep time
3. Cart in JavaScript + "Place Order" -> /api/order -> writes to orders + order_items
4. Order status flow (pending -> preparing -> ready) + customer-side polling
5. Owner analytics: visits, veg/non-veg/both split, revenue, popular items
6. GST / offer / service charge billing calculation
7. QR code generator script (using the `qrcode` Python package)
