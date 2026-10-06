CREATE TABLE IF NOT EXISTS tutor_contexts (
    context_id TEXT PRIMARY KEY,
    learner_profile_id TEXT NOT NULL,
    card_id TEXT NOT NULL,
    lineage INTEGER NOT NULL,
    error_event_id TEXT NOT NULL,
    help_event_id TEXT NOT NULL UNIQUE,
    provider_id TEXT NOT NULL,
    tutor_text TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('VERIFICATION_REQUIRED', 'VERIFIED')),
    created_at TEXT NOT NULL,
    helped_at_epoch BIGINT NOT NULL,
    verified_event_id TEXT,
    UNIQUE(learner_profile_id, card_id, lineage)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_tutor_context_pending_card
    ON tutor_contexts(learner_profile_id, card_id)
    WHERE status = 'VERIFICATION_REQUIRED';
CREATE INDEX IF NOT EXISTS idx_tutor_context_learner
    ON tutor_contexts(learner_profile_id, card_id, lineage);
INSERT INTO peis_schema_migrations(version) VALUES ('0004_tutor_lifecycle_postgres') ON CONFLICT (version) DO NOTHING;
