# Signup returns “Authentication is temporarily unavailable”

This HTTP 503 is intentionally generic. It can represent database connectivity, missing migrated schema, or invalid stored authentication/configuration data. The browser message alone does not identify the cause.

A reproduced compatibility case: a legacy database contains MFA flags stored as the strings `true`/`false` or integers `1`/`0`. The new strict MFA configuration reader rejected these values before running signup. Canonical legacy values are now normalized during stored-configuration reads. Administrator API input remains strict, and unknown values still fail closed. Regression tests exercise actual signup with legacy disabled flags and verify that malformed settings create no account.

Server logs now emit `Authentication backend failure` with an operation, exception class, category and stack locations. They omit SQL parameters, raw stored values, passwords and tokens. Categories include:

- `database_schema`: check migration/startup logs and confirm the service uses the intended database.
- `database_locked`: inspect concurrent writes and database availability.
- `database`: inspect database service connectivity and the deployment's database configuration.
- `stored_data_validation`: use the stack location to identify the invalid configuration or credential record; inspect only the relevant fields.

For an affected deployment, update to an image containing this patch and reproduce signup. If the error remains, capture the corresponding backend diagnostic line and startup migration errors. Do not infer an SMTP or password problem from this message, and do not reset the database or disable MFA as a workaround. Actual production cause remains unconfirmed until those deployment diagnostics are available.
