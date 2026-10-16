# Task workflow

1. **Establish source:** inspect supplied ZIP, repo `main`, docs and exact versions; compare Git blob SHA.
2. **Map impact:** identify API/SQL/UI/gesture/navigation dependencies and regressions.
3. **Diagnose:** capture source evidence and distinguish confirmed cause from hypothesis.
4. **Plan:** define minimal patch and acceptance criteria before editing.
5. **Implement:** preserve working behavior, update linked files and docs together.
6. **Test:** static checks first, then mocked API/browser checks, then staging/device checks when available.
7. **Review:** inspect diff, secrets, archive layout, old overrides, duplicate handlers and API ownership.
8. **Deliver:** attach actual ZIP and `.env.example`, list changed files, pass/fail tests and unverified risks.
9. **Close:** only call an issue fixed after the acceptance criteria have evidence; otherwise label “code changed; device confirmation pending”.
