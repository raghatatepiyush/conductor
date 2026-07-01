# Test Design Principles

The judgment that separates a top-1% test suite from a box-checking one. Apply these when designing and writing tests in Phase 2. They are framework-agnostic; the examples use generic pseudocode.

## Contents
1. What to test: risk-based prioritization (incl. auditing existing coverage)
2. Where to test: choosing the level
3. Behavior over implementation
4. Assertion quality (incl. mutation testing)
5. Determinism, isolation, and speed
6. The edge-case catalog
7. Naming and structure
8. Test-data hygiene
9. The red-green discipline (and why)
10. Pruning judgment
11. Anti-patterns to avoid
12. Framework-family notes

---

## 1. What to test: risk-based prioritization

You cannot test everything, and trying to produces a slow, brittle suite nobody trusts. Spend effort where **likelihood of failure × cost of failure** is highest:

- Core business logic and money/data-integrity paths.
- Anything with branching, edge conditions, or tricky state.
- Boundaries between systems (APIs, parsers, serializers, auth).
- Code that has broken before, or that's about to change.

Deprioritize trivial glue, framework-guaranteed behavior, and getters/setters. Coverage percentage is a weak proxy — 100% coverage with weak assertions catches nothing. Aim for *meaningful* coverage of behavior that matters.

### Auditing existing coverage (backfill mode)

When the job is to raise coverage on code that already exists, first assess each source unit on two axes, then attack the worst corner first.

**Depth** of any existing tests:
- **UNTESTED** — no test exists.
- **SHALLOW** — happy path only.
- **ADEQUATE** — happy path + error cases.
- **THOROUGH** — happy path + errors + edge cases + integration at the boundary.

**Risk** of the unit:
- **HIGH** — auth, payments, data mutations, security, public API surface.
- **MEDIUM** — business logic, state management, data transformation.
- **LOW** — presentational UI, simple utilities, constants.

Rank gaps as: HIGH+UNTESTED → HIGH+SHALLOW → MEDIUM+UNTESTED → MEDIUM+SHALLOW → the rest. This stops you from spending effort decorating low-risk utilities while an untested payment path sits exposed.

## 2. Where to test: choosing the level

Prefer the **lowest level that can catch the bug**, because lower tests are faster, more isolated, and pinpoint failures precisely:

- **Unit** — one unit of logic, dependencies faked. Fast, many, the foundation.
- **Integration** — units wired together, real adapters where it matters (DB, queue). Fewer, slower, catch wiring bugs.
- **End-to-end / UI** — the whole system through its real interface. Fewest, slowest, most valuable for critical user journeys, most prone to flake.

Don't write an e2e test for what a unit test covers. Reserve the expensive levels for the things only they can verify (real integration, real user flow). When a bug spans layers, test the seam at the lowest layer that contains it.

## 3. Behavior over implementation

Assert on **observable behavior and contracts** — inputs, outputs, side effects, state transitions visible to callers — not on internal details like private fields, call order, or how a result was computed. Tests bound to implementation break on every refactor even when behavior is unchanged, which trains the team to ignore or delete them. The right question is: *"If someone rewrites the internals but preserves the contract, should this test still pass?"* If yes, you're testing behavior. Over-mocking is the usual culprit — mocking so much that you assert the implementation back to itself.

## 4. Assertion quality

A test earns its keep only if it can fail for the right reason.

- Assert **specific expected values/states**, not "didn't throw" or "is not null." `assert result == 42` beats `assert result is not None`.
- One logical behavior per test (you can have several assertions verifying that one behavior). When unrelated things share a test, a failure is ambiguous and later assertions never run.
- Verify the **full meaningful outcome**: return value *and* the side effects that matter (record written, event emitted, nothing else mutated).
- Prefer assertions that produce a **clear failure message** — expected-vs-actual, with context — so a red test explains itself without debugging.

**How to know your assertions actually bite:** the rigorous check is *mutation testing* — tools that deliberately inject small faults into the production code (flip a `>` to `>=`, return null, drop a line) and confirm a test fails for each. A high mutation score is far stronger evidence of quality than a high coverage number, which only proves a line ran, not that any assertion would have noticed it breaking. You won't run a full mutation campaign on every task, but use the mindset: for each test ask *"what wrong behavior would make this fail?"* — if the honest answer is "nothing," the test is theater.

## 5. Determinism, isolation, and speed

Flaky tests are worse than no tests: they erode trust in the entire suite until people rerun until green. Make every test deterministic and self-contained:

- **Control time** — inject clocks; never assert on real `now()`.
- **Control randomness** — seed it or inject it.
- **Control external I/O** — fake network, filesystem, and third-party calls at the unit/integration level; never depend on a live external service in a way that can flake (and never hit paid or destructive real endpoints from tests).
- **Control ordering and concurrency** — no test may depend on another test's side effects or on execution order. Each test sets up its own state and tears it down (or uses transactional rollback / fresh fixtures). This is what lets the suite run in parallel safely.
- **No shared mutable global state** leaking between tests.

