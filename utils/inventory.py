#------------------------------------------------------------------------------
# Inventory stuff
#------------------------------------------------------------------------------

import socket
import yaml
import os
import time
import shutil

INVENTORY_FILE = "inventories/ngr.yml"

class Inventory:

    global INVENTORY_FILE

    HNPREFIX = 'rcph'
    
    ALL_KEY = 'all'
    HOSTS_KEY = 'hosts'
    VARS_KEY = 'vars'
    FIRST_MGR_KEY = 'docker-first-manager'
    OTHER_MGRS_KEY = 'docker-other-managers'
    WORKERS_KEY = 'docker-workers'
    ES_HOSTS_KEY = 'es-hosts'

    def __init__(self, newfile = True) : 

        self.filename = INVENTORY_FILE
        
        if newfile:

            self.data = {}
            self.data[self.ALL_KEY] = {self.HOSTS_KEY: {}, self.VARS_KEY : {}}
            self.data[self.FIRST_MGR_KEY] = {self.HOSTS_KEY : {}}
            self.data[self.OTHER_MGRS_KEY] = {self.HOSTS_KEY: {}}
            self.data[self.WORKERS_KEY] = {self.HOSTS_KEY: {}}
            self.data[self.ES_HOSTS_KEY] = {self.HOSTS_KEY : {}}
            
        else:

            with open(self.filename, 'r') as stream:
                try:
                    self.data = yaml.load(stream)
                except yaml.YAMLError as e:
                    print(e)
            stream.close()

    def save(self):
        
        if os.path.exists(self.filename):
            shutil.copy2(self.filename, self.filename +
                         '-%s' % (time.strftime('%y%m%d-%H%M%S')))
            
        with open(self.filename, 'w') as stream:
            try:
                yaml.dump(self.data, stream, default_flow_style=False)
            except yaml.YAMLError as e:
                print(e)

        stream.close()

    def iprint(self):
        print(yaml.dump(self.data, default_flow_style=False))


    def numberOfHosts(self):
        return len(self.data[self.ALL_KEY][self.HOSTS_KEY])

    def getNGRAddress(self):
        return self.firstNodeAddress
        
#-------------------------------------------------------------------------------    
# Collect inventory data from user
#-------------------------------------------------------------------------------    
    def collectInventoryDataFromUser(self, firstNode=1, visionaddr = None):

        i = firstNode
        if firstNode == 1:
            valid = False
            while not valid:
                addr = raw_input("\nWhat is the NGR node IP address ? ")
                try:
                    socket.inet_aton(addr)
                    valid = True
                except:
                    print("Incorrect address format, try again ...")
                self.data[self.ALL_KEY][self.HOSTS_KEY].update(
                    {self.HNPREFIX+'01' : {'ansible_ssh_host' : addr}})
                i = 2

            # inventory_userid = raw_input("\nuserid for NGR nodes? ")
            # inventory_passwd = raw_input("password for NGR nodes? ")
            inventory_userid = 'root'
            inventory_passwd = 'radware'

            self.firstNodeAddress = self.data[self.ALL_KEY][self.HOSTS_KEY][self.HNPREFIX+'01']['ansible_ssh_host']
            self.data[self.ALL_KEY][self.VARS_KEY] = {
                'ansible_ssh_user' : inventory_userid, 
                #'ansible_ssh_password' : inventory_passwd,
                'ansible_user' : inventory_userid,
                #'ansible_password' : inventory_passwd, 
                'docker_swarm_port' : 2377,
                'docker_swarm_manager' : self.HNPREFIX+'01', 
                'docker_swarm_addr': self.firstNodeAddress
                   ,
                'vision_address' : visionaddr
            }
                
        else:
            while True:
                addr = raw_input("Additional NGR node IP [type IP address (non address will stop)]? ")
                try:
                    socket.inet_aton(addr)
                except:
                    break

                self.data[self.ALL_KEY][self.HOSTS_KEY].update(
                    {self.HNPREFIX+'%02d' % (i) : {'ansible_ssh_host' : addr}})

                i = i + 1

            
#-------------------------------------------------------------------------------    
# Update inventory (add nodes)
#-------------------------------------------------------------------------------    
    def updateInventory(self):

        for host in self.data[self.ALL_KEY][self.HOSTS_KEY]:
            
            if (host == self.HNPREFIX+'01'):
                self.data[self.FIRST_MGR_KEY][self.HOSTS_KEY].update(
                    {self.HNPREFIX+'01' : None})
            elif (host == self.HNPREFIX+'02' or host == self.HNPREFIX+'03'):
                self.data[self.OTHER_MGRS_KEY][self.HOSTS_KEY].update({host : None})
            else:
                self.data[self.WORKERS_KEY][self.HOSTS_KEY].update({host : None})

            # In version 1.0.0 all ngr node should host es        
            self.data[self.ES_HOSTS_KEY][self.HOSTS_KEY].update({host : None})
