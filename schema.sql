-- ===================================================
-- FOODIES DATABASE SCHEMA
-- ===================================================

-- Restaurant owners (the only ones who log in)
CREATE TABLE IF NOT EXISTS owners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_name TEXT NOT NULL,
    owner_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    location TEXT,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Per-restaurant settings (GST, service charge etc.)
CREATE TABLE IF NOT EXISTS restaurant_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL,
    gst_percent REAL DEFAULT 0,
    service_type TEXT DEFAULT 'self',        -- 'self' or 'table'
    service_charge REAL DEFAULT 0,           -- flat amount, only used if service_type = 'table'
    FOREIGN KEY (restaurant_id) REFERENCES owners(id)
);

-- Menu items (food + beverages + sweets etc.)
CREATE TABLE IF NOT EXISTS menu_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    brand TEXT,                              -- for beverages e.g. "Coca-Cola"
    description TEXT,
    price REAL NOT NULL,
    category TEXT NOT NULL,                  -- Starters, Main Course, Chaats, Juices, Ice Creams, Sweets, Beverages
    food_type TEXT NOT NULL DEFAULT 'veg',   -- 'veg' or 'non-veg'
    image_url TEXT,
    prep_time_minutes INTEGER DEFAULT 10,
    offer_percent REAL DEFAULT 0,
    day_of_week TEXT,                        -- 'Mon','Tue',... or NULL = available every day / today-only
    available INTEGER DEFAULT 1,             -- 1 = yes, 0 = no
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES owners(id)
);

-- Every time a customer opens the menu (for visit analytics)
CREATE TABLE IF NOT EXISTS visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL,
    table_number TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES owners(id)
);

-- One row per placed order
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id INTEGER NOT NULL,
    table_number TEXT,
    customer_name TEXT,
    order_type TEXT,                         -- 'veg', 'non-veg', 'both' -- auto-calculated
    status TEXT DEFAULT 'pending',           -- pending, preparing, ready, completed
    subtotal REAL,
    gst_amount REAL,
    service_charge REAL,
    discount_amount REAL,
    total_amount REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES owners(id)
);

-- Items inside each order
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    menu_item_id INTEGER NOT NULL,
    item_name TEXT NOT NULL,                 -- stored directly so history stays correct even if menu changes later
    quantity INTEGER NOT NULL,
    price_at_order REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (menu_item_id) REFERENCES menu_items(id)
);

-- ===================================================
-- INDEXES — keep lookups fast as owners/customers grow
-- (SQLite already indexes PRIMARY KEY and UNIQUE columns,
--  these cover the columns we filter/count by all the time)
-- ===================================================
CREATE INDEX IF NOT EXISTS idx_menu_items_restaurant   ON menu_items(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_menu_items_category      ON menu_items(restaurant_id, category);
CREATE INDEX IF NOT EXISTS idx_visits_restaurant        ON visits(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_visits_timestamp         ON visits(timestamp);
CREATE INDEX IF NOT EXISTS idx_orders_restaurant        ON orders(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_orders_status            ON orders(restaurant_id, status);
CREATE INDEX IF NOT EXISTS idx_order_items_order        ON order_items(order_id);
