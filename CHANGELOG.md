# Changelog

All notable changes to bhd-cli will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2026-02-17

### Added
- OSINT test type support to align with Black Hat Defense LLC attack surface analysis service
- ICS/SCADA/OT test type support to align with Black Hat Defense LLC industrial security service offerings
- Test coverage for ICS and OSINT test type creation and validation

### Fixed
- Removed deprecation warning from pytest by using modern importlib.util.find_spec()

## [1.1.0] - 2026-02-15

### Added
- `bhd-cli version` command to display version information
- `bhd-cli export json` for clean JSON data export with deterministic ordering
- `bhd-cli export json --all` to export all engagements at once
- `bhd-cli export pdf` for professional PDF report generation (optional reportlab dependency)
- `bhd-cli export pdf --all` to export all engagement reports at once
- Storage abstraction layer (`storage.py`) for future SQLite backend support
- Comprehensive test coverage for export functionality

### Changed
- Export commands now display relative paths instead of absolute paths for portability
- Export --all mode processes engagements in deterministic alphabetical order
- Refactored data persistence into modular storage layer
- Updated README with "Security Engagement Documentation Framework" positioning
- Reorganized feature list by capability area in documentation

### Technical
- JSON remains current backend with SQLite-ready architecture
- reportlab is optional dependency (graceful degradation if not installed)
- Zero breaking changes; full backwards compatibility maintained
- Added pytest configuration to silence deprecation warnings

## [1.0.0] - 2026-02-15

### Added
- Initial production release
- Engagement management with scope and ROE tracking
- Finding management (add, edit, delete, search, filter)
- Risk scoring with guided impact/likelihood assessment
- Methodology tracking with phase-based workflow
- Home audit wizard for quick network assessments
- Markdown report generation with executive summaries
- Deterministic output with sorted findings
- Validation and guardrails for data quality
- Multi-engagement support with easy switching
- CLI-first design with no GUI dependencies

[1.1.0]: https://github.com/Taimaishu/bhd_app/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/Taimaishu/bhd_app/releases/tag/v1.0.0
