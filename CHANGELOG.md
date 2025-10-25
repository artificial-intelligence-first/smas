# Changelog

All notable changes to SMAS (SSOT Management Agents System) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial SMAS implementation with AGDD framework
- SSOTManagerMAG: Main orchestrator supporting query, update, validate, analyze requests
- ContentRetrieverSAG: Information retrieval with keyword-based search
- ContentValidatorSAG: Markdown linting and link validation
- TaxonomyManagerSAG: Terminology management for TAXONOMY.md
- CrossRefAnalyzerSAG: Inter-document reference analysis with orphan/cycle detection
- ContentUpdaterSAG: Content updates with Git operations and PR creation
- 12 JSON Schema contracts for agent input/output validation
- Test skeletons for all 6 agents
- AGDD stub for development (pending official package release)
- Project documentation (README, CONTRIBUTING, CODE_OF_CONDUCT)

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

## [0.1.0] - YYYY-MM-DD (To be released)

Initial release.
