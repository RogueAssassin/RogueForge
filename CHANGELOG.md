# Changelog

## 2.1.0 (testing)

- Advanced the permanent testing branch after successful RogueForge 2.0.0 production promotion.
- Preserved API version 2 and state schema version 1 as the compatibility baseline.
- Kept the validated lifecycle, update, logging, terminal and RogueDashboard integration systems unchanged.
- Updated the testing README and release metadata while retaining 2.0.0 as the stable main/latest production release.
- Added no environment revision because 2.1.0 introduces no new runtime setting.
- Reserved 2.1 development for versioned API expansion, structured bounded audit/events, diagnostics and recovery-quality improvements.

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

