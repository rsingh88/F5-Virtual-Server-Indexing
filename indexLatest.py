#!/usr/bin/python

import sys
import os
import re
from f5.bigip import ManagementRoot


######################### HTML Code ###########################

htmlHead = '''
<!DOCTYPE html>
<html>
<head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <title></title>
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous"> 

        <style type="text/css" media="screen">
        .mystyle {
    background-color: white;
    font-size: 15px;}
        .bodyClass {
    background-color: #eaeef7;
        }
        .errorClass {
        color : red;
        }
        </style>
        <script  type="text/javascript" charset="utf-8" async defer>
                function myFunction(elementID) {
                    var x = document.getElementById(elementID);
                    if (x.style.display === "none") {
                        x.style.display = "block";} 
                    else {
                        x.style.display = "none";
                    }
                }
        </script>
</head>
<body class = "bodyClass">
        <div class="container">
                        <table class = "table table-hover table-condensed">
                                <caption>vip index runs weekly</caption>
                                <thead class = 'mystyle'>
                                        <tr>
                                                <th>VIP Name</th> <th>VIP IP</th><th>Device and Partition</th><th> Hostname</th>
                                        </tr>
                                </thead>


'''
VipFile = open("/var/www/html/lbconf/vip_index_ihs.html","wa")
VipFile.write(htmlHead)


######################### HTML END ###########################





user = ''
pwd = ''
#activeLTM = []     
activeLTM = {}
vipList = [] # vipList declared to hold the list vips from all devices




def globalVariable():
        global user
        global pwd
        if len(sys.argv)!=3:
                print "You have not entered the user/pwd. Usage: python prog.py user pwd"
                sys.exit(1)
        else:
                user = sys.argv[1]
                pwd = sys.argv[2]
       

def deviceFunction():
        global activeLTM 
        with open("device_list.txt", "rb") as DeviceList:
                for device in DeviceList:
                        device = device.strip()
                        mgmt = ManagementRoot(device,user,pwd,verify=False)
                        print "Connection to "+device+" successful!"
                        ltmSys  = mgmt.tm.cm.devices.get_collection()
                        # above api call will return both active and standby device information in the form of list type object. 
                        # index 0 will be one from where api call has been intiated
                        if str(ltmSys[0].failoverState) ==      'active':
                                #activeLTM.append(str(ltmSys[0].managementIp))
                                activeLTM[str(ltmSys[0].hostname)] = str(ltmSys[0].managementIp)
                        else:
                                #activeLTM.append(str(ltmSys[1].managementIp))
                                activeLTM[str(ltmSys[1].hostname)] = str(ltmSys[1].managementIp)

        print activeLTM

class VirtualClass:
    def __init__(self, device,user,pwd):
        self.device = device
        self.user = user
        self.pwd =pwd
        self.mgmt = ManagementRoot(self.device,self.user,self.pwd,verify=False)

    def vipContent(self):
        return self.mgmt.tm.ltm.virtuals.get_collection()

    def vipload(self,partition,vipName):
        self.partition = partition
        self.vipName = vipName
        return self.mgmt.tm.ltm.virtuals.virtual.load(partition=self.partition, name=self.vipName)
    
    def vipLoadIapp(self,partition,vipName,subPath):
        self.partition = partition
        self.vipName = vipName
        self.subPath = subPath
        return self.mgmt.tm.ltm.virtuals.virtual.load(partition=self.partition, name=self.vipName, subPath=self.subPath)

    def poolContent(self,partition,pool):
        self.partition = partition
        self.pool = pool
        return self.mgmt.tm.ltm.pools.pool.load(partition=self.partition, name=self.pool)



                                        ######################
#First Loop Gets into each device, second loops grab the vipCollection list and iterate over its item. Each item has vip contents. 
# Variable in a function is defined only in local scope
                                        #######################



def vipListFunction():
        global vipList 
        for host,ip in activeLTM.items():  
            deviceObject = VirtualClass(ip,user,pwd) 
            vipCollection = deviceObject.vipContent()
            
            #print ip+ " connection successfull"
            
            for vip in vipCollection: # Loop to iterate over the vip 
                partitionTemp = re.search(r"\/(.+)\/",vip.destination)
                partition = partitionTemp.group(1)
                vipIPTemp = re.search(r"[\d.%:]+",vip.destination)
                vipIP = vipIPTemp.group()
                # Try block to handle the exception raised when there isn't any pool configured inside vip
                # subPath is to collect iAPP name, this will be used for vip built with iapp
                try:
                   poolRE = re.search(r"(.+)\/(.+)",vip.pool)
                   pool = poolRE.group(2)
                except AttributeError:
                   pool = "none"
                try:
                   subPath = vip.subPath
                except:
                   subPath = 'none'
                vipList.append(vip.name+"$"+vipIP+"$"+ip+"$"+partition+"$"+pool+"$"+host+"$"+subPath)

        #This is exit of both above loops, now we need to sort the list so that same name vip can be found together in different DC
        vipList.sort()
        print subPath  # This is to check if index is being generated.
        return vipList




