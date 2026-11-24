# Repository instructions

## Project constraints

- Follow `SPEC.md`; use Python's standard library only.
- Implement hash tables without Python `dict`, `set`, or built-in `hash()`.
- Preserve one public mapping interface across the separate-chaining and
  linear-probing implementations.
- When comparing table strategies, use identical keys for both and state the
  theoretical successful and unsuccessful probe formulas. Collect counts from
  the production table implementations with resizing disabled or avoided.
- Generate short codes from monotonically increasing IDs encoded as base62.
  Never use a hash value as a short code.
- Add or update focused tests before implementation, and do not weaken tests to
  make an implementation pass.
- Run `make test` after behavior changes. Keep generated experiments reproducible.
- Keep error behavior explicit and consistent with the specification.

## Git workflow

- Use `main` as the stable branch and `develop` as the integration branch.
- Create each `feature/<issue-number>-<short-name>` branch from `develop`.
- Keep one numbered step per feature branch and report actual progress on its
  corresponding GitHub issue.
- Commit completed work with `Step N: 한 일 (#N)` and merge the feature branch
  into `develop`; push the feature commit and updated `develop`.
- Do not commit directly to `main`. Do not claim issue actions or manual checks
  that were not actually performed.

## Code quality

- Prefer small, clear standard-library implementations and meaningful boundary
  tests.
- Keep web handlers thin and reuse the core shortener and hash-table APIs.
- Do not add dependencies, generated caches, or unrelated files.
