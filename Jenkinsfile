pipeline {
    agent any

    option {
        buildDiscarder(logRotator(numToKeepStr: '5', daysToKeepStr: '5'))
        timestamp()
    }

    environment {
        DOCKER_IMAGE        = "sotsuba/lossteach-gdgaic-model-api"
        DOCKER_TAGS         = "latest"
        DOCKER_FULL_IMAGE   = "${DOCKER_IMAGE}:${DOCKER_TAGS}"
        
        DOCKER_REGISTRY_CREDENTIAL = 'dockerhub'
    }

    stages {
        stage("[Testing] Run tests") {
            // dir {
            //     docker {
            //         image 'python:3.9-slim'
            //     }
            //     step {
                    
            //         echo "Testing..."
            //         sh 'pip install -r requirements.txt && pytest'
            //     }
            // }
            steps {
                echo "The test stage is skipped."
            }
        }

        stage("Build the model API") {
            steps {
                dir ('app/model-api') {
                    scripts {
                        echo '[Building image]'
                        echo 'Building image for deployment...'
                        sh "docker build -t ${DOCKER_FULL_IMAGE} ."
                        echo 'Docker image built successfully.'

                        echo '[Pushing image]'
                        echo 'Pushing image for deployment...'
                        sh "docker push ${DOCKER_FULL_IMAGE}"
                        echo 'Docker image pushed successfully.'
                    }
                }
            }
        }
    }
}