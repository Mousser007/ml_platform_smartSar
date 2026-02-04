pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python Environment') {
            steps {
                sh '''
                python3 -m venv venv
                . venv/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }

        stage('Scraping Tayara') {
            steps {
                sh '''
                . venv/bin/activate
                python scraping/tayara_scraper.py
                '''
            }
        }

        stage('Data Preprocessing') {
            steps {
                sh '''
                . venv/bin/activate
                python preprocessing/clean_data.py
                '''
            }
        }

        stage('Feature Engineering') {
            steps {
                sh '''
                . venv/bin/activate
                python features/feature_engineering.py
                '''
            }
        }

        stage('Train Price Model') {
            steps {
                sh '''
                . venv/bin/activate
                python models/train_price_model.py
                '''
            }
        }

        stage('Train Opportunity Model') {
            steps {
                sh '''
                . venv/bin/activate
                python models/train_opportunity_model.py
                '''
            }
        }

        stage('Evaluate Models') {
            steps {
                sh '''
                . venv/bin/activate
                python evaluation/evaluate.py
                '''
            }
        }

        stage('Archive Artifacts') {
            steps {
                archiveArtifacts artifacts: 'models/*.pkl, evaluation/*.json'
            }
        }
    }

    post {
        always {
            cleanWs()
        }
        failure {
            echo 'Pipeline failed – model quality or script error'
        }
        success {
            echo 'Pipeline completed successfully'
        }
    }
}
