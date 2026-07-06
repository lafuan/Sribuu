-- Migration: 0001_initial_schema
-- Ported from PostgreSQL to D1 (SQLite)

-- Users
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    notification_enabled INTEGER NOT NULL DEFAULT 0,
    reminder_time TEXT DEFAULT '20:00',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_users_email ON users(email);

-- Payment Methods
CREATE TABLE payment_methods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    icon TEXT NOT NULL,
    is_default INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_payment_methods_active ON payment_methods(is_active);

-- Categories
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    icon TEXT NOT NULL,
    color TEXT NOT NULL,
    is_default INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_categories_default ON categories(is_default, is_active);
CREATE INDEX idx_categories_user ON categories(user_id, is_active);

-- Transactions
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    payment_method_id INTEGER REFERENCES payment_methods(id) ON DELETE SET NULL,
    parent_transaction_id INTEGER REFERENCES transactions(id) ON DELETE SET NULL,
    amount INTEGER NOT NULL,
    notes TEXT,
    attachment_path TEXT,
    transaction_date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_tx_user_date ON transactions(user_id, transaction_date);
CREATE INDEX idx_tx_user_category ON transactions(user_id, category_id);
CREATE INDEX idx_tx_user_payment ON transactions(user_id, payment_method_id);
CREATE INDEX idx_tx_parent ON transactions(parent_transaction_id);
CREATE INDEX idx_tx_user_amount ON transactions(user_id, transaction_date, amount);

-- Budgets
CREATE TABLE budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    month INTEGER NOT NULL,
    year INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    rollover INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_budget_user_month ON budgets(user_id, year, month);
CREATE INDEX idx_budget_user_cat_month ON budgets(user_id, category_id, year, month);

-- Subscriptions
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    name TEXT NOT NULL,
    amount INTEGER NOT NULL,
    billing_cycle TEXT NOT NULL DEFAULT 'monthly',
    start_date TEXT NOT NULL,
    next_payment_date TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_sub_user_active ON subscriptions(user_id, is_active);
CREATE INDEX idx_sub_user_cat ON subscriptions(user_id, category_id);

-- Bills
CREATE TABLE bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    name TEXT NOT NULL,
    amount INTEGER NOT NULL,
    due_date TEXT NOT NULL,
    is_paid INTEGER NOT NULL DEFAULT 0,
    paid_date TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_bills_user_due ON bills(user_id, due_date);
CREATE INDEX idx_bills_user_paid ON bills(user_id, is_paid);

-- Rules (auto-categorization)
CREATE TABLE rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    match_keywords TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    payment_method_id INTEGER REFERENCES payment_methods(id) ON DELETE SET NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    priority INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_rules_user_active ON rules(user_id, is_active);
CREATE INDEX idx_rules_user_priority ON rules(user_id, priority);

-- Transaction Templates
CREATE TABLE transaction_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    payment_method_id INTEGER REFERENCES payment_methods(id) ON DELETE SET NULL,
    amount INTEGER NOT NULL,
    name TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_templates_user ON transaction_templates(user_id);
