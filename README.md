# CrashTest: API Automation Framework with Qase TestOps

Automated test framework for Conduit API (RealWorld) with Qase TestOps integration.

## Project Structure
- `src/` - Models and configuration
- `tests/` - Test suites (User & Auth, Articles, Comments, Favorites, Profile, Tags)
- `docs/test-cases/` - Test case specifications in Markdown
- `scripts/` - Qase synchronization scripts
- `pytest.ini` - Pytest configuration
- `qase.config.json` - Qase TestOps configuration

## Running Tests
Run all tests with Qase TestOps reporting:
```bash
pytest -v tests/ --qase-mode=testops
```
