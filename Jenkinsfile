#!groovy

@Library('emt-pipeline-lib@master') _

repo_creds = 'emt-jenkins-github-ssh'
repo_url = 'git@github.com:hlaf/fs.poormanscrashplanfs.git'

getPipelineConfig().compute_coverage = true

node('docker-slave') {
   
  stage('Checkout') {
	checkoutFromGit(repo_creds, repo_url)
  }
    
  stage('Acceptance') {
	initializeVirtualEnv()
	runTests(environment: 'coverage')
	publishCoberturaReport()
    verifyCoverage()
  }

  stage('Release') {
	  bumpPackageVersion(repo_creds,
						 'emt-jenkins',
						 'jenkinsci@emtegrity.com',
						 'src/fs_crashplanfs/__init__.py')
  }
}
