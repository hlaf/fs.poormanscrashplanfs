#!groovy

@Library('emt-pipeline-lib@master') _

repo_creds = '800f1808-4270-4189-bb73-d73c2379af8e'
repo_url = 'https://github.com/hlaf/fs.poormanscrashplanfs'

node('linux') {
   
  stage('Checkout') {
	checkoutFromGit(repo_creds, repo_url)
  }
    
  stage('Acceptance') {
    
    sh '''
        label="$(uname)"
        echo "The label is ${label}"

        case "${label}" in
          Darwin* )
            module load python
            ;;
          Linux* )
            module load python/2.7-linux-x64-centos-rpm
            ;;
        esac

        virtualenv master_venv

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
						 version_file='src/fs_crashplanfs/__init__.py')
  }
}
