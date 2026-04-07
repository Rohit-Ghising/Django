pipeline {
    agent any

    environment {
        BACKEND_IMAGE = 'gadgetzone-backend'
    }

    stages {
        stage('Build Backend Image') {
            steps {
                script {
                    def command = "docker build -t ${env.BACKEND_IMAGE}:${env.BUILD_NUMBER} -t ${env.BACKEND_IMAGE}:latest -f Dockerfile ."
                    if (isUnix()) {
                        sh command
                    } else {
                        bat command
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'Backend Docker image was built successfully.'
        }
    }
}
