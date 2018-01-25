#------------------------------------------------------------------------------
# Inventory stuff
#------------------------------------------------------------------------------

import socket
import yaml
import os
import time
import shutil
import sys

class Inventory:

    INVENTORIES = "./inventories/"
    BACKUPS =  INVENTORIES + "backups/"
    
    ALL_KEY = 'all'
    HOSTS_KEY = 'hosts'
    VARS_KEY = 'vars'
    FIRST_MGR_KEY = 'docker-first-manager'
    OTHER_MGRS_KEY = 'docker-other-managers'
    WORKERS_KEY = 'docker-workers'
    ES_HOSTS_KEY = 'es-hosts'

    def __init__(self, filename):

        self.name = filename
        self.filename = self.INVENTORIES + filename + '.yml'
        self.nodeprefix = filename + '-'
        
        if not os.path.exists(self.filename):

            print("Creating new inventory: " + self.filename) 

            self.data = {}
            self.data[self.ALL_KEY] = {self.HOSTS_KEY: {}, self.VARS_KEY : {}}
            self.data[self.FIRST_MGR_KEY] = {self.HOSTS_KEY : {}}
            self.data[self.OTHER_MGRS_KEY] = {self.HOSTS_KEY: {}}
            self.data[self.WORKERS_KEY] = {self.HOSTS_KEY: {}}
            self.data[self.ES_HOSTS_KEY] = {self.HOSTS_KEY : {}}
            
        else:

            print("Adding nodes to inventory: " + self.filename)
            
            with open(self.filename, 'r') as stream:
                try:
                    self.data = yaml.load(stream)
                except yaml.YAMLError as e:
                    print(e)
            stream.close()

    def save(self):

        if not os.path.exists(self.INVENTORIES):
            os.makedirs(self.INVENTORIES)
        
        if not os.path.exists(self.BACKUPS):
            os.makedirs(self.BACKUPS)
            
        if os.path.exists(self.filename):
            shutil.copy2(self.filename, self.BACKUPS + self.name +
                         '-%s' % (time.strftime('%y%m%d-%H%M%S')) + '.yml')
            
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

#---------------------------------------------------------------------------    
# Collect inventory data from user
#---------------------------------------------------------------------------    
    def collectInventoryDataFromUser(self):

        next = self.numberOfHosts() + 1
        if next == 1:
            valid = False
            while not valid:
                addr = raw_input("\nWhat is the IP address for first node ? ")
                try:
                    socket.inet_aton(addr)
                    valid = True
                except:
                    print("Incorrect address format, try again ...")
                self.data[self.ALL_KEY][self.HOSTS_KEY].update(
                    {self.nodeprefix+'01' : {'ansible_ssh_host' : addr}})

            inventory_userid = raw_input("\nuserid for cluster nodes? ")
            inventory_passwd = raw_input("password for cluster nodes? ")

            self.firstNodeAddress = self.data[self.ALL_KEY][self.HOSTS_KEY][self.nodeprefix+'01']['ansible_ssh_host']
            self.data[self.ALL_KEY][self.VARS_KEY] = {
                'ansible_ssh_user' : inventory_userid, 
                'ansible_user' : inventory_userid,
                'ansible_ssh_password' : inventory_passwd,
                'ansible_password' : inventory_passwd, 
                'docker_swarm_port' : 2377,
                'docker_swarm_manager' : self.nodeprefix+'01', 
                'docker_swarm_addr': self.firstNodeAddress,
            }

            next = 2
                
        while True:
            addr = raw_input("Add node [type IP address (non address will stop)]? ")
            try:
                socket.inet_aton(addr)
            except:
                break

            self.data[self.ALL_KEY][self.HOSTS_KEY].update(
                {self.nodeprefix+'%02d' % (next) : {'ansible_ssh_host' : addr}})

            next = next + 1
            
#---------------------------------------------------------------------------    
# Update inventory (add nodes)
#---------------------------------------------------------------------------    
    def updateInventory(self):

        for host in self.data[self.ALL_KEY][self.HOSTS_KEY]:
            
            if (host == self.nodeprefix+'01'):
                self.data[self.FIRST_MGR_KEY][self.HOSTS_KEY].update(
                    {self.nodeprefix+'01' : None})
            elif (host == self.nodeprefix+'02' or host == self.nodeprefix+'03'):
                self.data[self.OTHER_MGRS_KEY][self.HOSTS_KEY].update({host : None})
            else:
                self.data[self.WORKERS_KEY][self.HOSTS_KEY].update({host : None})

            # For now, all nodes should host es        
            self.data[self.ES_HOSTS_KEY][self.HOSTS_KEY].update({host : None})

#---------------------------------------------------------------------------    
# Main
#---------------------------------------------------------------------------    
def main():

    if len(sys.argv) != 2:
        print("Usage: inventory filename")
        sys.exit()
        
    inventory = Inventory(sys.argv[1])
    inventory.collectInventoryDataFromUser()
    inventory.updateInventory()
    inventory.save()
    
if __name__ == "__main__":
    main()
