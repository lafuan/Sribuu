-- Migration: 0003_drop_broken_indexes
-- Drops indexes that reference columns not present in the live D1 database.
-- The live database was created with an older schema that was missing
-- parent_transaction_id and payment_method_id columns.
-- Since CREATE INDEX IF NOT EXISTS still fails when the column doesn't exist,
-- we need ALTER TABLE ... DROP COLUMN is not supported in SQLite,
-- so we must DROP INDEX separately.
-- These were already removed from 0001_initial.sql to prevent re-occurrence.

-- Drop index referencing parent_transaction_id (missing column in live DB)
DROP INDEX IF EXISTS idx_tx_parent;

-- Drop index referencing payment_method_id (also missing column in live DB)
DROP INDEX IF EXISTS idx_tx_user_payment;
