# F5 VIP Indexing with iControlRest call
Following code generates vip index in tabular form with their specific config from F5 BigIP devices


indexLatest.py
================
Pre-requisite:
1.) You need to have python2.7 version 
2.) You need to install f5-sdk module in your python. 
      pip install f5-sdk 
      or follow : https://pypi.python.org/pypi/f5-sdk/  or https://github.com/F5Networks/f5-common-python
3.) You need download "device_list.txt" and keep it in the same directory where you copy "indexLatest.py". 
4.) "device_list.txt" open this file and copy mgmt ip/ltm-system-name(if dns works for you) in the file.
      e.g   10.10.10.10
            20.20.20.20
            30.30.30.30
5.) Download and Unpack "required.zip" file in the same directory where you have "indexLatest.py". Zip file contains ".png" files 
    which will be used to show virtual servers and members status in green,blue or red.
 
6.) You will have to change the file path as per your desired location, code line number54 
    for example VipFile = open("filePath/fileName.html","wa")

7.) You are ready now, indexLatest.py needs to run with admin/pwd as commond line argument
    for eg. 
      python indexLatest.py admin abc@123
 
Outcome:

1.) Following script generates an html file(at the same location which you specified in step 6), which holds up list of virtual            servers and their config. 

"test.html" is attached which shows how the final outcome will look like.




   
