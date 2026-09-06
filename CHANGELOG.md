# Changelog

## 2.0.0 (testing)

- Established RogueForge API version 2 and persistent-state schema version 1.
- Added stable read-only `/api/v2/status` and `/api/v2/contract` endpoints.
- Added API/state contract metadata to the RogueDashboard integration payload.
- Declared backward compatibility from the validated 1.9.0 state baseline; no data migration is required for this testing candidate.
- Preserved the verified lifecycle, update preview, image verification, rollback, bounded logging, terminal and operation-history systems.
- Kept the default `.env` unchanged because 2.0.0 introduces no new runtime environment command.
- Kept 2.0.0 on the permanent `testing` branch pending live-host validation before main/latest promotion.

## 1.9.0 (testing)

- Established the final 1.x cleanup baseline before RogueForge 2.0.
- Removed no-op environment revision blocks and cleaned the repository for the major-version transition.

