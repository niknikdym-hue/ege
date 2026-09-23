CREATE TABLE IF NOT EXISTS pro_payment_orders (
    order_id TEXT PRIMARY KEY,
    inv_id BIGINT NOT NULL UNIQUE,
    user_identity_ref TEXT NOT NULL,
    learner_profile_id TEXT NOT NULL,
    offer_code TEXT NOT NULL,
    product_code TEXT NOT NULL,
    duration_days INTEGER NOT NULL,
    amount_kopecks BIGINT NOT NULL,
    payment_method TEXT NOT NULL,
    status TEXT NOT NULL,
    receipt_status TEXT NOT NULL,
    provider TEXT NOT NULL,
    provider_payment_ref TEXT,
    provider_receipt_ref TEXT,
    attempt_count INTEGER NOT NULL,
    created_at_epoch BIGINT NOT NULL,
    updated_at_epoch BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS pro_payment_events (
    event_key TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    event_kind TEXT NOT NULL,
    payload_sha256 TEXT NOT NULL,
    created_at_epoch BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS pro_entitlements (
    entitlement_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL UNIQUE,
    learner_profile_id TEXT NOT NULL,
    product_code TEXT NOT NULL,
    starts_at_epoch BIGINT NOT NULL,
    expires_at_epoch BIGINT NOT NULL,
    state TEXT NOT NULL,
    revoked_at_epoch BIGINT,
    revoke_reason TEXT
);
CREATE INDEX IF NOT EXISTS idx_pro_orders_learner ON pro_payment_orders(learner_profile_id);
CREATE INDEX IF NOT EXISTS idx_pro_entitlements_learner ON pro_entitlements(learner_profile_id);
CREATE INDEX IF NOT EXISTS idx_pro_entitlements_active ON pro_entitlements(learner_profile_id, product_code, state, expires_at_epoch);
INSERT INTO peis_schema_migrations(version) VALUES ('0003_payments_entitlement_postgres') ON CONFLICT (version) DO NOTHING;
