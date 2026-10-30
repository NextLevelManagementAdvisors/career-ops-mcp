# Configuration: whose job search is this?

The server no longer assumes a particular owner. Owner name and target roles resolve, in order, from:

1. Environment variables
2. `CAREER_OPS_ROOT/config/profile.yml` (the career-ops profile file)
3. A neutral default ("the user", no archetypes)

| Value | Env var | profile.yml key |
|---|---|---|
| Owner name | `CAREER_OPS_OWNER_NAME` | `candidate.full_name` |
| Target archetypes | `CAREER_OPS_ARCHETYPES` (comma-separated) | `target_roles.archetypes[].name`, else `target_roles.primary` |

These feed the `evaluate_fit` prompt (North Star section and red-flag wording) and the server instructions. The prompt is built on each call, so editing `profile.yml` takes effect immediately. The server instructions are built at startup, so changing the name there needs a restart.

Missing-file errors now include the path that was checked, for example `applications.md not found at <CAREER_OPS_ROOT>/data/applications.md`.
