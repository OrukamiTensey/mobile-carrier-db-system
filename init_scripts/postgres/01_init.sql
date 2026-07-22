-- Ініціалізація таблиць PostgreSQL

-- Таблиця абонентів
CREATE TABLE IF NOT EXISTS subscribers (
    id SERIAL PRIMARY KEY,
    ric_number VARCHAR(20) UNIQUE NOT NULL,
    pin_code VARCHAR(10),
    full_name VARCHAR(255) NOT NULL,
    phone_model VARCHAR(100),
    phone_type VARCHAR(50) CHECK (phone_type IN ('smartphone', 'feature_phone', 'tablet')),
    service_type VARCHAR(50) CHECK (service_type IN ('prepaid', 'postpaid', 'corporate')),
    contract_duration_months INTEGER DEFAULT 12,
    contract_start_date DATE NOT NULL DEFAULT CURRENT_DATE,
    monthly_cost DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблиця платежів
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    subscriber_id INTEGER REFERENCES subscribers(id) ON DELETE CASCADE,
    amount DECIMAL(10, 2) NOT NULL,
    due_date DATE NOT NULL,
    paid_date DATE,
    is_delayed BOOLEAN DEFAULT FALSE,
    delay_days INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Індекси для оптимізації запитів
CREATE INDEX IF NOT EXISTS idx_subscribers_ric ON subscribers(ric_number);
CREATE INDEX IF NOT EXISTS idx_subscribers_active ON subscribers(is_active);
CREATE INDEX IF NOT EXISTS idx_payments_subscriber ON payments(subscriber_id);
CREATE INDEX IF NOT EXISTS idx_payments_delayed ON payments(is_delayed);
CREATE INDEX IF NOT EXISTS idx_payments_due_date ON payments(due_date);

-- Тригер для оновлення updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_subscribers_updated_at
    BEFORE UPDATE ON subscribers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Вставка тестових даних
INSERT INTO subscribers (ric_number, pin_code, full_name, phone_model, phone_type, service_type, contract_duration_months, contract_start_date, monthly_cost)
VALUES 
    ('380501234567', '1234', 'Іванов Іван Іванович', 'iPhone 15 Pro', 'smartphone', 'postpaid', 24, '2024-01-15', 499.00),
    ('380502345678', '5678', 'Петренко Петро Петрович', 'Samsung Galaxy S24', 'smartphone', 'postpaid', 12, '2024-03-01', 399.00),
    ('380503456789', '9012', 'Сидоренко Марія Олексіївна', 'Xiaomi 14', 'smartphone', 'prepaid', 6, '2024-06-10', 199.00),
    ('380504567890', '3456', 'Коваленко Олег Вікторович', 'Nokia 3310', 'feature_phone', 'prepaid', 12, '2024-02-20', 99.00),
    ('380505678901', '7890', 'Шевченко Анна Сергіївна', 'iPad Pro', 'tablet', 'corporate', 36, '2023-09-01', 799.00)
ON CONFLICT (ric_number) DO NOTHING;

-- Тестові платежі (деякі прострочені)
INSERT INTO payments (subscriber_id, amount, due_date, paid_date, is_delayed, delay_days)
SELECT 
    s.id,
    s.monthly_cost,
    '2024-11-01'::date,
    '2024-11-05'::date,
    TRUE,
    4
FROM subscribers s WHERE s.ric_number = '380501234567';

INSERT INTO payments (subscriber_id, amount, due_date, paid_date, is_delayed, delay_days)
SELECT 
    s.id,
    s.monthly_cost,
    '2024-11-01'::date,
    NULL,
    TRUE,
    36
FROM subscribers s WHERE s.ric_number = '380502345678';

INSERT INTO payments (subscriber_id, amount, due_date, paid_date, is_delayed, delay_days)
SELECT 
    s.id,
    s.monthly_cost,
    '2024-12-01'::date,
    '2024-12-01'::date,
    FALSE,
    0
FROM subscribers s WHERE s.ric_number = '380503456789';
