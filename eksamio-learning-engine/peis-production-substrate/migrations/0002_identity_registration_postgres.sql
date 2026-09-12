CREATE TABLE IF NOT EXISTS passwordless_challenges (
    challenge_id TEXT PRIMARY KEY,
    user_identity_ref TEXT NOT NULL,
    channel TEXT NOT NULL,
    verification_hash TEXT NOT NULL,
    anonymous_identity_ref TEXT,
    created_at_epoch BIGINT NOT NULL,
    expires_at_epoch BIGINT NOT NULL,
    consumed_at_epoch BIGINT
);
CREATE TABLE IF NOT EXISTS identity_sessions (
    session_hash TEXT PRIMARY KEY,
    user_identity_ref TEXT NOT NULL,
    learner_profile_id TEXT NOT NULL,
    created_at_epoch BIGINT NOT NULL,
    expires_at_epoch BIGINT NOT NULL,
    revoked_at_epoch BIGINT
);
CREATE INDEX IF NOT EXISTS idx_identity_sessions_user ON identity_sessions(user_identity_ref);
CREATE INDEX IF NOT EXISTS idx_identity_sessions_learner ON identity_sessions(learner_profile_id);
CREATE TABLE IF NOT EXISTS registration_consent_events (
    event_seq BIGSERIAL PRIMARY KEY,
    event_id TEXT UNIQUE NOT NULL,
    user_identity_ref TEXT NOT NULL,
    consent_type TEXT NOT NULL,
    action TEXT NOT NULL,
    captured_at_epoch BIGINT NOT NULL,
    document_version TEXT NOT NULL,
    text_version TEXT NOT NULL,
    client_request_id TEXT NOT NULL,
    registration_challenge_id TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_registration_consent_request ON registration_consent_events(user_identity_ref, consent_type, client_request_id);
CREATE INDEX IF NOT EXISTS idx_registration_consent_latest ON registration_consent_events(user_identity_ref, consent_type, event_seq);
CREATE INDEX IF NOT EXISTS idx_registration_consent_challenge ON registration_consent_events(user_identity_ref, registration_challenge_id, consent_type);
CREATE TABLE IF NOT EXISTS registration_begin_operations (
    operation_id TEXT PRIMARY KEY,
    user_identity_ref TEXT NOT NULL,
    request_fingerprint TEXT NOT NULL,
    challenge_id TEXT UNIQUE NOT NULL,
    channel TEXT NOT NULL,
    created_at_epoch BIGINT NOT NULL,
    expires_at_epoch BIGINT NOT NULL,
    delivery_state TEXT NOT NULL,
    delivery_ref TEXT,
    updated_at_epoch BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_registration_begin_user ON registration_begin_operations(user_identity_ref, created_at_epoch);
DROP TRIGGER IF EXISTS no_update_registration_consent_events ON registration_consent_events;
CREATE TRIGGER no_update_registration_consent_events BEFORE UPDATE OR DELETE ON registration_consent_events FOR EACH ROW EXECUTE FUNCTION peis_reject_history_mutation();
INSERT INTO peis_schema_migrations(version) VALUES ('0002_identity_registration_postgres') ON CONFLICT (version) DO NOTHING;
