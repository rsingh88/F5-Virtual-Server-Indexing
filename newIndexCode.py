
#!/usr/bin/python
import os
import re
from f5.bigip import ManagementRoot



# Variable in a function is defined only in local scope
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
    background-color: #c9dbdc;
    font-size: 15px;}
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
<body>
        <div class="container">
                        <table class = "table table-hover table-condensed">
                                <caption>vip index runs weekly</caption>
                                <thead class = 'mystyle'>
                                        <tr>
                                                <th>VIP Name</th> <th>VIP IP</th><th>Device and Partition</th>
                                        </tr>
                                </thead>


'''
VipFile = open("/var/www/html/lbconf/temp_IHS.html","wa")
VipFile.write(htmlHead)


DeviceList=["10.242.2.70","10.242.2.72","10.242.2.80"]


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

    def poolContent(self,partition,pool):
        self.partition = partition
        self.pool = pool
        return self.mgmt.tm.ltm.pools.pool.load(partition=self.partition, name=self.pool)


#First Loop Gets into each device, second loops grab the vipCollection list and iterate over its item. Each item has vip contents. 

# Variable in a function is defined only in local scope
def vipIndexFunction():
        vipList = []  # vipList declared to hold the list vips from all devices
        for device in DeviceList:  
            deviceObject = VirtualClass(device,"admin","xxxxx") 
            vipCollection = deviceObject.vipContent()
            
            print device+ " connection successfull"
            
            for vip in vipCollection: # Loop to iterate over the vip 
                partitionTemp = re.search(r"\/(.+)\/",vip.destination)
                partition = partitionTemp.group(1)
                vipIPTemp = re.search(r"[\d.%:]+",vip.destination)
                vipIP = vipIPTemp.group()
                # Try block to handle the exception raised when there isn't any pool configured inside vip
                try:
                   poolRE = re.search(r"(.+)\/(.+)",vip.pool)
                   pool = poolRE.group(2)
                except AttributeError:
                   pool = "none"
                
                vipList.append(vip.name+"$"+vipIP+"$"+device+"$"+partition+"$"+pool)

        #This is exit of both above loops, now we need to sort the list so that same name vip can be found together in different DC
        vipList.sort()
        print vipList  # This is to check if index is being generated.
        return vipList



# Variable in a function is defined only in local scope
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
                print Device
                # Table row write for the vip, ip and device/partition 
                VipFile.write('''<tr class = 'mystyle' onclick="myFunction('id'''+str(n)+'''')"><td>'''+vipName+"</td>"+"<td>"+IP+"</td>"+"<td>"+Device+"/"+partition+"</td></tr>")

                # Below here the configuration information of above vip goes, this will be hide/show feature in table row
                deviceObject2 = VirtualClass(Device,"admin","xxxxxx")
                #Try block is to handle the exception raised by iControlAPI, this was observed in case of iAPP configuration!
                try:  
                   virtualSever = deviceObject2.vipload(partition,vipName)
                   VipFile.write("<tr id='id"+str(n)+"' style='display:none'><td>"+"--VIP<br>"+"VIP Name : "+virtualSever.name +"<br>")
                   VipFile.write("VIP Address : "+virtualSever.destination+" "+virtualSever.ipProtocol+"<br>")
                   VipFile.write("Address Mask : "+virtualSever.mask+"<br>")
                   VipFile.write("sourceAddressTranslation : "+str(virtualSever.sourceAddressTranslation)+"<br>")
                   VipFile.write("translateAddress : "+virtualSever.translateAddress+"<br>")
                   VipFile.write("translatePort : "+virtualSever.translatePort+"<br>")

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
                           VipFile.write("Health Monitor : None")
                        # print members and state
                        members = virtualPool.members_s.get_collection()
                        VipFile.write("--members<br>")
                        for mem in members:
                                VipFile.write("member name: "+mem.name+" address: "+mem.address+" status: "+mem.state+" monitor: "+mem.monitor+"<br>")

                   # Finding policies and printing them
                   policies = virtualSever.policies_s.get_collection()
                   VipFile.write("--policies<br>")
                   for policy in policies:
                        VipFile.write("policy : "+policy.name+"<br>")

                   # iRules and printing them 
                   VipFile.write("iRules : "+str(virtualSever.rules)+"<br>")
                   VipFile.write("</td> </tr>")
                except:
                   VipFile.write("<tr id='id"+str(n)+"' style='display:none' class = 'errorClass' ><td> Config couldn't be downloaded. Must be an iAPP, please check LTM <br>")
                n+=1
        
        end_code = "</table> </div> </body> <html>"
        VipFile.write(end_code)
        VipFile.close()


#Function calls

vipList = vipIndexFunction()
htmlFileWrite(vipList)
