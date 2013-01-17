#!/usr/bin/env python
# -*- coding: utf-8 -*-
#     
#     machine.py
#     
#     This file is part of the RoboEarth Cloud Engine framework.
#     
#     This file was originally created for RoboEearth
#     http://www.roboearth.org/
#     
#     The research leading to these results has received funding from
#     the European Union Seventh Framework Programme FP7/2007-2013 under
#     grant agreement no248942 RoboEarth.
#     
#     Copyright 2012 RoboEarth
#     
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#     
#     http://www.apache.org/licenses/LICENSE-2.0
#     
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.
#     
#     \author/s: Dominique Hunziker 
#     
#     

# Custom imports
from rce.error import InternalError, MaxNumberExceeded
from rce.master.base import Status
from rce.master.container import Container


class ContainerProcessError(Exception):
    """ Exception is raised if there is no free container process.
    """


class RobotProcessError(Exception):
    """ Exception is raised if there is no free robot process.
    """


class Distributor(object):
    """ The Distributor is responsible for selecting the appropriate robot
        process to create a websocket connection. It therefore also keeps track
        of all the robot processes registered with the cloud engine.
        
        There should only one instance running in the Master process.
    """
    def __init__(self):
        """ Initialize the Distributor.
        """
        self._robots = set()
        self._iter = iter(self._robots)
    
    def registerRobotProcess(self, robot):
        assert robot not in self._robots
        self._robots.add(robot)
    
    def unregisterRobotProcess(self, robot):
        assert robot in self._robots
        self._robots.remove(robot)
    
    def getNextLocation(self):
        """ Get the next endpoint running in an robot process to create a new
            robot websocket connection.
            
            @return:            Next robot endpoint.
            @rtype:             rce.master.robot.RobotEndpoint
                                (subclass of rce.master.base.Proxy)
        """
        try:
            return min(self._robots, key=lambda r: r.active)
        except ValueError:
            raise RobotProcessError('There is no free robot process.')
    
    def cleanUp(self):
        assert len(self._robots) == 0


class LoadBalancer(object):
    """ The Load Balancer is responsible for selecting the appropriate
        container to launch a new container. It therefore also keeps track
        of all the container processes registered with the cloud engine.
        
        There should only one instance running in the Master process.
    """
    def __init__(self):
        """ Initialize the Load Balancer.
        """
        self._machines = set()
    
    def createMachine(self, ref, maxNr):
        """ Create a new Machine object, which can be used to create new
            containers.
            
            @param ref:         Remote reference to the ContainerClient in the
                                container process.
            @type  ref:         twisted::RemoteReference
            
            @param maxNr:       The maximum number of container which are
                                allowed in the machine.
            @type  maxNr:       int
            
            @return:            New Machine instance.
            @rtype:             rce.master.machine.Machine
        """
        machine = Machine(ref, maxNr)
        self._machines.add(machine)
        return machine
    
    def destroyMachine(self, machine):
        """ Destroy a Machine object.
            
            @param machine:     Machine instance which should be destroyed.
            @type  machine:     rce.master.machine.Machine
        """
        try:
            self._machines.remove(machine)
        except KeyError:
            raise InternalError('Tried to remove a non existent machine.')
        
        machine.destroy()
    
    def _getNextMachine(self):
        """ Internally used method to retrieve the machine where the next
            container should be created.
        """
        try:
            return min(self._machines, key=lambda m: m.active)
        except ValueError:
            raise ContainerProcessError('There is no free container process.')
    
    def createContainer(self, uid):
        """ Select an appropriate machine and create a container.
            
            @param uid:         Unique ID which is used to identify the
                                environment process when he connects to the
                                Master.
            @type  uid:         str
            
            @return:            New Container instance.
            @rtype:             rce.master.machine.Container
        """
        return self._getNextMachine().createContainer(uid)
    
    def cleanUp(self):
        """ Method should be called to destroy all machines.
        """
        for machine in self._machines.copy():
            self.destroyMachine(machine)
        
        assert len(self._machines) == 0


class Machine(object):
    """ Representation of a machine in which containers can be created. It
        keeps track of all the containers running in the machine.
    """
    def __init__(self, ref, maxNr):
        """ Initialize the Machine.
            
            @param ref:         Remote reference to the ContainerClient in the
                                container process.
            @type  ref:         twisted::RemoteReference
            
            @param maxNr:       The maximum number of container which are
                                allowed in the machine.
            @type  maxNr:       int
        """
        self._ref = ref
        self._maxNr = maxNr
        self._ip = ref.broker.transport.getPeer().host
        
        self._containers = set()
    
    @property
    def active(self):
        """ The number of active containers in the machine. """
        return len(self._containers)
    
    def createContainer(self, uid):
        """ Create a container.
            
            @param uid:         Unique ID which is used to identify the
                                environment process when he connects to the
                                Master.
            @type  uid:         str
            
            @return:            New Container instance.
            @rtype:             rce.master.machine.Container
        """
        if len(self._containers) > self._maxNr:
            raise MaxNumberExceeded('Can not create more containers in this '
                                    'machine.')
        
        container = Container(self)
        status = Status(container)
        self._ref.callRemote('createContainer', status,
                             uid).chainDeferred(container)
        return container
    
    def registerContainer(self, container):
        assert container not in self._containers
        self._containers.add(container)
    
    def unregisterContainer(self, container):
        assert container in self._containers
        self._containers.remove(container)
    
    def destroy(self):
        """ Method should be called to destroy the machine and will take care
            of deleting all circular references.
        """
        for container in self._containers.copy():
            container.destroy()
        
        assert len(self._containers) == 0
    
    def __eq__(self, other):
        return self._ip == other._ip
    
    def __ne__(self, other):
        return self._ip != other._ip
    
    def __hash__(self):
        return hash(self._ip)