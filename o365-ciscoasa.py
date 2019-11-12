import json
import urllib.request
import uuid
import os
import ipaddress
import argparse
import sys

#Original starting code from Microsoft article:
#(https://docs.microsoft.com/en-us/office365/enterprise/office-365-ip-web-service)
#

# helper to call the webservice and parse the response
def webApiGet(methodName, instanceName, clientRequestId):
    ws = "https://endpoints.office.com"
    requestPath = ws + '/' + methodName + '/' + instanceName + '?clientRequestId=' + clientRequestId
    request = urllib.request.Request(requestPath)
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode())

def printRoutes(endpointSets,routeType):
    flatIps=[]
    with open('O365-Routes-ObjectGroups.txt', 'w') as output:
        for endpointSet in endpointSets:
            if endpointSet['category'] in ('Optimize', 'Allow'):
                ips = endpointSet['ips'] if 'ips' in endpointSet else []
                category = endpointSet['category']
                serviceArea = endpointSet['serviceArea']
                # IPv4 strings have dots while IPv6 strings have colons
                ip4s = [ip for ip in ips if '.' in ip]
                tcpPorts = endpointSet['tcpPorts'] if 'tcpPorts' in endpointSet else ''
                udpPorts = endpointSet['udpPorts'] if 'udpPorts' in endpointSet else ''
                for ip in ip4s:
                    flatIps.extend([(serviceArea, category, ip, tcpPorts, udpPorts)])

        print("Converting O365 Endpoints into Route Statements")
        currentServiceArea = " "
        groupList = []
        for ip in flatIps:
            serviceArea = ip [0]
            if serviceArea != currentServiceArea:
                #Set the current type like Common, Exchange, Skype, etc
                if currentServiceArea != " ":
                    output.write f"! Routes for {currentServiceArea}"
                groupList = []
                uniqueIps = []
                currentServiceArea = serviceArea
            if ip[2] not in uniqueIps:
                #uniqueIps is used because the same IP can be listed multiple times with different ports.
                uniqueIps.append(ip[2])
                ipNet = ipaddress.ip_network(ip[2])
                routeOutput = routeCreate(ipNet,remark,routeType)
                groupList.append(routeOutput)



def routeCreate(ipNet, remark, routeType):
    #Take in an IP network, comment and whether it is Nexus or IOS
    if routeType == "Nexus":
        output = printNexusRoute(ipNet,remark)
    if routeType == "IOS":
        output = printIOSRoute(ipNet,remark)
    return output

    

def main (argv):
    # Parse
    # path where client ID and latest version number will be stored
    datapath = 'endpoints_clientid_latestversion.txt'
    # fetch client ID and version if data exists; otherwise create new file
    if os.path.exists(datapath):
        with open(datapath, 'r') as fin:
            clientRequestId = fin.readline().strip()
            latestVersion = fin.readline().strip()
    else:
        clientRequestId = str(uuid.uuid4())
        latestVersion = '0000000000'
        with open(datapath, 'w') as fout:
            fout.write(clientRequestId + '\n' + latestVersion)
    version = webApiGet('version', 'Worldwide', clientRequestId)
    if version['latest'] > latestVersion:
        print('New version of Office 365 worldwide commercial service instance endpoints detected')
        # write the new version number to the data file
        with open(datapath, 'w') as fout:
            fout.write(clientRequestId + '\n' + version['latest'])
        # invoke endpoints method to get the new data
        endpointSets = webApiGet('endpoints', 'Worldwide', clientRequestId)
        # filter results for Allow and Optimize endpoints, and transform these into tuples with port and category
        flatUrls = []
        printASA(endpointSets)
    else:
        print("Office 365 worldwide commercial service instance endpoints are up-to-date.")

if __name__ == '__main__':
    main(sys.argv)
