CREATE TABLE IF NOT EXISTS ganttax_imports (
 id VARCHAR(36) PRIMARY KEY,
 project_code VARCHAR(255),
 imported_at TIMESTAMPTZ NOT NULL,
 source_sha256 VARCHAR(64) NOT NULL,
 mapping_version VARCHAR(20) NOT NULL,
 approval_status VARCHAR(20) NOT NULL DEFAULT 'STAGED',
 raw_state JSONB NOT NULL,
 normalized_state JSONB NOT NULL
);
