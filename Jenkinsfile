node(){
    try{
        properties([
            parameters([
                string(defaultValue: '', name: 'GoldCopy_Jenkins_URL', description: 'Enter Gold Copy Jenkins Instance URL'),
                string(defaultValue: '', name: 'GoldCopy_Username', description: 'Enter Gold Copy Jenkins Instance Username'),
                string(defaultValue: '', name: 'Remote_Jenkins_URL', description: 'Enter Remote Jenkins Instance URL'),
                string(defaultValue: '', name: 'Remote_Username', description: 'Enter Remote Jenkins Instance Username'),
                string(defaultValue: '', name: 'Remote_Host', description: 'Enter Remote Machine Host/Ipaddress'),
                string(defaultValue: '', name:'Remote_User', description: 'Enter Remote Machine User')
                ])
        ])    

        stage('Clean Workspace'){
            cleanWs()
        }

        stage('checkout'){
            checkout scm
        }

        stage('Install Python Modules'){
            def pexpect = sh returnStatus: true, script: 'python -c "import pexpect"'
            def jenkins = sh returnStatus: true, script: 'python -c "import jenkins"'
            def jenkinsapi = sh returnStatus: true, script: 'python -c "import jenkinsapi"'
            def xlwt = sh returnStatus: true, script: 'python -c "import xlwt"'
            def xlrd = sh returnStatus: true, script: 'python -c "import xlrd"'
            def xlutils = sh returnStatus: true, script: 'python -c "from xlutils.copy import copy"'

            if (pexpect == 1 || jenkins == 1 || jenkinsapi == 1 || xlwt == 1 || xlrd == 1 || xlutils ==1){
                install()
                echo "Installed Successfully"    
            }
            else
            echo "Already Installed"
        }	
        // Store GoldCopy Master Password in GoldCopy_Password secret variable 
        // Store Remote Jenkins Master Password in Remote_Password secret variable
        // Store Remote Machine Password in Remote_vm_Password secret variable
        stage('Python Script to match plugins information'){ 
            withCredentials([string(credentialsId: 'GoldCopy_Password', variable: 'GoldCopy_Password'), string(credentialsId: 'Remote_Password', variable: 'Remote_Password'), string(credentialsId: 'Remote_vm_Password', variable: 'Remote_vm_Password')]) {
            sh "python plugin.py $GoldCopy_Jenkins_URL $GoldCopy_Username $GoldCopy_Password $Remote_Jenkins_URL $Remote_Username $Remote_Password $Remote_Host $Remote_User $Remote_vm_Password"
            }  
        }
    }
    catch(Exception e){
        error "Error due to exception :  $e"
    }
    finally{
        stage('Send Report'){
            emailext attachmentsPattern: '**/report.csv', body: 'Please find the below report status for plugins configuration', 
            subject: 'Plugin Configuration Match Report - ${BUILD_STATUS}', to: 'chakresh.kolluru@infostretch.com'
        }
    }
    
}

def install(){
    sh "pip install pexpect"
    sh "pip install python-jenkins"
    sh "pip install jenkinsapi"
    sh "pip install xlwt"
    sh "pip install xlrd"
    sh "pip install xlutils"
}
