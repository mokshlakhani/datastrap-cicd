# Viva cheat sheet

## 25 likely questions

**1. What is CI?**
Continuous Integration means every time someone pushes code, a server automatically builds it and runs tests. Problems are found within minutes instead of weeks later.

**2. What is CD?**
Continuous Delivery means the tested code is always ready to release, and Continuous Deployment means it is released automatically. In our project staging deploys automatically and prod waits for one human click, so it is Continuous Delivery.

**3. What is Jenkins?**
Jenkins is an automation server. It watches the repository and runs our pipeline (build, test, scan, deploy) whenever the code changes.

**4. What is a pipeline?**
A pipeline is the ordered list of steps code goes through from commit to running application. If one step fails, the later steps do not run.

**5. What is a pipeline stage?**
A stage is one named step of the pipeline, such as Lint or Test. Jenkins shows each stage as a box, green if it passed and red if it failed.

**6. Why do we use a Jenkinsfile?**
It stores the pipeline as a text file inside the repository ("pipeline as code"). That way it is versioned, reviewed and recreated anywhere, instead of being clicked together in the Jenkins UI.

**7. Declarative vs scripted pipeline?**
Declarative has a fixed, simple structure (`pipeline { stages { ... } }`) and is easier for beginners. Scripted is plain Groovy code with more freedom but is easier to get wrong. We use declarative.

**8. What is SonarQube?**
It is a tool that reads source code and reports bugs, security hotspots, code smells (hard-to-maintain code), duplication and test coverage. It does not run the program, it studies the code ("static analysis").

**9. What is a Quality Gate?**
A set of pass/fail rules, for example "no new bugs and enough test coverage on new code". If the code fails the gate, our pipeline aborts, so low-quality code is not delivered.

**10. How does Jenkins learn the Quality Gate result?**
SonarQube calls a webhook on Jenkins when its analysis finishes, and `waitForQualityGate` receives the verdict. Without that webhook the stage would wait until it times out.

**11. What is Trivy?**
Trivy is a security scanner for container images. It lists known vulnerabilities (CVEs) in the operating system packages and libraries inside the image. We fail on CRITICAL and only report HIGH.

**12. Why Docker?**
A container packages the app with everything it needs, so it runs the same on my laptop, in Jenkins and on a server. It also starts fast and is easy to replace or roll back.

**13. Image vs container?**
An image is the frozen recipe/package (like a class); a container is a running copy of it (like an object). One image can start many containers.

**14. Why tag images with build number and commit SHA?**
The tag tells exactly which build and which commit is running, and lets us roll back to an exact older version. Using only `latest` would hide that information.

**15. Webhook vs polling?**
With a webhook GitHub tells Jenkins immediately when something is pushed. With polling Jenkins asks GitHub every few minutes, which is slower and wasteful but works when GitHub cannot reach Jenkins (like on my laptop). We use a webhook with polling as backup.

**16. What happens if tests fail?**
The Test stage turns red and Jenkins stops the pipeline. SonarQube, Docker build and Deploy never run, so broken code cannot reach production. `make demo-fail` shows this.

**17. What is a health check?**
A small automatic question to the app ("are you alive?"). Docker's HEALTHCHECK fetches the home page every 10 seconds, and our deploy script waits until it says healthy.

**18. What happens if the new version is unhealthy?**
The deploy script stops it, prints its logs, and starts the previous image again (auto-rollback). The pipeline still ends as failed so nobody believes the deploy worked.

**19. Blue-green vs rolling deployment?**
Blue-green runs the new version next to the old one and switches traffic over at once, so rollback is instant. Rolling replaces instances one by one. Ours is simpler: stop old, start new, roll back if unhealthy, with a few seconds of downtime.

**20. What is a smoke test?**
A very quick test of the deployed system ("does it switch on without smoke?"). We use curl to check the home page, the demo data, and that a private file returns 404.

**21. What is linting and why do it?**
A linter (flake8) checks code for mistakes and style problems without running it. It catches things like unused variables early and keeps the code consistent.

**22. What is code coverage?**
The percentage of code lines that the tests actually run. Higher coverage means fewer untested places where bugs can hide. pytest-cov measures it and SonarQube displays it.

**23. Why is there a manual approval before prod?**
Automation is good for tests, but releasing to real users is a business decision. The `input` step pauses the pipeline until a person confirms.

**24. How are secrets handled?**
Never in the repository. The SonarQube token is stored in Jenkins Credentials, the database password is in a git-ignored `docker/.env` created from `.env.example`, and the app itself uses only demo data.

**25. What are the risks of mounting the Docker socket into Jenkins?**
Whoever can run commands in Jenkins can control Docker on the host (almost root access). It is fine for a lab on a laptop; in production you would use separate build agents.

## Explain it to a non-technical person

Imagine a bakery where every new recipe must pass inspection before it goes on sale. When a baker finishes a change, a robot assistant automatically tastes it (tests), checks the recipe for mistakes and bad habits (SonarQube), checks the ingredients for anything unsafe (Trivy), packs it in a sealed box that works the same everywhere (Docker), puts it on the shop shelf, and checks that the shelf display really works. If any check fails, the cake never reaches the customers, and if the new cake turns out spoiled the robot puts yesterday's cake back. A person only has to press one button to say "yes, sell it".

## Glossary

| Term | Meaning |
|---|---|
| Artifact | A file saved from a build (reports, coverage) so you can download it later |
| Branch | A separate line of work in git (`main` is the official one) |
| Build | One run of the pipeline |
| CI / CD | Continuous Integration / Continuous Delivery (or Deployment) |
| Container | A running, isolated copy of an image |
| Coverage | % of code lines executed by tests |
| CVE | A publicly known security vulnerability with an ID like CVE-2026-1234 |
| Docker Compose | Tool that starts several containers together from one YAML file |
| Dockerfile | The recipe for building an image |
| flake8 | Python linter |
| Image | A packaged, read-only template for containers |
| JUnit | A standard XML format for test results that Jenkins can display |
| Jenkinsfile | The pipeline definition, stored in the repository |
| Lint | Automatic checking of code style and obvious mistakes |
| Plugin | An add-on that gives Jenkins a new ability (e.g. SonarQube) |
| Quality Gate | Pass/fail rules SonarQube applies to the analysis |
| pytest | Python testing tool |
| Rollback | Going back to the previous working version |
| Smoke test | A quick "is it alive?" test after deploying |
| Stage | One named step in a pipeline |
| Static analysis | Examining code without running it |
| Trivy | Container image vulnerability scanner |
| Webhook | A message one system sends another when an event happens (push -> Jenkins) |
| Workspace | The folder where Jenkins checks out and builds the code |
