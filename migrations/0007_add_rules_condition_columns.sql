-- Migration: 0007_add_rules_condition_columns
-- The _worker.ts code uses description, condition, action columns for rules
-- but migration 0001 created match_keywords, category_id, payment_method_id instead.
-- This fix adds the missing columns and drops the old unused ones.

-- Add new columns used by the auto-categorization engine
ALTER TABLE rules ADD COLUMN description TEXT NOT NULL DEFAULT '';
ALTER TABLE rules ADD COLUMN condition TEXT NOT NULL DEFAULT '{}';
ALTER TABLE rules ADD COLUMN action TEXT NOT NULL DEFAULT '{}';

-- Old columns (not used by new engine) — kept for backward compatibility
-- but made optional via defaults. Existing data preserved.
-- match_keywords, category_id, payment_method_id remain but are unused by _worker.ts
