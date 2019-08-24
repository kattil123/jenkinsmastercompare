from jenkinsapi.jenkins import Jenkins #pip3 install jenkinsapi
import sys
import xlwt
import xlrd 
from xlutils.copy import copy
import xml.etree.ElementTree as ET
from pexpect import pxssh # pip3 install pexpect
import jenkins # pip3 install python-jenkins
import os

def check():
   print("./plugin1.py <GoldCopyMaster_URL> <GoldCopyMaster_Username> <GoldCopyMaster_Password> <RemoteJenkins_URL> <RemoteJenkins_Username> <RemoteJenkins_Password> <Remote_Host> <Remote_User> <Remote_Password>" )
   sys.exit(0)    


def save_goldcopy_info(url,username,password):
   GoldCopy=Jenkins(url,username,password)
   data1= GoldCopy.plugins._data

   # Created a csv file to store plugin name and version
   fg = open("plugin.csv","w")
   fg.write("Plugin Name,Version\n\n")

   for i in data1['plugins']:
       fg.write(i['shortName']+","+i['version'] )
       fg.write('\n')
   fg.close()   


def match_plugins(url,username,password):
   RemoteInstance=Jenkins(url,username,password) 
   data2= RemoteInstance.plugins._data

   # Reading Gold Copy Instance Plugins Information from plugin.csv file and map to other instance
   f1 = open("plugin.csv","r")
   f = f1.readlines()
   
   # Generating Report to report.csv file 
   excel_file = xlwt.Workbook()
   sheet = excel_file.add_sheet('jenkins')
   #sheet.set_column(1,3,25)
   row = 0
   col = 0
   
   # Here f[2:] implies to read file from line 3 of plugin.csv file. So that it ignores reading titles[Plugin Name,Version]
   print("Total Plugins in Gold Copy Jenkins Instance -- "+str(len(f[2:]))) 
   print("-----------------------------------------------------------------")
   print("Total Plugins in Remote Jenkins Instance -- "+str(len(data2['plugins'])))
   print("-----------------------------------------------------------------")
   
   count1 = 0           # To get total number of matched plugins
   count2 = 0           # To get total number of unmatched plugins due to version
   count3 = 0           # To get total number of unavailable plugins

   # Dictionary to store the list of matched and unmatched plugins
   result = {"matched": [], "unmatched": [], "unavailable": [] }
   
   # Loop for matching the plugins 
   for i in f[2:]:
       count = 0    
       for j in data2['plugins']:
           if (i.split(",")[0] == j['shortName'] and i.split(",")[1].strip() == j['version']):
               result['matched'].append(dict({"name": i.split(",")[0], "version": i.split(",")[1].strip()}))
               count1+=1
           if (i.split(",")[0] == j['shortName'] and i.split(",")[1].strip() != j['version']):        
               result['unmatched'].append(dict({"name": i.split(",")[0], "version1": i.split(",")[1].strip(), "version2": j['version']}))
               count2+=1
           if (i.split(",")[0] == j['shortName']):
               count = 1  
       if count == 0:     
          result['unavailable'].append(dict({"name": i.split(",")[0], "version": i.split(",")[1].strip()}))  
          count3+=1   

   style = xlwt.easyxf('align: vert center;''font: colour black;')
   print("***** Plugins Matched ******")
   sheet.write(row,col,"Plugins Matched",xlwt.easyxf('align: vert center;''font: colour green, bold True;'))
   sheet.write(row+1,col,"Plugin Name",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   sheet.write(row+1,col+1,"Version",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   row+=1   # To give line space
   for i in result['matched']:
      print("Plugin Name  : "+ i['name']+ "   Version  : "+i['version'])
      sheet.write(row+1,col,i['name'],style)
      sheet.write(row+1,col+1,i['version'],style)
      row+=1 

   print("-----------------------------------------------------------------")
   print("Total Plugins Matched with version is  -- "+ str(count1))
   print("-----------------------------------------------------------------")
   
   print("****** Plugin UnMatched due to version *******")
   row+=1 # To give line space   
   sheet.write(row+1,col,"Plugins UnMatched due to version",xlwt.easyxf('align: vert center;''font: colour red, bold True;'))
   sheet.write(row+2,col,"Plugin Name",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   sheet.write(row+2,col+1,"Gold Copy Jenkins Instance Version",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   sheet.write(row+2,col+2,"Remote Jenkins Instance Version",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   row+=2   # To give line space
   for i in result['unmatched']:
      print("Plugin Name   : "+i['name']+ "  Gold Copy Master version  : "+i['version1']+ "  Remote Jenkins Version  : "+i['version2'])   
      sheet.write(row+1,col,i['name'],style)
      sheet.write(row+1,col+1,i['version1'],style)
      sheet.write(row+1,col+2,i['version2'],style)
      row+=1 

   print("-----------------------------------------------------------------")
   print("Total Unmatched Plugins with different version is -- "+str(count2))
   print("-----------------------------------------------------------------")

   print("*****Plugins Unavailable******")
   row+=2 # To give line space   
   sheet.write(row,col,"Plugins Unavailable",xlwt.easyxf('align: vert center;''font: colour red, bold True;'))
   sheet.write(row+1,col,"Plugin Name",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   sheet.write(row+1,col+1,"Version",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   row+=1   # To give line space
   for i in result['unavailable']:
      print("Plugin Name :  "+i['name']+ " Version : "+i['version'])
      sheet.write(row+1,col,i['name'],style)
      sheet.write(row+1,col+1,i['version'],style)
      row+=1 
   
   f1.close()
   excel_file.save('final_report.xlsx')
   print("-----------------------------------------------------------------")
   print("Total Unavailable Plugins  -- "+str(count3))
   print("-----------------------------------------------------------------")


def match_shared_libraries(master,remote,remote_host,remote_user,remote_password):  
   master_home = master.run_script('println(System.getenv("JENKINS_HOME"))')
   remote_home = remote.run_script('println(System.getenv("JENKINS_HOME"))')    
   gsl1 = ET.parse(master_home+'/org.jenkinsci.plugins.workflow.libs.GlobalLibraries.xml').getroot()
   ssh = pxssh.pxssh()
   ssh.login(remote_host,remote_user,remote_password,sync_multiplier=5)
   ssh.sendline('sudo cat '+remote_home+'/org.jenkinsci.plugins.workflow.libs.GlobalLibraries.xml') 
   ssh.prompt() # match the prompt
   xmlstr = str("".join((ssh.before).split('\r\n')[1:]))
   ssh.logout()              
   gsl2 = ET.fromstring(xmlstr)
  # print("----------GLOBAL SHARED LIBRARIES-------------------")
   rb = xlrd.open_workbook('final_report.xlsx',formatting_info=True)
   r_sheet = rb.sheet_by_index(0) 
   r = r_sheet.nrows
   col = 0
   wb = copy(rb) 
   sheet = wb.get_sheet('jenkins') 
   
   # Dictionary to store the list of matched and unmatched global shared libraries 
   result = {"matched": [], "unmatched_cred": [], "unmatched_remote": [],"unavailable": [] }
   
   # Loop for matching Global Shared Libraries        
   for i in gsl1.find('libraries').iter('org.jenkinsci.plugins.workflow.libs.LibraryConfiguration'):
      count = 0   
      for j in gsl2.find('libraries').iter('org.jenkinsci.plugins.workflow.libs.LibraryConfiguration'):
          if i.find('name').text == j.find('name').text and i.find('retriever').find('scm').find('remote').text == j.find('retriever').find('scm').find('remote').text:
             credential_id1 = i.find('retriever').find('scm').find('credentialsId').text
             credential_id2 = j.find('retriever').find('scm').find('credentialsId').text
             cr1 = ET.parse(master_home+'/credentials.xml').getroot()
             for z in cr1.find('domainCredentialsMap').find('entry').find('java.util.concurrent.CopyOnWriteArrayList').iter('com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl'):
                if credential_id1 == z.find('id').text:
                   data = 'println(hudson.util.Secret.decrypt("{}"))'.format(z.find('password').text)
                   p1 = master.run_script(data)
                   user1 = z.find('username').text

             ssh = pxssh.pxssh()
             ssh.login(remote_host,remote_user,remote_password,sync_multiplier=5)
             ssh.sendline('sudo cat '+remote_home+'/credentials.xml')
             ssh.prompt()
             xmlstr1 =  str("".join((ssh.before).split('\r\n')[1:]))
             ssh.logout()
             cr2 = ET.fromstring(xmlstr1)
             for z in cr2.find('domainCredentialsMap').find('entry').find('java.util.concurrent.CopyOnWriteArrayList').iter('com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl'):
                if credential_id2 == z.find('id').text:     
                   data = 'println(hudson.util.Secret.decrypt("{}"))'.format(z.find('password').text)
                   p2 = remote.run_script(data)
                   user2 = z.find('username').text
             if user1 == user2 and p1 == p2:
                result["matched"].append(dict({"name": i.find('name').text}))   
             if user1 != user2 or p1 == p2:   
                result["unmatched_cred"].append(dict({"name": i.find('name').text}))   
          if i.find('name').text == j.find('name').text and i.find('retriever').find('scm').find('remote').text != j.find('retriever').find('scm').find('remote').text:
             result["unmatched_remote"].append(dict({"name": i.find('name').text,"remote1": i.find('retriever').find('scm').find('remote').text,"remote2": j.find('retriever').find('scm').find('remote').text}))      
          if i.find('name').text == j.find('name').text:
             count = 1
      if count == 0:
         result["unavailable"].append(dict({"name" : i.find('name').text}))  

   style = xlwt.easyxf('align: vert center;''font: colour black;')
   print("*****Global Shared Libraries Matched*****")
   r+=1 # To give line space
   sheet.write(r,col,"Global Shared Libraries Matched",xlwt.easyxf('align: vert center;''font: colour green, bold True;'))
   sheet.write(r+1,col,"Library Name",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   r+=2   # To give line space  
   for i in result['matched']:
      print("Library Name  : "+ i['name'])
      sheet.write(r+1,col,i['name'],style)
      r+=1   
      
   print("*****Global Shared Libraries unmatched due to different credentials*****")      
   r+=1 # To give line space
   sheet.write(r,col,"Global Shared Libraries unmatched due to different credentials",xlwt.easyxf('align: vert center;''font: colour red, bold True;'))
   sheet.write(r+1,col,"Library Name",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   r+=2   # To give line space         
   for i in result["unmatched_cred"]:
      print("Library Name  : "+i['name'])
      sheet.write(r+1,col,i['name'],style)
      r+=1   

   print("*****Global Shared Libraries unmatched due to different remote*****")
   r+=2 # To give line space
   sheet.write(r,col,"Global Shared Libraries unmatched due to different remote",xlwt.easyxf('align: vert center;''font: colour red, bold True;'))
   sheet.write(r+1,col,"Library Name",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   sheet.write(r+1,col+1,"Gold Copy Instance Remote Url",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   sheet.write(r+1,col+2,"Remote Jenkins Url",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   r+=2   # To give line space             
   for i in result["unmatched_remote"]:
      print("Library Name  : "+ i['name']+" Gold Copy Remote Url : "+ i['remote1']+"  Remote Jenkins Url  : "+ i['remote2'])
      sheet.write(r+1,col,i['name'],style)
      sheet.write(r+1,col+1,i['remote1'],style) 
      sheet.write(r+1,col+2,i['remote2'],style)
      r+=1 

   print("******Global Shared Libraries Unavailable******")
   r+=2 # To give line space
   sheet.write(r,col,"Global Shared Libraries unavailable",xlwt.easyxf('align: vert center;''font: colour red, bold True;'))
   sheet.write(r+1,col,"Library Name",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   r+=2   # To give line space             
   for i in result["unavailable"]:
      print("Library Name  : "+i['name'])
      sheet.write(r+1,col,i['name'],style)
      r+=1 

   wb.save('final_report.xlsx')    

def match_github_servers(master,remote,remote_host,remote_user,remote_password):
   master_home = master.run_script('println(System.getenv("JENKINS_HOME"))')
   remote_home = remote.run_script('println(System.getenv("JENKINS_HOME"))')
   g1 = ET.parse(master_home+'/github-plugin-configuration.xml').getroot()
   ssh = pxssh.pxssh()
   ssh.login(remote_host,remote_user,remote_password,sync_multiplier=5)
   ssh.sendline('sudo cat '+remote_home+'/github-plugin-configuration.xml') 
   ssh.prompt() # match the prompt
   xmlstr = str("".join((ssh.before).split('\r\n')[1:]))
   ssh.logout()              
   g2 = ET.fromstring(xmlstr)

   rb = xlrd.open_workbook('final_report.xlsx',formatting_info=True)
   r_sheet = rb.sheet_by_index(0) 
   r = r_sheet.nrows
   col = 0
   wb = copy(rb) 
   sheet = wb.get_sheet('jenkins') 
   
   # Dictionary to store the list of matched and unmatched github servers
   result = {"matched": [], "unmatched_cred": [], "unmatched_remote": [],"unavailable": [] }
   

   # Loop for matching Github Servers
   for i in g1.find('configs').iter('github-server-config'):
      count = 0
      for j in g2.find('configs').iter('github-server-config'):
         if i.find('name').text == j.find('name').text and i.find('apiUrl').text == j.find('apiUrl').text:       
            credential_id1 = i.find('credentialsId').text
            credential_id2 = j.find('credentialsId').text
            cr1 = ET.parse(master_home+'/credentials.xml').getroot()
            p1 =""
            for z in cr1.find('domainCredentialsMap').iter('entry'):
               if z.find('list') == None:
                      continue
               for y in z.find('list').iter('org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl'):
                 if credential_id1 == y.find('id').text:
                    data = 'println(hudson.util.Secret.decrypt("{}"))'.format(y.find('secret').text)
                    p1 = master.run_script(data)
            ssh = pxssh.pxssh()
            ssh.login(remote_host,remote_user,remote_password,sync_multiplier=5)
            ssh.sendline('sudo cat '+remote_home+'/credentials.xml')
            ssh.prompt()
            xmlstr1 =  str("".join((ssh.before).split('\r\n')[1:]))
            ssh.logout()
            cr2 = ET.fromstring(xmlstr1)
            p2 = ""
            for z in cr2.find('domainCredentialsMap').iter('entry'):
               if z.find('list') == None:
                  continue    
               for y in z.find('list').iter('org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl'):
                if credential_id2 == y.find('id').text:     
                     data = 'println(hudson.util.Secret.decrypt("{}"))'.format(y.find('secret').text)
                     p2 = remote.run_script(data)
            if p1 == p2:
               result["matched"].append(dict({"name": i.find('name').text}))
            else:
               result["unmatched_cred"].append(dict({"name":i.find('name').text}))
         if i.find('name').text == j.find('name').text and i.find('apiUrl').text != j.find('apiUrl').text:           
            result["unmatched_remote"].append(dict({"name": i.find('name').text,"remote1":i.find('apiUrl').text,"remote2":j.find('apiUrl').text})) 
         if i.find('name').text == j.find('name').text:           
            count = 1
      if count == 0:
             result["unavailable"].append(dict({"name":i.find('name').text}))

   style = xlwt.easyxf('align: vert center;''font: colour black;')
   print("******Github Servers Matched******")
   r+=1 # To give line space
   sheet.write(r,col,"Github Servers Matched",xlwt.easyxf('align: vert center;''font: colour green, bold True;'))
   sheet.write(r+1,col,"Server Name",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   r+=2   # To give line space  
   for i in result['matched']:
      print("Server Name  : "+ i['name'])
      sheet.write(r+1,col,i['name'],style)
      r+=1   

   print("*****Github Servers unmatched due to different credentials*****")      
   r+=2# To give line space
   sheet.write(r,col,"Github Servers unmatched due to different credentials",xlwt.easyxf('align: vert center;''font: colour red, bold True;'))
   sheet.write(r+1,col,"Server Name",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   r+=2   # To give line space         
   for i in result["unmatched_cred"]:
      print("Server Name  : "+i['name'])
      sheet.write(r+1,col,i['name'],style)
      r+=1   

   print("*****Github Servers unmatched due to different remote*****")
   r+=2 # To give line space
   sheet.write(r,col,"Github Servers unmatched due to different remote",xlwt.easyxf('align: vert center;''font: colour red, bold True;'))
   sheet.write(r+1,col,"Server Name",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   sheet.write(r+1,col+1,"Gold Copy Instance Remote Url",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   sheet.write(r+1,col+2,"Remote Jenkins Url",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   r+=2   # To give line space             
   for i in result["unmatched_remote"]:
      print("Server Name  : "+ i['name']+" Gold Copy Remote Url : "+ i['remote1']+"  Remote Jenkins Url  : "+ i['remote2'])
      sheet.write(r+1,col,i['name'],style)
      sheet.write(r+1,col+1,i['remote1'],style) 
      sheet.write(r+1,col+2,i['remote2'],style)
      r+=1 

   print("******Github Servers Unavailable******")
   r+=2 # To give line space
   sheet.write(r,col,"Github Servers unavailable",xlwt.easyxf('align: vert center;''font: colour red, bold True;'))
   sheet.write(r+1,col,"Server Name",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   r+=2   # To give line space             
   for i in result["unavailable"]:
      print("Server Name  : "+i['name'])
      sheet.write(r+1,col,i['name'],style)
      r+=1 

   wb.save('final_report.xlsx')    


def check_maven_installations(master,remote,remote_host,remote_user,remote_password):
   #master_home = master.run_script('println(System.getenv("JENKINS_HOME"))')
   remote_home = remote.run_script('println(System.getenv("JENKINS_HOME"))')
   #m1 = ET.parse(master_home+'/hudson.tasks.Maven.xml').getroot()
   ssh = pxssh.pxssh()
   ssh.login(remote_host,remote_user,remote_password,sync_multiplier=5)
   ssh.sendline('sudo cat '+remote_home+'/hudson.tasks.Maven.xml') 
   ssh.prompt() # match the prompt
   xmlstr = str("".join((ssh.before).split('\r\n')[1:]))
   ssh.logout()              
   m2 = ET.fromstring(xmlstr)
   rb = xlrd.open_workbook('final_report.xlsx',formatting_info=True)
   r_sheet = rb.sheet_by_index(0) 
   r = r_sheet.nrows
   col = 0
   wb = copy(rb) 
   sheet = wb.get_sheet('jenkins') 
   
   # Dictionary to store the maven version installed ot not
   result = {"matched": [], "unmatched": [] }
   
   # Loop for matching maven installations
   for i in m2.find('installations').iter('hudson.tasks.Maven_-MavenInstallation'):
            ssh = pxssh.pxssh()
            ssh.login(remote_host,remote_user,remote_password,sync_multiplier=5)
            ssh.sendline("python -c 'import os; print(os.path.exists("+'"'+i.find('home').text+'"'+"))'") 
            ssh.prompt() # match the prompt
            val = str("".join((ssh.before).split('\r\n')[1:]))
            ssh.logout()
            if val == "True":   
               result["matched"].append(dict({"home": i.find('home').text}))
            else:
               result["unmatched"].append(dict({"home":i.find('home').text}))    

   style = xlwt.easyxf('align: vert center;''font: colour black;')
   print("******Maven Version Exists locally******")
   r+=2 # To give line space
   sheet.write(r,col,"Maven Versions Exists Locally",xlwt.easyxf('align: vert center;''font: colour green, bold True;'))
   sheet.write(r+1,col,"Version",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   r+=2   # To give line space  
   for i in result['matched']:
      print("Version : "+ i['home'])
      sheet.write(r+1,col,i['home'],style)
      r+=1   
   print("******Maven Version NOT Exists locally******")
   r+=2 # To give line space
   sheet.write(r,col,"Maven Versions NOT Exists Locally",xlwt.easyxf('align: vert center;''font: colour red, bold True;'))
   sheet.write(r+1,col,"Version",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   r+=2   # To give line space  
   for i in result['unmatched']:
      print("Version : "+ i['home'])
      sheet.write(r+1,col,i['home'],style)
      r+=1   

   wb.save('final_report.xlsx')    
                  
def match_sonar_servers(master,remote,remote_host,remote_user,remote_password):
   master_home = master.run_script('println(System.getenv("JENKINS_HOME"))')
   remote_home = remote.run_script('println(System.getenv("JENKINS_HOME"))')
   s1 = ET.parse(master_home+'/hudson.plugins.sonar.SonarGlobalConfiguration.xml').getroot()
   ssh = pxssh.pxssh()
   ssh.login(remote_host,remote_user,remote_password,sync_multiplier=5)
   ssh.sendline('sudo cat '+remote_home+'/hudson.plugins.sonar.SonarGlobalConfiguration.xml') 
   ssh.prompt() # match the prompt
   xmlstr = str("".join((ssh.before).split('\r\n')[1:]))
   ssh.logout()              
   s2 = ET.fromstring(xmlstr)

   rb = xlrd.open_workbook('final_report.xlsx',formatting_info=True)
   r_sheet = rb.sheet_by_index(0) 
   r = r_sheet.nrows
   col = 0
   wb = copy(rb) 
   sheet = wb.get_sheet('jenkins') 
   
   # Dictionary to store the list of matched and unmatched sonar servers
   result = {"matched": [], "unmatched_cred": [], "unmatched_remote": [],"unavailable": [] }
   
   # Loop for matching Sonar Servers
   for i in s1.find('installations').iter('hudson.plugins.sonar.SonarInstallation'):
      count = 0  
      for j in s2.find('installations').iter('hudson.plugins.sonar.SonarInstallation'):
          if i.find('name').text == j.find('name').text and i.find('serverUrl').text == j.find('serverUrl').text:
             credential_id1 = i.find('credentialsId').text
             credential_id2 = j.find('credentialsId').text
             cr1 = ET.parse(master_home+'/credentials.xml').getroot()
             for z in cr1.find('domainCredentialsMap').find('entry').find('java.util.concurrent.CopyOnWriteArrayList').iter('org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl'):
                if credential_id1 == z.find('id').text:
                   data = 'println(hudson.util.Secret.decrypt("{}"))'.format(z.find('secret').text)
                   p1 = master.run_script(data)

             ssh = pxssh.pxssh()
             ssh.login(remote_host,remote_user,remote_password,sync_multiplier=5)
             ssh.sendline('sudo cat '+remote_home+'/credentials.xml')
             ssh.prompt()
             xmlstr1 =  str("".join((ssh.before).split('\r\n')[1:]))
             ssh.logout()
             cr2 = ET.fromstring(xmlstr1)
             p2 = ""
             for z in cr2.find('domainCredentialsMap').find('entry').find('java.util.concurrent.CopyOnWriteArrayList').iter('org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl'):
                if credential_id2 == z.find('id').text:     
                   data = 'println(hudson.util.Secret.decrypt("{}"))'.format(z.find('secret').text)
                   p2 = remote.run_script(data)
             if p1 == p2:   
                result["matched"].append(dict({"name": i.find('name').text}))
             else:
                result["unmatched_cred"].append(dict({"name": i.find('name').text}))  

          if i.find('name').text == j.find('name').text and i.find('serverUrl').text != j.find('serverUrl').text:
             result["unmatched_remote"].append(dict({"name":i.find('name').text,"remote1":i.find('serverUrl').text,"remote2":j.find('name').text}))     
          if i.find('name').text == j.find('name').text:
             count = 1
      if count == 0:
         result["unavailable"].append(dict({"name":i.find('name').text}))

   style = xlwt.easyxf('align: vert center;''font: colour black;')
   print("*****Sonar Servers Matched*****")
   r+=1 # To give line space
   sheet.write(r,col,"Sonar Servers Matched",xlwt.easyxf('align: vert center;''font: colour green, bold True;'))
   sheet.write(r+1,col,"Server Name",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   r+=2   # To give line space  
   for i in result['matched']:
      print("Server Name  : "+ i['name'])
      sheet.write(r+1,col,i['name'],style)
      r+=1   
      
   print("*****Sonar Servers unmatched due to different credentials*****")      
   r+=2 # To give line space
   sheet.write(r,col,"Sonar Servers unmatched due to different credentials",xlwt.easyxf('align: vert center;''font: colour red, bold True;'))
   sheet.write(r+1,col,"Server Name",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   r+=2   # To give line space         
   for i in result["unmatched_cred"]:
      print("Server Name  : "+i['name'])
      sheet.write(r+1,col,i['name'],style)
      r+=1   

   print("*****Sonar Servers unmatched due to different remote*****")
   r+=2 # To give line space
   sheet.write(r,col,"Sonar Servers unmatched due to different remote",xlwt.easyxf('align: vert center;''font: colour red, bold True;'))
   sheet.write(r+1,col,"Server Name",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   sheet.write(r+1,col+1,"Gold Copy Instance Remote Url",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   sheet.write(r+1,col+2,"Remote Jenkins Url",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   r+=2   # To give line space             
   for i in result["unmatched_remote"]:
      print("Server Name  : "+ i['name']+" Gold Copy Remote Url : "+ i['remote1']+"  Remote Jenkins Url  : "+ i['remote2'])
      sheet.write(r+1,col,i['name'],style)
      sheet.write(r+1,col+1,i['remote1'],style) 
      sheet.write(r+1,col+2,i['remote2'],style)
      r+=1 

   print("******Sonar Servers Unavailable******")
   r+=2 # To give line space
   sheet.write(r,col,"Sonar Servers unavailable",xlwt.easyxf('align: vert center;''font: colour red, bold True;'))
   sheet.write(r+1,col,"Server Name",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
   r+=2   # To give line space             
   for i in result["unavailable"]:
      print("Server Name  : "+i['name'])
      sheet.write(r+1,col,i['name'],style)
      r+=1 

   wb.save('final_report.xlsx')    

def verify_security(master,remote):
       info1 = master.get_info()
       info2 = remote.get_info()
       rb = xlrd.open_workbook('final_report.xlsx',formatting_info=True)
       r_sheet = rb.sheet_by_index(0) 
       r = r_sheet.nrows
       col = 0
       wb = copy(rb) 
       sheet = wb.get_sheet('jenkins') 
       style = xlwt.easyxf('align: vert center;''font: colour black;')
       print("------Security-----------")
       r+=2# To give line space
       sheet.write(r,col,"Security",xlwt.easyxf('align: vert center;''font: colour black, bold True;'))
       if info1['useSecurity'] == info2['useSecurity']:
          print("Security is Enabled on Both")
          sheet.write(r+1,col,"Security is Enabled",xlwt.easyxf('align: vert center;''font: colour green, bold True;')) 
       else:
          print("Security is NOT matching"+"Gold Copy Master -- "+info1['useSecurity']+"Remote Jenkins -- "+info2['useSecurity']) 
          sheet.write(r+1,col,"Security is NOT Enabled",xlwt.easyxf('align: vert center;''font: colour red, bold True;')) 
          sheet.write(r+1,col,info1['security'],xlwt.easyxf('align: vert center;''font: colour black, bold True;')) 
          sheet.write(r+1,col,info2['security'],xlwt.easyxf('align: vert center;''font: colour black, bold True;')) 
       
       wb.save('final_report.xlsx')    
           
def main(): 
   if len(sys.argv) != 10:
        check()
   # Function to save GoldCopy Jenkins Instance Plugins Information to csv file 
   save_goldcopy_info(sys.argv[1],sys.argv[2],sys.argv[3])
   # Function to match the csv file with Remote Jenkins Instance Plugin Configuration
   match_plugins(sys.argv[4],sys.argv[5],sys.argv[6])
   
   # Calling the jenkins using api
   goldcopy = jenkins.Jenkins(sys.argv[1],sys.argv[2],sys.argv[3])
   remotemaster = jenkins.Jenkins(sys.argv[4],sys.argv[5],sys.argv[6])     
   # Function to match Global Shared Libraries
   match_shared_libraries(goldcopy,remotemaster,sys.argv[7],sys.argv[8],sys.argv[9])

   # Function to match github servers
   match_github_servers(goldcopy,remotemaster,sys.argv[7],sys.argv[8],sys.argv[9])

   #Function to check Maven Installations
   check_maven_installations(goldcopy,remotemaster,sys.argv[7],sys.argv[8],sys.argv[9])

   #Function to match Sonar Servers
   match_sonar_servers(goldcopy,remotemaster,sys.argv[7],sys.argv[8],sys.argv[9])

   #Function to verify security
   verify_security(goldcopy,remotemaster)

if __name__ == '__main__':
   main()