def htmlFileWrite(vipList):
        n = 1
        for item in vipList:

                itemList = str(item).split("$")
                vipName = itemList[0] 
                IP = itemList[1]
                Device = itemList[2]
                Device = str(Device)
                partition = itemList[3]
                pool = itemList[4]
                host = itemList[5]
                subPath = itemList[6]
                print 

                # Below here the configuration information of above vip goes, this will be hide/show feature in table row
                deviceObject2 = VirtualClass(Device,user,pwd)
                #Try block is to handle the exception raised by iControlAPI, this was observed in case of iAPP configuration!
                try: 
                   if(subPath =='none'):
                        virtualSever = deviceObject2.vipload(partition,vipName)
                   else:
                        virtualSever = deviceObject2.vipLoadIapp(partition,vipName,subPath)
                   vipStat = virtualSever.stats.load()
                   # This try block is to handle exception raised in BIGIP 12.x.x version, due to nested stats dictionary
                   try:
                        vipStatus = str(vipStat.entries['status.availabilityState']['description'])
                   except:
                        for selflink, nestValue in vipStat.entries.items():
                                pass
                        vipStatus = str(vipStat.entries.get(selflink)['nestedStats']['entries']['status.availabilityState']['description'])
                   if (vipStatus == 'available'):
                       VipFile.write('''<tr class = 'mystyle' onclick="myFunction('id'''+str(n)+'''')"><td> <img src="green.png" height = 12 width = 12> '''+vipName+"</td>"+"<td>"+IP+"</td>"+"<td>"+Device+"/"+partition+"</td><td>"+ host+"</td> </tr>")
                   else:
                       VipFile.write('''<tr class = 'mystyle' onclick="myFunction('id'''+str(n)+'''')"><td> <img src="red.png" height = 12 width = 12> '''+vipName+"</td>"+"<td>"+IP+"</td>"+"<td>"+Device+"/"+partition+"</td><td>"+ host+"</td></tr>")
                   VipFile.write("<tr id='id"+str(n)+"' style='display:none'><td>"+"--VIP<br>"+"VIP Name : "+virtualSever.name +"<br>")
                   VipFile.write("VIP Address : "+virtualSever.destination+" "+virtualSever.ipProtocol+"<br>")
                   VipFile.write("Address Mask : "+virtualSever.mask+"<br>")
                   VipFile.write("sourceAddressTranslation : "+str(virtualSever.sourceAddressTranslation)+"<br>")
                   VipFile.write("translateAddress : "+virtualSever.translateAddress+"<br>")
                   VipFile.write("translatePort : "+virtualSever.translatePort+"<br>")
                   VipFile.write("iApp Name : "+subPath+"<br>")

                   # Finding profiles and printing them
                   profiles = virtualSever.profiles_s.get_collection()
                   VipFile.write("--Profiles<br>")
                   for profileItem in profiles:
                        VipFile.write("Profile : "+profileItem.name+"<br>")

                   # print pool and its content
                   if pool != "none":
                        virtualPool = deviceObject2.poolContent(partition,pool)
                        VipFile.write("--Pool<br>")
                        VipFile.write("Pool Name : "+virtualPool.name+"<br>")
                        VipFile.write("load Balancing Mode : "+virtualPool.loadBalancingMode+"<br>")
                        try:
                           VipFile.write("Health Monitor : "+virtualPool.monitor+"<br>")
                        except AttributeError:
                           VipFile.write("Health Monitor : None<br> ")
                        # print members and state
                        members = virtualPool.members_s.get_collection()
                        VipFile.write("--members<br>")
                        for mem in members:
                            if(str(mem.state) == 'up'):
                                VipFile.write("<img src='green-dot.png' height = 12 width = 12> "+mem.name+" address: "+mem.address+"<br>")
                            else:
                                VipFile.write("<img src='red-dot.png' height = 12 width = 12> "+mem.name+" address: "+mem.address+"<br>")
                   # Finding policies and printing them
                   policies = virtualSever.policies_s.get_collection()
                   VipFile.write("--policies<br>")
                   for policy in policies:
                        VipFile.write("policy : "+policy.name+"<br>")

                   # iRules and printing them 
                   VipFile.write("--iRules<br>irule : "+str(virtualSever.rules)+"<br>")
                   VipFile.write("</td> </tr>")
                except:
                   VipFile.write('''<tr class = 'mystyle' onclick="myFunction('id'''+str(n)+'''')"><td> <img src="blue.png" height = 12 width = 12> '''+vipName+"</td>"+"<td>"+IP+"</td>"+"<td>"+Device+"/"+partition+"</td><td>"+ host+"</td> </tr>")
                   VipFile.write("<tr id='id"+str(n)+"' style='display:none' class = 'errorClass' ><td> Config couldn't be downloade, please check LTM <br>")
                n+=1
        
        end_code = "</table> </div> </body> <html>"
        VipFile.write(end_code)
        VipFile.close()


# #######Function calls##################


globalVariable()
deviceFunction()
vipList = vipListFunction()
htmlFileWrite(vipList)
