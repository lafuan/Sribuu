-- Migration: 0004_add_missing_columns
-- Adds columns to transactions table that were missing in the live D1 database.
-- The D1 database was created with an older schema that lacked
-- payment_method_id and parent_transaction_id columns.
-- 
-- Since SQLite doesn't support IF NOT EXISTS for ALTER TABLE ADD COLUMN,
-- we use a TRY/CATCH pattern: the migration runner should handle
-- "duplicate column name" errors gracefully. Alternatively, this can be
-- run manually: first check with PRAGMA table_info then execute only
-- the missing ALTER TABLE statements.

-- Add payment_method_id column (FK to payment_methods)
ALTER TABLE transactions ADD COLUMN payment_method_id INTEGER REFERENCES payment_methods(id) ON DELETE SET NULL;

-- Add parent_transaction_id column (self-referencing FK)
ALTER TABLE transactions ADD COLUMN parent_transaction_id INTEGER REFERENCES transactions(id) ON DELETE SET NULL;

-- Re-create indexes that were dropped in 0003 (now that columns exist)
CREATE INDEX IF NOT EXISTS idx_tx_user_payment ON transactions(user_id, payment_method_id);
CREATE INDEX IF NOT EXISTS idx_tx_parent ON transactions(parent_transaction_id);
