#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       DjangoDB.py
#       
#       Copyright 2012 dominique hunziker <dominique.hunziker@gmail.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#       
#       

import settings as rosSettings

import sys
from django.conf import settings

settings.configure(
    DATABASE_ENGINE=rosSettings.DJANGO_DB.get('DATABASE_ENGINE', ''),
    DATABASE_NAME=rosSettings.DJANGO_DB.get('DATABASE_NAME', ''),
    DATABASE_USER=rosSettings.DJANGO_DB.get('DATABASE_USER', ''),
    DATABASE_PASSWORD=rosSettings.DJANGO_DB.get('DATABASE_PASSWORD', ''),
    DATABASE_HOST=rosSettings.DJANGO_DB.get('DATABASE_HOST', ''),
    DATABASE_PORT=rosSettings.DJANGO_DB.get('DATABASE_PORT', ''),
    TIME_ZONE=rosSettings.DJANGO_DB.get('TIME_ZONE', ''),
)

if rosSettings.DJANGO_ROOT_DIR not in sys.path:
    sys.path.append(rosSettings.DJANGO_ROOT_DIR)

from reappengine.models import Package, Node, Param, Interface

from Exceptions import InvalidRequest
from ROSUtil.Parser import createParameterParser, createInterfaceParser, createNodeParser

class DjangoDBError(Exception):
    """ This error is raised if an error occurred in conjunction with
        the django database.
    """
    pass

def _getPackage(pkg):
    """ Internal function to get the specified Package model instance.

        @param pkg:     Package name
        @type  pkg:     str

        @raise:     DjangoDBError if no or more than one matching model
                    is found.
    """
    package = Package.objects.filter(name=pkg)

    if len(package) != 1:
        if package:
            raise DjangoDBError('Package could not uniquely identified.')
        else:
            raise DjangoDBError('Package could not be found.')

    return package[0]

def _getNode(package, node):
    """ Internal function to get the specified Node model instance located
        in the specified package.

        @param package:     Package in which the node is located
        @type  package:     Package model instance

        @param node:    Node name
        @type  node:    str

        @raise:     DjangoDBError if no or more than one matching model
                    is found.
    """
    node = Node.objects.filter(name=node, pkg=package)

    if len(node) != 1:
        if package:
            raise DjangoDBError('Node could not uniquely identified.')
        else:
            raise DjangoDBError('Node could not be found.')

    return node[0]

def _getParam(node):
    """ Internal function to get a list of all the Param model instances
        for the given node.
        
        @param node:    Node for which the parameters should be searched
        @type  node:    Node
    """
    return Param.objects.filter(node=node)

def _getInterface(node):
    """ Internal function to get a list of all the Interface model instances
        for the given node.
        
        @param node:    Node for which the interfaces should be searched
        @type  node:    Node
    """
    return Interface.objects.filter(node=node)

def _split(name):
    """ Internal function to split and check a key.
    """
    parts = name.split('/')

    if len(parts) != 2:
        raise InvalidRequest('Key {0} is not valid.'.format(name))

    return tuple(parts)

def existsNode(key):
    """ Check if the given key is valid, i.e. if there is a matching
        entry in the database.

        @param key:     Key which should be checked
        @type  key:     str

        @return:    True if the key is valid; False otherwise
    """
    try:
        pkg, node = _split(key)
    except InvalidRequest:
        return False

    try:
        _getNode(_getPackage(pkg), node)
    except DjangoDBError:
        return False

    return True

def getNode(key):
    """ Get the node definition for the given key.

        @param key:     Key for which the node definition should be retrieved.
        @type  key:     str

        @return:    Node instance.
        @rtype:     Node

        @raise:     DjangoDBError
    """
    pkg, exe = _split(key)

    pkg = _getPackage(pkg)
    node = _getNode(pkg, exe)
    params = _getParam(node)
    interfaces = _getInterface(node)

    config = [createParameterParser(param.name, param.paramType, param.opt, param.default) for param in params]
    interfaces = [createInterfaceParser(interface.msgType, '{0}/{1}'.format(pkg.name, interface.msgDef), interface.name) for interface in interfaces]

    return createNodeParser(pkg.name, node.name, config, interfaces)