**Speed is part of correctness**, because a suite that's too slow stops being run. Keep unit tests in the low-millisecond range (roughly <100ms each) and integration tests under about a second; anything dramatically slower usually means a real dependency leaked into a test that should have faked it, or the wrong level was chosen (§2). Reserve genuinely slow, full-stack tests for the few critical journeys that need them.

## 6. The edge-case catalog

Happy-path-only tests give false confidence. Systematically probe:

- **Boundary values** — at, just below, and just above each limit (0, 1, max, max+1, length boundaries).
- **Equivalence classes** — one representative per class of input that's treated the same, rather than dozens of near-duplicates.
- **Empty / null / missing** — empty string, empty collection, null, absent field, whitespace-only.
- **Invalid / malformed** — wrong type, out-of-range, malformed payloads, injection-shaped input.
- **Error and failure paths** — dependency throws, times out, returns an error; does the code handle it correctly? These are where real incidents hide.
- **Numeric pitfalls** — negatives, zero, overflow, floating-point rounding, division by zero.
- **Idempotency and repetition** — calling twice, retries, duplicate events.
- **Concurrency** — race conditions, ordering, partial failures (where relevant).
- **Unicode / encoding / locale / timezone** for text and time handling.

For UI work, also cover responsive breakpoints, loading/empty/error states, and basic accessibility (focus, labels, keyboard) where the project cares about it.

## 7. Naming and structure

A test is also documentation. Make the intent obvious at a glance.

- **Name the scenario and expected outcome**, e.g. `withdraw_more_than_balance_is_rejected` or `parses_empty_input_as_empty_list` — not `test1` or `testWithdraw`.
- **Structure as Arrange–Act–Assert** (or Given–When–Then): set up state, perform the action, verify the outcome — visibly separated.
- Keep tests short and linear; pull repeated setup into well-named fixtures/builders, but avoid hiding the thing under test behind layers of indirection.
- One reason to fail per test makes failures legible.

## 8. Test-data hygiene

- Use realistic but **minimal** data — only what the assertion needs.
- **Never commit secrets** (keys, tokens, real credentials) or real personal data into tests or fixtures.
- Don't depend on production data or on data that can change underneath you.
- Prefer builders/factories with sensible defaults over giant static fixtures, so each test overrides only the field it cares about.

## 9. The red-green discipline (and why)

When adding a test, see it **fail first, for the expected reason** before you make it pass. This is not ceremony: a test that was green from the moment you wrote it may be asserting nothing, testing the wrong thing, or silently passing due to a setup bug. The red step proves the test has teeth. Only then drive it to green — and in this skill, green is reached through correct test setup and expectations, *never* by editing production code. If the only way to green is a production change, you've located a real defect: stop and report it.

## 10. Pruning judgment

Stale tests — commented-out, obsolete, duplicated, or testing removed behavior — add noise and false confidence, so remove them when you're in the file. But pruning is a scalpel, not a chainsaw: **never delete a test that still meaningfully guards behavior** just to clean up, because that silently lowers safety. Before deleting, ask whether anything still depends on what it verifies. Net coverage of real behavior must not decrease. Record what you removed and why.

## 11. Anti-patterns to avoid

- **Assertion-free tests** — they execute code and check nothing; pure false confidence.
- **Testing the mock** — over-mocking until you assert your stubs back to yourself.
- **Brittle implementation coupling** — asserting private state or exact call sequences that change on refactor.
- **Flaky reliance on time/order/network** — see §5.
- **One mega-test** — dozens of unrelated assertions; ambiguous failures, early assertions mask later ones.
- **Snapshot-everything** — giant auto-approved snapshots nobody reads; they catch noise, not intent.
- **Logic in tests** — loops/conditionals/computation that can themselves be buggy; prefer explicit, table-style cases.
- **Copy-paste explosion** — near-identical tests where one parameterized/table-driven test would be clearer.

## 12. Framework-family notes

Conform to whichever the project uses; the principles above are constant across all of them:

- **xUnit-style** (JUnit, NUnit, pytest, Go `testing`, etc.) — arrange/act/assert, setup/teardown hooks, parameterized cases.
- **BDD / spec-style** (RSpec, Jasmine/Jest `describe`/`it`, Cucumber) — nested contexts with human-readable descriptions; let the description read as a sentence.
- **Table-driven** (idiomatic Go; easy anywhere) — one test body, many input/expected rows; ideal for equivalence classes and boundaries.
- **Property-based** (QuickCheck, Hypothesis, fast-check, proptest) — assert invariants over generated inputs; excellent for parsers, serializers, and pure logic. Reach for it when "for all inputs, X holds" captures the contract better than hand-picked cases.

Match the project's existing flavor so your tests look like they belong.
