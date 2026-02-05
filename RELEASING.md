## Releasing

This repo publishes:

- **npm**: `@get-continuum/sdk` (from `packages/sdk-ts`)
- **PyPI**: `continuum-local` (from `packages/local-py`)

### One-time setup (GitHub Actions secrets)

Set these repository secrets:

- `NPM_TOKEN`: npm publish token with access to `@get-continuum/*`
- `PYPI_API_TOKEN`: PyPI token with permission to publish `continuum-local`

### Cut a release

1. Bump versions:
   - `packages/sdk-ts/package.json`
   - `packages/local-py/pyproject.toml`
2. Commit the version bumps.
3. Create and push a tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Tag pushes trigger:

- `.github/workflows/release-npm.yml`
- `.github/workflows/release-pypi.yml`

