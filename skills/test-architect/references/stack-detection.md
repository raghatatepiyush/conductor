# Stack Detection

How to identify the language, test framework, runner, and run command in any repository — so the Test Architect conforms to the project instead of assuming an ecosystem. Use during Phase 1 discovery.

## Detection procedure

1. **Find the manifest / build files** at the repo root (table below) to identify the language and dependency manager.
2. **Look in those files for test dependencies and scripts** — the declared test framework and the canonical test command usually live here.
3. **Read 2–3 existing test files.** They are ground truth for the framework actually in use, the naming convention, where tests live, how fixtures and assertions are written, and the project's style. Mirror this.
4. **Read the CI config** (`.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/`, `azure-pipelines.yml`, `bitbucket-pipelines.yml`, etc.) to see how tests are *actually* invoked in practice — this is the most reliable run command.
5. **Check for a lockfile** to confirm the package manager (e.g. `package-lock.json` vs `yarn.lock` vs `pnpm-lock.yaml`).
6. If the stack is still ambiguous (no manifest, mixed languages, unconventional layout), **ask the user** rather than guessing — the wrong runner wastes the whole cycle.

## Ecosystem cheat-sheet

| Ecosystem | Manifest / build files | Common test frameworks | Typical test location | Typical run command |
| :--- | :--- | :--- | :--- | :--- |
| **JS / TS (Node)** | `package.json` (+ `package-lock.json` / `yarn.lock` / `pnpm-lock.yaml`) | Jest, Vitest, Mocha, Jasmine, AVA, node:test; Playwright/Cypress (e2e) | `__tests__/`, `test/`, or `*.test.ts` / `*.spec.ts` colocated | `npm test` / `yarn test` / `pnpm test`; or the runner directly |
| **Python** | `pyproject.toml`, `setup.py`, `requirements*.txt`, `tox.ini`, `Pipfile` | pytest, unittest, nose2; Hypothesis (property) | `tests/`, `test/`, or `test_*.py` / `*_test.py` | `pytest`, `python -m pytest`, `python -m unittest`, `tox` |
| **JVM (Java/Kotlin/Scala)** | `pom.xml` (Maven), `build.gradle(.kts)` (Gradle) | JUnit 4/5, TestNG, Spock, Kotest, ScalaTest | `src/test/java`, `src/test/kotlin` (mirrors `src/main`) | `mvn test`, `./gradlew test` |
| **Go** | `go.mod` | built-in `testing`, testify; table-driven idiom | **colocated** `*_test.go` beside source | `go test ./...` |
| **Rust** | `Cargo.toml` | built-in `#[test]`; proptest/quickcheck | **colocated** unit tests in-file under `#[cfg(test)]`; integration in `tests/` | `cargo test` |
| **Ruby** | `Gemfile`, `*.gemspec` | RSpec, Minitest | `spec/` (RSpec), `test/` (Minitest) | `bundle exec rspec`, `rake test` |
| **PHP** | `composer.json` | PHPUnit, Pest | `tests/` | `vendor/bin/phpunit`, `vendor/bin/pest`, `composer test` |
| **.NET (C#/F#)** | `*.csproj`, `*.fsproj`, `*.sln` | xUnit, NUnit, MSTest | separate `*.Tests` project | `dotnet test` |
| **Swift / iOS** | `Package.swift`, `*.xcodeproj`, `*.xcworkspace` | XCTest, Swift Testing | `Tests/` (SwiftPM) or a test target | `swift test`; `xcodebuild test` |
| **Android (Kotlin/Java)** | `build.gradle(.kts)` | JUnit + Espresso (UI), Robolectric | `src/test` (unit), `src/androidTest` (instrumented) | `./gradlew test`, `./gradlew connectedAndroidTest` |
| **C / C++** | `CMakeLists.txt`, `Makefile`, `meson.build`, `conanfile` | GoogleTest, Catch2, doctest, Boost.Test | `test/`, `tests/` | via `ctest`, or the built test binary |
| **Elixir** | `mix.exs` | ExUnit | `test/` | `mix test` |
| **Dart / Flutter** | `pubspec.yaml` | `package:test`, `flutter_test` | `test/` | `dart test`, `flutter test` |

The table is a starting map, not an exhaustive list — new and niche frameworks appear constantly. Existing test files and CI config always win over the table when they disagree.

## Test layout: colocated vs separate

This matters for boundary #1 ("test code only"). Two common layouts:

- **Separate test tree** (most JVM, Python, Ruby, PHP, .NET, JS-with-`__tests__`): tests live in their own directory. Your changes stay within it.
- **Colocated** (Go `foo_test.go` beside `foo.go`; Rust `#[cfg(test)]` blocks inside the source file; some JS `*.test.ts` beside the module): test code lives next to — or inside the same file as — production code. Here you **still only edit the test portions** (the `_test.go` file, the `#[cfg(test)] mod tests` block, the `*.test.ts` file). Never alter the surrounding production code. The boundary is about *what code you change*, not which file it sits in.

When in doubt about which lines are "test" vs "production" in a colocated file, the test framework's markers (`#[cfg(test)]`, `_test.go` suffix, `describe`/`it` blocks, test attributes/annotations) delimit your editable surface.

## Identifying the environment tier

For boundary #3, find what environment the tests point at:

- Config files and profiles: `.env*`, `config/<env>.*`, `application-<profile>.yml`, test settings modules.
- Environment variables referenced by the test setup (base URLs, DB hosts, API endpoints).
- Naming hints in URLs/hosts: `localhost`/`127.0.0.1` and `*.dev`/`*.uat`/`*.staging` vs anything that looks like production.

If you cannot tell with confidence whether a target is production or shared, treat it as the more dangerous tier and ask before running.
