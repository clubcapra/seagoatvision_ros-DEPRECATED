#! /usr/bin/env python

#    Copyright (C) 2012  Club Capra - capra.etsmtl.ca
#
#    This file is part of CapraVision.
#    
#    CapraVision is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Contains the FilterChain class and helper functions to work with the filter chain."""

import CapraVision.server.filters

from CapraVision.server.filters.dataextract import DataExtractor
from CapraVision.server.filters.parameter import Parameter

import ConfigParser
import types

import numpy as np

def my_import(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod

def params_list(chain):
    flist = []
    for filtre in chain.filters:
        fname = filtre.__class__.__name__
        params = []
        for name in dir(filtre):
            parameter = getattr(filtre, name)
            if not isinstance(parameter, Parameter):
                continue
            params.append((name, parameter.get_current_value()))
        flist.append((fname, params))
    return flist

def isnumeric(string):
    try:
        float(string)
        return True
    except ValueError:
        return False
    
def read(file_name):
    """Open a filtre chain file and load its content in a new filtre chain."""
    new_chain = FilterChain()
    cfg = ConfigParser.ConfigParser()
    cfg.read(file_name)
    for section in cfg.sections():
        filtre = CapraVision.server.filters.create_filter(section) 
        for member in filtre.__dict__:
            parameter = getattr(filtre,member)
            if not isinstance(parameter, Parameter):
                continue
            val = cfg.get(section, member)
            if val == "True" or val == "False":
                parameter.set_current_value(cfg.getboolean(section, member))
            elif isnumeric(val):
                parameter.set_current_value(cfg.getfloat(section, member))
            else:
                if isinstance(val, str):
                    val = '\n'.join([line[1:-1] for line in str.splitlines(val)])
                parameter.set_current_value(val)
        if hasattr(filtre, 'configure'):
            filtre.configure()
        new_chain.add_filter(filtre)
    return new_chain

def write(file_name, chain):
    """Save the content of the filter chain in a file."""
    cfg = ConfigParser.ConfigParser()
    for fname, params in params_list(chain):
        cfg.add_section(fname)
        for name, value in params:
            if isinstance(value, str):
                value = '\n'.join(['"%s"' % line for line in str.splitlines(value)])
            cfg.set(fname, name, value)
    cfg.write(open(file_name, 'w'))
    
class FilterChain:
    """ Observable.  Contains the chain of filters to execute on an image.

    The observer must be a method that receive a filter and an image as parameter.
    The observer method is called after each execution of a filter in the filter chain.
    """
    def __init__(self):
        self.filters = []
        self.image_observers = {}
        self.filter_output_observers = []

    def count(self):
        return len(self.filters)

    def get_filter_output_observers(self):
        return self.filter_output_observers

    def get_filter_list(self):
        class Filter: pass
        retValue = []
        for item in self.filters:
            filter = Filter()
            setattr(filter, "name", item.__class__.__name__)
            setattr(filter, "doc", item.__doc__)
            retValue.append(filter)
        return retValue

    def __getitem__(self, index):
        return self.filters[index]

    def add_filter(self, filtre):
        self.filters.append(filtre)

    def remove_filter(self, filtre):
        self.filters.remove(filtre)

    def reload_filter(self, filtre=None):
        # if filter is none, we reload all filters
        if filtre is None:
            lstFilterIndex = range(len(self.filters))
        elif filtre in self.filters:
            lstFilterIndex = [self.filters.index(filtre)]
        else:
            lstFilterIndex = []
            
        # example of __module__:
        for index in lstFilterIndex:
            item = self.filters[index]
            # reload the module
            module = my_import(item.__module__)
            reload(module)
            # recreate the instance
            self.filters[index] = getattr(module , item.__class__.__name__)()
            
    def add_image_observer(self, observer, filter_name):
        lstObserver = self.image_observers.get(filter_name, [])
        if lstObserver:
            if observer in lstObserver:
                print("This observer already observer the filter %s" % filter_name)
                return False
            else:
                lstObserver.append(observer)
        else:
            self.image_observers[filter_name] = [observer]
        return True

    def remove_image_observer(self, observer, filter_name):
        lstObserver = self.image_observers.get(filter_name, [])
        if lstObserver:
            if observer in lstObserver:
                lstObserver.remove(observer)
                if not lstObserver:
                    del self.image_observers[filter_name]
                return True

        print("This observer is not in observation list for filter %s" % filter_name)
        return False

    def add_filter_output_observer(self, output):
        self.filter_output_observers.append(output)
        for f in self.filters:
            if isinstance(f, DataExtractor):
                f.add_output_observer(output)
        return True

    def remove_filter_output_observer(self, output):
        self.filter_output_observers.remove(output)
        for f in self.filters:
            if isinstance(f, DataExtractor):
                f.remove_output_observer(output)
        return True

    def execute(self, image):
        for f in self.filters:
            image = f.execute(image)
            lst_observer = self.image_observers.get(f.__class__.__name__, [])
            for observer in lst_observer:
                # copy the picture because the next filter will modify him
                observer(np.copy(image))
        return image

