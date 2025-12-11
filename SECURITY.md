# Security Policy

## Reporting Security Issues

If you discover a security vulnerability, please **do not** open a public issue. Instead, contact the maintainers directly via a secure channel.

## Credential Management

### Environment Variables

**Never commit credentials to git.** All sensitive values must be stored in environment variables or secure secret management systems.

- Production credentials: Store in `.env` (gitignored) or your deployment platform's secret manager
- Demo/test credentials: Use environment variables with clear naming (e.g., `DEMO_SL10_USERNAME`, `DEMO_SL10_PASSWORD`)

### Required Environment Variables

See `.env.example` for the complete list of required variables.

## Exposed Credentials (Historical)

### Demo SyteLine Account (2024-2025)

**Status**: ⚠️ **Credentials were committed to git history**

- **Username**: `DevWorkshop06`
- **Password**: `WeTest$Code1`
- **Environment**: Demo/Test SyteLine 10 CloudSuite instance
- **Risk Level**: Low (demo/test account, not production)

**Affected Commits**: Multiple commits from `a084af2` through `df16a13` (Dec 2024)

**Remediation**:
1. ✅ **Source code redacted** (commit `34afa53`): All hardcoded credentials removed from current codebase
2. ⚠️ **Git history**: Old commits still contain these credentials (Option B: documented rotation instead of history rewrite)
3. 🔄 **Credential rotation required**: If this account is still active, rotate the password immediately

### Rotation Steps

If the demo account (`DevWorkshop06`) is still in use:

1. **Log into SyteLine 10 CloudSuite admin console**
2. **Change password** for user `DevWorkshop06`
3. **Update environment variables** in all deployment environments:
   ```bash
   DEMO_SL10_USERNAME=DevWorkshop06
   DEMO_SL10_PASSWORD=<new-password>
   ```
4. **Update Postman collection** with new credentials (stored as Postman variables, not in collection file)
5. **Verify** demo endpoints still work: `/api/demo/health`

### Prevention

We've implemented the following safeguards to prevent future credential leaks:

1. **Pre-commit hooks**: `gitleaks` scans commits before they're made
2. **CI/CD scanning**: GitHub Actions runs `gitleaks` on every push
3. **Code review**: All PRs are scanned for secrets
4. **Documentation**: `.env.example` shows required variables without values

## Secret Scanning

### Pre-commit

Install and run pre-commit hooks to catch secrets before committing:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### CI/CD

GitHub Actions automatically runs `gitleaks` on every push and pull request. The build will fail if secrets are detected.

### Manual Scanning

Run gitleaks manually:

```bash
# Install gitleaks
brew install gitleaks  # macOS
# or download from https://github.com/gitleaks/gitleaks/releases

# Scan current working directory
gitleaks detect --source . --verbose

# Scan specific commit
gitleaks detect --source . --log-opts "HEAD~1..HEAD"
```

## Best Practices

1. **Never hardcode credentials** in source code, even for demo/test accounts
2. **Use environment variables** for all sensitive values
3. **Use `.env.example`** to document required variables (without values)
4. **Rotate credentials immediately** if exposed
5. **Review git history** before making repos public
6. **Use secret management** (AWS Secrets Manager, HashiCorp Vault, etc.) for production

## Security Tools

- **Bandit**: Python security linter (runs in CI)
- **Gitleaks**: Secret scanning (pre-commit + CI)
- **Pre-commit hooks**: Automated checks before commits

## Questions?

Contact the maintainers for security-related questions or to report vulnerabilities.
