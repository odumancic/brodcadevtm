#!/usr//bin/python

import requests
import json
import sys
import os
import re
import time

###########################################################################################################################
###                                        pool.conf syntax                                                             ###
### vserver:[virtual server name];main:[main pool of the virtual server];failover:[failover pool of the virtual server] ###
###                              (one entry per line per virtual server)                                                ###
###########################################################################################################################

buf_arg = 0
sys.stdout = os.fdopen(sys.stdout.fileno(), 'a+', buf_arg)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'a+', buf_arg)


usage = "Usage: rest.py <options> \n Options: \n --remove-failover \t Remove from failover" + \
        "\n --add-failover \t Add to failover \n --move-failover \t Move to failover" + \
        "\n --move-main \t\t Move to main" + \
        "\n\n The scripts reads from pool.conf the configurations to change." + \
        "\n Multiple lines can be used to configure different virtual servers." + \
        "\n\nExample:" + \
        "\nvserver:[Virtual Server name];main:[Main Pool name];failover:[Failover Pool name]"


def main():
    for arg in sys.argv[1:]:
        if arg in ("--remove-failover", "--add-failover", "--move-failover", "--move-main", ""):
            return arg
        else:
            print usage
            exit()


class Connect():
    def __init__(self, choice):
        self.choice = choice

        client = requests.Session()
        #client.auth = ('rest', 'password')
        client.headers.update({'Authorization' : 'Basic cmVzdDpwYXNzd29yZA=='})
        
        client.verify = False

        url = 'http://localhost:9070/api/tm/3.7/'

        jsontype = {'content-type': 'application/json'}

        f = open("pool.conf", "r")
        for row in f:
            row = row.rstrip('\n')
            dataset = dict(item.split(":") for item in row.split(";"))

            if choice == "--add-failover":
                # add failover to server
                print "ADD THE FAILOVER %s to %s (VServer %s) -" % (
                    dataset['failover'], dataset['main'], dataset['vserver']),
                payload = {'properties': {'basic': {'failure_pool': dataset['failover'].rstrip()}}}
                try:
                    response = client.put(url + 'config/active/pools/' + dataset['main'], data=json.dumps(payload), headers=jsontype)
                    #print
                    #print dataset['main']
                    #print payload
                except requests.exceptions.ConnectionError:
                    print "Error: Unable to connect to " + url
                    sys.exit(1)
                string = str(response.status_code)
                if re.match(r"^2..$", string):
                    print "done"
                else:
                    print response.status_code

            elif choice == "--remove-failover":
                # remove failover from server
                print "REMOVE THE FAILOVER %s from %s (VServer %s) -" % (
                    dataset['failover'], dataset['main'], dataset['vserver']),
                payload = {'properties': {'basic': {'failure_pool': ''}}}
                try:
                    response = client.put(url + 'config/active/pools/' + dataset['main'], data=json.dumps(payload), headers=jsontype)
                    #print
                    #print dataset['main']
                    #print payload
                except requests.exceptions.ConnectionError:
                    print "Error: Unable to connect to " + url
                    sys.exit(1)
                string = str(response.status_code)
                if re.match(r"^2..$", string):
                    print "done"
                else:
                    print response.status_code

            elif choice == "--move-failover":
                print "MOVE TO THE FAILOVER %s on %s" % (dataset['failover'], dataset['vserver']),
                nodes = []
                response = client.get(url + 'config/active/pools/' + dataset['main'])
                data = json.loads(response.content)
                countElements = data['properties']['basic']['nodes_table']

                # Draining all nodes on main
                for i in range(len(countElements)):
                    #print "MOVE TO THE FAILOVER %s on %s" % (dataset['failover'], dataset['vserver']),
                    data['properties']['basic']['nodes_table'][i]['state'] = 'draining'
                    payload = {'properties': {'basic': {'nodes_table': data['properties']['basic']['nodes_table']}}}
                    nodes.append(data['properties']['basic']['nodes_table'][i]['node'])

                    try:
                        response = client.put(url + 'config/active/pools/' + dataset['main'], data=json.dumps(payload),
                                              headers=jsontype)
                        #print
                        #print dataset['main']
                        #print payload
                    except requests.exceptions.ConnectionError:
                        print "Error: Unable to connect to " + url
                        sys.exit(1)
                    string = str(response.status_code)

                responseTrafficName = client.get(url + 'config/active/traffic_ip_groups/')
                dataTrafficName = json.loads(responseTrafficName.content)

                responseMachines = client.get(url + 'config/active/traffic_ip_groups/' + dataTrafficName['children'][0]['name'])
                dataMachineName = json.loads(responseMachines.content)

                time.sleep(15)

                for servers in [dataset['main']]:
		    sys.stdout.write(str("\nWAITING FOR ALL ACTIVE CONNECTIONS TO CLOSE on %s ") % servers)
                    # print "\nWAITING FOR ALL ACTIVE CONNECTIONS TO CLOSE on %s" % servers,
                    active_conn = -1
                    count = 0
                    while active_conn != 0:
                        for machineNames in dataMachineName['properties']['basic']['machines']:
                            for node in nodes:
                                active_conn = 0
                                try:
                                    active_conn = 0
                                    responseActiveConn1 = client.get(
                                        url + 'status/' + machineNames + '/statistics/nodes/per_pool_node/' + servers + '-' + node + '/')
                                    dataActiveConn1 = json.loads(responseActiveConn1.content)
                                    if (dataActiveConn1['statistics']['state'] == 'draining'):
                                        active_conn += dataActiveConn1['statistics']['current_conn']

                                    if count == 20:
                                        clean = False
                                        active_conn = 0
                                        break
                                    if active_conn != 0:
                                        count += 1
                                        time.sleep(2)
                                        sys.stdout.write(str("."))
					sys.stdout.flush()
					# print ".",
                                        clean = False
                                        break
                                    else:
                                        clean = True
                                except:
                                    pass

                if clean is True:
                    # if there are no connection do the failover
                    print "\nMOVE TO THE FAILOVER %s" % dataset['vserver'],
                    payload = {'properties': {'basic': {'pool': dataset['failover'].rstrip()}}}
                    try:
                        response = client.put(url + 'config/active/virtual_servers/' + dataset['vserver'],
                                              data=json.dumps(payload), headers=jsontype)
                        #print
                        #print dataset['main']
                        #print payload
                    except requests.exceptions.ConnectionError:
                        print "Error: Unable to connect to " + url
                        sys.exit(1)
                    string = str(response.status_code)
                    if re.match(r"^2..$", string):
                        print "- done"
                    else:
                        print response.status_code

                    # make node state active
                    data['properties']['basic']['nodes_table'][i]['state'] = 'active'
                    payload = {'properties': {'basic': {'nodes_table': data['properties']['basic']['nodes_table']}}}
                    nodes.append(data['properties']['basic']['nodes_table'][i]['node'])

                    try:
                        response = client.put(url + 'config/active/pools/' + dataset['main'], data=json.dumps(payload),
                                              headers=jsontype)
                        #print
                        #print dataset['main']
                        #print payload
                    except requests.exceptions.ConnectionError:
                        print "Error: Unable to connect to " + url
                        sys.exit(1)
                    string = str(response.status_code)

                else:
                    print " - TIMEOUT - SKIPPING"

            elif choice == "--move-main":

                # making all nodes on main active
                response = client.get(url + 'config/active/pools/' + dataset['main'])
                data = json.loads(response.content)
                countElements = data['properties']['basic']['nodes_table']

                for i in range(len(countElements)):
                    print "ACTIVATING MAIN NODES %s on %s -" % (dataset['failover'], dataset['vserver']),
                    data['properties']['basic']['nodes_table'][i]['state'] = 'active'
                    payload = {'properties': {'basic': {'nodes_table': data['properties']['basic']['nodes_table']}}}

                    try:
                        response = client.put(url + 'config/active/pools/' + dataset['main'], data=json.dumps(payload),
                                              headers=jsontype)
                        #print
                        #print dataset['main']
                        #print payload
                    except requests.exceptions.ConnectionError:
                        print "Error: Unable to connect to " + url
                        sys.exit(1)
                    string = str(response.status_code)
                    if re.match(r"^2..$", string):
                        print "done"
                    else:
                        print response.status_code

                # moving to main
                print "MOVE TO THE MAIN %s on %s -" % (dataset['failover'], dataset['vserver']),
                payload = {'properties': {'basic': {'pool': dataset['main'].rstrip()}}}
                try:
                    response = client.put(url + 'config/active/virtual_servers/' + dataset['vserver'], data=json.dumps(payload),
                                          headers=jsontype)
                except requests.exceptions.ConnectionError:
                    print "Error: Unable to connect to " + url
                    sys.exit(1)
                string = str(response.status_code)
                if re.match(r"^2..$", string):
                    print "done"
                else:
                    print response.status_code

if __name__ == "__main__":
    args = main()
    if args is None:
        print usage
    change = Connect(args)

