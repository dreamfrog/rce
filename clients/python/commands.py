#!/usr/bin/env python
import json

# Configuration Message - Create Container
cmd_CS = {
            "type":"CS",
            "dest":"$$$$$$",
            "orig":"robotUniqueID", # Redundant
            "data":None
            }

cmd_CS_js = json.dumps(cmd_CS)

print(cmd_CS_js)            

# Configuration Message - Create Container Response
cmd_CSR = {
            "type":"CSR",
            "dest":"robotUniqueID",
            "orig":"$$$$$$",
            "data":{"containerID":"cid"}
            }

cmd_CSR_js = json.dumps(cmd_CSR)

print(cmd_CSR_js)     

# Configuration Message - Distroy Container
cmd_CH = {
  "type":"CH",
  "dest":"$$$$$$",
            "orig":"robotUniqueID",  
            "data":{"containerID":"cid"}
            }

cmd_CH_js = json.dumps(cmd_CH)

print(cmd_CH_js)            

# Configuration Message - Change Components
nodeConfigs = [{
    "nodeID":"nid",
    "nodeName":"nn",
    "namespaceID":"ns",
    }]
cmd_CC = {
            "type":"CC",
            "dest":"containerID_receivedFrom_cmd_CSR",
            "orig":"robotUniqueID",
            "data":{
                    "addNodes":nodeConfigs,
                    "removeNodes":["nameSpaceID/nodeID"],
                    "addInterfaces":[{"interfaceName":"inm",
                                    "type":"type", # Options: Publisher/Subscriber/Service 
                                    "class":"className"} # msgType for Publisher/Subscriber | srvType for Service
                                    ],
                    "removeInterfces":["inm"],
                    "setParam":{"paramName":"paramValue"},
                    "deleteParam" : ["paramName"]
                    }
            }

#TODO: Future we will be able to send a full roslauch file for nodes and parameters.

cmd_CC_js = json.dumps(cmd_CC)
print(cmd_CC_js)

# Data Messages
msg = {"linear":{"x":0,"y":0,"z":0},"angular":{"x":0,"y":0,"z":0}};

cmd_RM = {
    "type":"RM",
    "dest":"destination_container/robot",
    "orig":"origin_container/robot",
    "data":{
        "type":"geometry_msgs/Twist", # Service/Msg type # This is actually redundant: Interface has all details
        "msgID":"mid",  # Applicable only to services. Only if you want to maintain correspondence between request and response.
        "interfaceID":'iid', # Corresponds to the receiver in rosbridge
        "msg":msg} # In case of srv call: _request_class of the srv class
    }

cmd_RM_js = json.dumps(cmd_RM)
print(cmd_RM_js)