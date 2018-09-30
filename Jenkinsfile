#!groovy

@Library('emt-pipeline-lib@master') _

repo_creds = 'emt-jenkins-git-ssh'
repo_url = 'git@github.com:hlaf/fs.poormanscrashplanfs.git'

node('linux') {
   
  stage('Checkout') {
	checkoutFromGit(repo_creds, repo_url)
  }
    
  stage('Acceptance') {
    
	initializeVirtualEnv()

    sh '''
        source master_venv/bin/activate

        # NOTE: Ignore aliases
        \\pip install tox --upgrade

        tox -e coverage
    '''

    publishJUnitReport()
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
