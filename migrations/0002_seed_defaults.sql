-- Migration: 0002_seed_defaults
-- Default payment methods and categories

-- Default payment methods
INSERT INTO payment_methods (name, icon, is_default, is_active) VALUES
    ('Cash', '💵', 0, 1),
    ('Debit Card', '💳', 0, 1),
    ('Credit Card', '💳', 0, 1),
    ('E-Wallet', '📱', 0, 1),
    ('Bank Transfer', '🏦', 0, 1);

-- Default categories (user_id = NULL for system defaults)
INSERT INTO categories (user_id, name, icon, color, is_default, is_active) VALUES
    (NULL, 'Food & Dining', '🍔', '#FF6B6B', 1, 1),
    (NULL, 'Transportation', '🚗', '#4ECDC4', 1, 1),
    (NULL, 'Shopping', '🛍️', '#45B7D1', 1, 1),
    (NULL, 'Entertainment', '🎮', '#96CEB4', 1, 1),
    (NULL, 'Bills & Utilities', '⚡', '#FFEAA7', 1, 1),
    (NULL, 'Healthcare', '🏥', '#DDA0DD', 1, 1),
    (NULL, 'Education', '📚', '#98D8C8', 1, 1),
    (NULL, 'Housing', '🏠', '#F7DC6F', 1, 1),
    (NULL, 'Income', '💰', '#2ECC71', 1, 1),
    (NULL, 'Savings', '🏦', '#3498DB', 1, 1),
    (NULL, 'Investment', '📈', '#9B59B6', 1, 1),
    (NULL, 'Subscription', '🔄', '#E67E22', 1, 1),
    (NULL, 'Other', '📦', '#95A5A6', 1, 1);
