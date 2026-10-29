// Jenkinsfile = the recipe Jenkins follows. It lives in the repo, so the pipeline is versioned like code.
// "Declarative" style: a fixed, easy-to-read structure of pipeline { agent, options, stages, post }.
pipeline {
    // Run on any Jenkins machine; our single Jenkins container already has Python, Node, Docker CLI and the Sonar scanner.
    agent any

    // Settings for the whole pipeline.
    options {
        // Put a time stamp in front of every console line (helps to see which step is slow).
        timestamps()
        // Stop a build that hangs for more than 40 minutes.
        timeout(time: 40, unit: 'MINUTES')
        // Keep only the last 15 builds so the disk does not fill up.
        buildDiscarder(logRotator(numToKeepStr: '15'))
        // Never run two builds at once (they would fight over the same ports and containers).
        disableConcurrentBuilds()
    }

    // How a build is started automatically.
    triggers {
        // Preferred: GitHub calls Jenkins ("webhook") the moment someone pushes.
        githubPush()
        // Fallback: if the webhook cannot reach Jenkins, ask GitHub for changes every ~5 minutes.
        pollSCM('H/5 * * * *')
    }

    // Variables available in every stage.
    environment {
        // Name of the Docker image we build.
        IMAGE_NAME  = 'datastrap'
        // Folder (inside the workspace) where reports are collected.
        REPORTS_DIR = 'reports'
        // Tell Python tools to skip the "new pip version" notice in logs.
        PIP_DISABLE_PIP_VERSION_CHECK = '1'
        // Trivy (security scanner) runs as a Docker container of this exact version.
        TRIVY_IMAGE = 'aquasec/trivy:0.76.1'
    }

    stages {

        // ---------- 1. CHECKOUT ----------
        stage('Checkout') {
            steps {
                // Download the code of the branch that triggered this build.
                checkout scm
                // Run a few shell commands.
                script {
                    // Ask git for the 7-character id of the latest commit, e.g. "ab12cd3".
                    env.GIT_SHORT = sh(script: 'git rev-parse --short=7 HEAD', returnStdout: true).trim()
                    // Image tag = build number + commit id, e.g. "42-ab12cd3": tells exactly which code is inside.
                    env.IMAGE_TAG = "${env.BUILD_NUMBER}-${env.GIT_SHORT}"
                    // Decide once whether this build is for the main branch (only main may be deployed).
                    env.IS_MAIN = (env.GIT_BRANCH in ['origin/main', 'main']) ? 'true' : 'false'
                }
                // Print what we are about to build.
                echo "Building commit ${env.GIT_SHORT} from ${env.GIT_BRANCH} as image tag ${env.IMAGE_TAG}"
                // Create the folder for reports.
                sh 'mkdir -p "$REPORTS_DIR"'
            }
        }

        // ---------- 2. INSTALL DEPENDENCIES ----------
        stage('Install deps') {
            // These three installs do not depend on each other, so run them side by side to save time.
            parallel {
                // Python: create a private virtual environment and install app + test tools in it.
                stage('Python (venv)') {
                    steps {
                        // Make a clean venv in .venv (also needed by the mobile tests).
                        sh 'python3 -m venv .venv'
                        // Install the app's libraries and the dev tools (pytest, flake8) with exact versions.
                        sh '.venv/bin/pip install -q -r requirements.txt -r requirements-dev.txt'
                    }
                }
                // Node: install the phone app's libraries exactly as locked in package-lock.json.
                stage('npm ci: mobile') {
                    steps {
                        // "npm ci" = reproducible install (fails if lock file and package.json disagree).
                        dir('mobile') { sh 'npm ci --no-audit --no-fund' }
                    }
                }
                // Node: same for the token server.
                stage('npm ci: token-server') {
                    steps {
                        // Reproducible install of the token server's libraries.
                        dir('token-server') { sh 'npm ci --no-audit --no-fund' }
                    }
                }
            }
        }

        // ---------- 3. LINT ----------
        stage('Lint') {
            steps {
                // flake8 reads .flake8 and fails the build on real code problems (unused names, syntax slips, ...).
                sh '.venv/bin/flake8 .'
            }
        }

        // ---------- 4. TEST ----------
        stage('Test') {
            steps {
                // Python tests: write JUnit results (for Jenkins) and coverage.xml (for SonarQube).
                sh '.venv/bin/pytest --junitxml="$REPORTS_DIR/pytest.xml" --cov --cov-report=xml:coverage.xml --cov-report=term'
                // Token server tests: save the output, convert it to JUnit XML, then pass on the real exit code.
                sh '''
                    cd token-server
                    npm test > ../$REPORTS_DIR/token-server.log 2>&1; rc=$?
                    cat ../$REPORTS_DIR/token-server.log
                    ../.venv/bin/python ../ci/to_junit.py token-server ../$REPORTS_DIR/token-server.log $rc ../$REPORTS_DIR/token-server.xml
                    exit $rc
                '''
                // Mobile tests: "test:ci" is the version of `npm test` that needs no personal data.
                sh '''
                    cd mobile
                    npm run test:ci > ../$REPORTS_DIR/mobile.log 2>&1; rc=$?
                    cat ../$REPORTS_DIR/mobile.log
                    ../.venv/bin/python ../ci/to_junit.py mobile ../$REPORTS_DIR/mobile.log $rc ../$REPORTS_DIR/mobile.xml
                    exit $rc
                '''
            }
            post {
                // Publish test results even when a test failed, so Jenkins shows the red test names.
                always {
                    // Read every JUnit XML file in the reports folder.
                    junit allowEmptyResults: true, testResults: 'reports/*.xml'
                }
            }
        }

        // ---------- 5. SONARQUBE ANALYSIS ----------
        stage('SonarQube analysis') {
            steps {
                // 'sonarqube' = the server name you add in Manage Jenkins > System. It injects the URL and token.
                withSonarQubeEnv('sonarqube') {
                    // Scan the code and upload the result; settings come from sonar-project.properties, the login token from Jenkins.
                    sh 'sonar-scanner -Dsonar.token="$SONAR_AUTH_TOKEN" -Dsonar.projectVersion="$IMAGE_TAG"'
                }
            }
        }

        // ---------- 6. QUALITY GATE ----------
        stage('Quality Gate') {
            steps {
                // Wait (max 10 min) for SonarQube's verdict, which it sends back through the webhook you create.
                timeout(time: 10, unit: 'MINUTES') {
                    // abortPipeline: true = if the gate says FAILED, stop here. Nothing bad gets built or deployed.
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        // ---------- 7. DOCKER BUILD ----------
        stage('Docker build') {
            steps {
                // Build the image from the Dockerfile and give it two names: exact version and "latest".
                sh 'docker build -t "$IMAGE_NAME:$IMAGE_TAG" -t "$IMAGE_NAME:latest" .'
            }
        }

        // ---------- 8. CONTAINER SECURITY SCAN ----------
        stage('Security scan (Trivy)') {
            steps {
                // Report only: list HIGH problems into a file but never fail (exit code 0).
                sh '''
                    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v trivy-cache:/root/.cache/ \
                        "$TRIVY_IMAGE" image --quiet --severity HIGH --ignore-unfixed --exit-code 0 \
                        "$IMAGE_NAME:$IMAGE_TAG" > "$REPORTS_DIR/trivy-high.txt"
                    cat "$REPORTS_DIR/trivy-high.txt"
                '''
                // Gate: any CRITICAL problem that already has a fix makes Trivy exit with 1, which fails the build.
                sh '''
                    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v trivy-cache:/root/.cache/ \
                        "$TRIVY_IMAGE" image --quiet --severity CRITICAL --ignore-unfixed --exit-code 1 \
                        "$IMAGE_NAME:$IMAGE_TAG" | tee "$REPORTS_DIR/trivy-critical.txt"
                '''
            }
        }

        // ---------- 9a. DEPLOY TO STAGING (automatic, main branch only) ----------
        stage('Deploy: staging') {
            // Skip this stage for any branch other than main (e.g. the demo-fail branch).
            when { expression { env.IS_MAIN == 'true' } }
            steps {
                // Replace the staging container with the new image on port 8081; rolls back if unhealthy.
                sh 'ci/deploy.sh datastrap-staging 8081 "$IMAGE_NAME:$IMAGE_TAG"'
                // Check that staging really answers.
                sh 'ci/smoke_test.sh datastrap-staging 8081'
            }
        }

        // ---------- 9b. HUMAN APPROVAL ----------
        stage('Approve prod') {
            // Only for main.
            when { expression { env.IS_MAIN == 'true' } }
            steps {
                // Pause the pipeline until a person clicks "Deploy" (or "Abort"). Give up after 30 minutes.
                timeout(time: 30, unit: 'MINUTES') {
                    // The question shown in Jenkins, with the button text.
                    input message: "Staging works. Deploy build ${env.IMAGE_TAG} to PROD (port 8080)?", ok: 'Deploy to prod'
                }
            }
        }

        // ---------- 9c. DEPLOY TO PROD ----------
        stage('Deploy: prod') {
            // Only for main.
            when { expression { env.IS_MAIN == 'true' } }
            steps {
                // Same script, prod name and port 8080. Auto-rollback to the previous image if unhealthy.
                sh 'ci/deploy.sh datastrap-prod 8080 "$IMAGE_NAME:$IMAGE_TAG"'
            }
        }

        // ---------- 10. SMOKE TEST ----------
        stage('Smoke test') {
            // Only for main.
            when { expression { env.IS_MAIN == 'true' } }
            steps {
                // curl the running prod container: home page, demo data, and that private files stay hidden.
                sh 'ci/smoke_test.sh datastrap-prod 8080'
            }
        }
    }

    // Steps that run at the very end, whatever the result.
    post {
        // Always: keep the reports, then empty the workspace.
        always {
            // Save reports and coverage so they can be downloaded from the build page.
            archiveArtifacts artifacts: 'reports/**, coverage.xml', allowEmptyArchive: true
            // Delete the workspace to keep the disk tidy (the archived files are already saved).
            cleanWs()
        }
        // Everything passed.
        success {
            // Friendly message in the console log.
            echo "SUCCESS: build ${env.IMAGE_TAG} passed every stage."
        }
        // Something failed.
        failure {
            // Tell the reader where to look.
            echo "FAILURE: build ${env.BUILD_NUMBER} stopped. Open the first red stage above and read its log."
        }
    }
}
