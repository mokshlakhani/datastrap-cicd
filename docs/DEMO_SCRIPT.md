# 5-minute demo script

**Before you start (do this once, not in the 5 minutes):** `make up`, finish `docs/SETUP.md`, run one build so images and caches are warm,
open three browser tabs: Jenkins job page (<http://localhost:8090>), SonarQube project (<http://localhost:9000>), the app (<http://localhost:8080>).

---

## Part A - A good commit goes all the way to production (about 2 min)

> "This is DataStrap, a Fitbit-style dashboard. My project adds an automatic pipeline around it, so every change is checked and delivered without anyone doing it by hand."

1. Make a harmless change and push it:
   ```bash
   echo "" >> docs/DEMO_SCRIPT.md && git commit -am "docs: small change" && git push
   ```
2. Switch to Jenkins. Say: *"GitHub just told Jenkins about my push using a webhook, so a build started by itself."*
3. Walk along the Stage View while it turns green:
   *"Checkout downloads the code. Install deps sets up Python and Node. Lint checks style. Tests run 27 Python tests plus the Node tests. SonarQube analyses quality, the Quality Gate stops us if it is bad, Docker builds the image, Trivy scans it for security holes."*
4. At the blue **Approve prod** box: *"Staging deployed automatically. Production needs a human to say yes."* Click **Deploy to prod**.
5. Show the green **Smoke test**. *"curl asked the running app for its pages, so we know it is really alive."*

## Part B - A bad commit is stopped (about 1.5 min)

> "Now what if someone pushes broken code?"

1. Run:
   ```bash
   make demo-fail
   ```
   *"This makes a branch called demo-fail with one test that always fails, and pushes it."*
2. In Jenkins start (or wait for) the `demo-fail` build. The **Test** stage turns **red**.
3. Point at the stage view: *"Everything after Test is grey. SonarQube, Docker build and Deploy never ran. Bad code can't reach production. Jenkins even lists which test failed under Test Result."*
4. Point at the app tab: *"Production is still running the last good version."*
5. Clean up afterwards: `make demo-fail-clean`.

## Part C - Reports and the running app (about 1.5 min)

1. **SonarQube tab:** *"This is the code quality report: bugs, vulnerabilities, code smells, duplicated code and test coverage. The Quality Gate is a pass/fail rule on top of these numbers."*
2. **Jenkins build page -> Artifacts:** *"Trivy's security report and the coverage report are saved with every build."*
3. **App tab (http://localhost:8080):** *"This is the deployed container. Docker checks its health every 10 seconds, and if a new version is unhealthy the pipeline puts the old one back automatically."*
4. Optional proof: `docker ps` shows `datastrap-prod` with `(healthy)`.

**Closing line:** *"Code goes in one end, and tested, scanned, deployed software comes out the other end, with a human approving production and the robots catching mistakes."*

## If something goes wrong live
* Build stuck at *Quality Gate*: the SonarQube webhook (SETUP step 11) is missing or wrong.
* Port 8080 busy: stop whatever uses it, or `make down` and rerun.
* Show the last successful build's screenshots (see the screenshots checklist in the README).
