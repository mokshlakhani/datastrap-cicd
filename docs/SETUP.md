# Setup from zero

Everything below was written for macOS / Windows (Docker Desktop) and Linux. Follow the numbers in order.
Each step says **"You should see"** so you know it worked.

## Part A - Start the tools

**1. Install Docker.** Docker Desktop (Mac/Windows) or Docker Engine + Compose plugin (Linux). Also install `git` and `make`.
*You should see:* `docker --version` and `docker compose version` both print a version.

**2. Give SonarQube enough memory settings (`vm.max_map_count`).** SonarQube's search engine refuses to start without it.
* Linux: `sudo sysctl -w vm.max_map_count=262144` (to keep it after reboot add `vm.max_map_count=262144` to `/etc/sysctl.conf`).
* Docker Desktop (Mac/Windows, WSL2): the setting lives in Docker's hidden VM. Usually the default is already fine. If SonarQube keeps restarting, run:
  `docker run --rm --privileged --pid=host alpine nsenter -t 1 -m -u -n -i sysctl -w vm.max_map_count=262144`
  (it resets when Docker Desktop restarts). On Windows with WSL2 you can instead run `wsl -d docker-desktop sysctl -w vm.max_map_count=262144`.
* Also give Docker Desktop at least **4 GB RAM** (Settings -> Resources).

**3. Get the code and start the stack.**
```bash
git clone https://github.com/mokshlakhani/datastrap-cicd.git
cd datastrap-cicd
make up
```
The first run builds the Jenkins image (about 3-6 minutes). *You should see:* three containers `jenkins`, `sonarqube`, `sonar-db` in `docker ps`.

**4. Check SonarQube is ready** (takes 1-2 minutes). Open <http://localhost:9000>.
*You should see:* a SonarQube login page. Log in with `admin` / `admin` and choose a new password when asked.

## Part B - Set up Jenkins

**5. Unlock Jenkins.** Open <http://localhost:8090>. It asks for an "Administrator password". Get it with:
```bash
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```
*You should see:* a "Customize Jenkins" screen after pasting it.

**6. Choose "Install suggested plugins"** and wait. Then create your admin user and accept the default Jenkins URL.
*You should see:* the Jenkins dashboard with "Welcome to Jenkins!".

**7. Check the extra plugins are there** (they are pre-installed by our image; the list is in `docker/jenkins/plugins.txt`).
Go to *Manage Jenkins -> Plugins -> Installed plugins* and look for:
Pipeline (`workflow-aggregator`), Git, GitHub, **SonarQube Scanner**, JUnit, Credentials Binding, Pipeline Stage View, Timestamper, Workspace Cleanup.
*You should see:* all of them in the list. If one is missing, install it from the "Available plugins" tab and restart.

**8. Create a SonarQube token.** In SonarQube: click your avatar (top right) -> *My Account* -> *Security* -> *Generate Tokens*,
name `jenkins`, type **Global Analysis Token** (or User Token), then **copy the token now** - it is shown only once.

**9. Store the token in Jenkins.** *Manage Jenkins -> Credentials -> System -> Global credentials -> Add Credentials*:
Kind **Secret text**, Secret = the token, ID `sonar-token`, then *Create*.
*You should see:* `sonar-token` in the credentials list. (The token never goes into the repo.)

**10. Tell Jenkins where SonarQube is.** *Manage Jenkins -> System -> SonarQube servers -> Add SonarQube*:
* Name: `sonarqube` (**must be exactly this**, the Jenkinsfile uses it)
* Server URL: `http://sonarqube:9000` (container name, not localhost)
* Server authentication token: choose `sonar-token`

Tick "Environment variables: Enable injection of SonarQube server configuration", then *Save*.

**11. Create the SonarQube webhook back to Jenkins** (this is how the Quality Gate stage hears the verdict).
In SonarQube: *Administration -> Configuration -> Webhooks -> Create*:
Name `jenkins`, URL `http://jenkins:8080/sonarqube-webhook/` (keep the trailing slash), *Create*.
*You should see:* the webhook listed. Without it, the Quality Gate stage waits until it times out.

**12. Create the pipeline job.** *New Item* -> name `datastrap-cicd` -> **Pipeline** -> OK. Then:
* *Pipeline -> Definition:* **Pipeline script from SCM**
* SCM: **Git**, Repository URL: `https://github.com/mokshlakhani/datastrap-cicd.git` (public repo, no credentials needed)
* Branch Specifier: `*/*` (so every branch is built; only `main` deploys)
* Script Path: `Jenkinsfile`
* Under *Build Triggers* tick **GitHub hook trigger for GITScm polling** and **Poll SCM** (schedule `H/5 * * * *`). The Jenkinsfile also declares these after the first run.
*Save*.

**13. Run it.** Click **Build Now**.
*You should see:* the Stage View filling in green boxes: Checkout, Install deps, Lint, Test, SonarQube analysis, Quality Gate, Docker build, Security scan (Trivy), Deploy: staging.
It then **pauses at "Approve prod"** (blue). Hover the box and click **Deploy to prod**.
Afterwards open <http://localhost:8081> (staging) and <http://localhost:8080> (prod): you should see the DataStrap dashboard with demo data.

**14. Look at the reports.** On the build page: *Test Result* (JUnit), *Artifacts* (coverage, Trivy reports).
In SonarQube open the project `datastrap-cicd`: *You should see* Quality Gate **Passed**, bugs, code smells, coverage and duplications.
(Note: the original code already contains some issues. The default quality gate only judges *new* code, so the first run passes.)

## Part C - Automatic builds on every push

**15. Jenkins is on your laptop, so GitHub can't reach it. Use ngrok** (free): install it, then run `ngrok http 8090`.
*You should see:* a public address like `https://abcd-12-34.ngrok-free.app`.

**16. Add the GitHub webhook.** GitHub repo -> *Settings -> Webhooks -> Add webhook*:
Payload URL `https://<your-ngrok-address>/github-webhook/`, Content type `application/json`, event **Just the push event**, *Add webhook*.
*You should see:* a green tick next to the webhook after GitHub's first "ping". The ngrok address changes every time you restart ngrok, so update the webhook then.

**17. Test it:** make a tiny commit and `git push`. A new build should appear in Jenkins within seconds.
If you skip steps 15-16, the **Poll SCM** fallback still starts a build within about 5 minutes.

## Stopping and cleaning up
```bash
make down                                              # stop everything, keep data
docker compose -f docker/docker-compose.yml down -v    # stop and DELETE all Jenkins/SonarQube data
```
