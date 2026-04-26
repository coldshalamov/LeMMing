## 2024-04-26 - [Initialization]
## 2024-04-26 - [Fix secrets shadow causing Admin Auth Bypass]
**Vulnerability:** A local variable named `secrets` shadowed the imported standard library `secrets` module, causing `secrets.compare_digest()` to raise an AttributeError. Since it threw a 500 error, authorization essentially failed closed, but it's a critical code logic bug preventing correct admin token checks.
**Learning:** Be careful when naming variables containing secret values that they don't shadow the widely used `import secrets` Python module.
**Prevention:** Use a different variable name such as `loaded_secrets` for JSON dictionary containing secrets, and use type linters that can catch shadowings if configured.
