pipeline {
  agent any

  options {
    timestamps()
    disableConcurrentBuilds()
  }

  triggers {
    githubPush()
  }

  environment {
    APP_DIR = "/opt/route-analyzer"
    BRANCH  = "main"
    REPO_URL = "https://github.com/IdoKimhi/route-analyzer.git"
  }

  stages {
    stage('Deploy') {
      steps {
        sh '''
          set -euo pipefail

          if [ ! -d "$APP_DIR/.git" ]; then
            echo "First deploy: cloning into $APP_DIR"
            mkdir -p "$APP_DIR"
            git clone "$REPO_URL" "$APP_DIR"
          fi

          cd "$APP_DIR"

          echo "Fetching latest code..."
          git fetch origin
          git checkout "$BRANCH"
          git reset --hard "origin/$BRANCH"

          echo "Restarting containers..."
          docker compose down
          docker compose up -d --build

          echo "Deployed commit:"
          git rev-parse --short HEAD

          echo "Compose status:"
          docker compose ps
        '''
      }
    }
  }
}
