# Changelog

## 1.9.0 (testing)

- Established the final 1.x cleanup baseline before RogueForge 2.0.
- Preserved the tested lifecycle, update-preview, image-verification, rollback, logging, terminal and RogueDashboard-integration systems.
- Removed no-op environment revision blocks and updater writes for releases that introduced no new environment commands.
- Clarified that environment revisions are created only when a release genuinely adds a new setting.
- Kept the canonical default environment file and `/opt/media-server/rogueforge` deployment layout.
- Cleaned current release documentation and roadmap for the 2.0 transition.
- Froze additional 1.x feature expansion; remaining work is stability, compatibility and main-branch promotion readiness.

## 1.6.0 (testing)

- Added the lightweight read-only RogueDashboard integration endpoint.
- Reused RogueForge's cached dashboard snapshot and in-memory operation history instead of adding another engine polling loop.
- Preserved the tested 1.5 lifecycle/update-preview and 1.4 logging systems.

## 1.5.0 (testing)

- Added authenticated stack update previews with affected services and image identity.
- Preserved verified in-place updates and rollback protection.
- Established the rule that existing administrator `.env` files survive upgrades.

## 1.4.0 (testing)

- Added live-log severity filtering, reconnect visibility and clearer operation timing while keeping logging on demand.

## 1.3.0

- Established the stable verified lifecycle and canonical deployment baseline.

