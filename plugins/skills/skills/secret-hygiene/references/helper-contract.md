# Helper contract

secret-hygiene ships no helper. When a project needs one, the agent writes it in the
project, in the project's own language, and the helper meets every requirement below.

1. **Secret source.** The helper reads the env file as data: no `source`, no command
   execution, no shell interpolation. It names the format it supports, for example
   "dotenv: `KEY=value` lines, `#` comments, optional single or double quotes".
2. **Allowed service.** The helper sends the credential to one named service or host and
   to no other destination.
3. **Defined result fields.** The helper prints only the fields its caller needs, such as
   the status code, a count, or an ID, never the full response.
4. **Sanitized output.** Everything on stdout and stderr passes a check that masks the
   credential in every form it travels in: raw, URL-encoded, and Base64 of the value and
   of `<API_EMAIL>:<API_TOKEN>` in the standard and URL-safe alphabets, with and without
   padding.
5. **Safe errors.** Errors carry a status and a short reason, never the raw response,
   headers, or a traceback. When no safe result can be formed, the helper exits with a
   fixed safe message and a non-zero code.
6. **No credentials across origins.** The helper handles redirects itself. A redirect to
   another origin (a different scheme, host, or port) does not receive the credential:
   the helper follows it with a request that carries no Authorization header, cookies, or
   URL credentials, or stops and reports the location without its query string.
7. **No argv, no leaking children.** The secret never appears in the helper's own argv or
   in the argv of a process it starts, and child processes that do not need it do not
   inherit it.

## Example interface

```text
scripts/<service>-api METHOD PATH [BODY_FILE]
```

- Reads `<API_TOKEN>` (and `<API_EMAIL>` for Basic auth) from `<ENV_FILE>`.
- Sends the request only to `<SERVICE_HOST>`.
- Prints `status=<code>` plus the named fields of the response, one per line.
- On failure prints `error=<code> <short reason>` and exits non-zero.

A presence check follows the same shape: `scripts/<service>-api --check-keys` prints
`<KEY_NAME>: set` or `<KEY_NAME>: missing` for each expected key.
