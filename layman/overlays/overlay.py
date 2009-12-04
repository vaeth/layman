#!/usr/bin/python
# -*- coding: utf-8 -*-
#################################################################################
# LAYMAN OVERLAY BASE CLASS
#################################################################################
# File:       overlay.py
#
#             Base class for the different overlay types.
#
# Copyright:
#             (c) 2005 - 2009 Gunnar Wrobel
#             (c) 2009        Sebastian Pipping
#             Distributed under the terms of the GNU General Public License v2
#
# Author(s):
#             Gunnar Wrobel <wrobel@gentoo.org>
#             Sebastian Pipping <sebastian@pipping.org>
#
''' Basic overlay class.'''

__version__ = "$Id: overlay.py 273 2006-12-30 15:54:50Z wrobel $"

#===============================================================================
#
# Dependencies
#
#-------------------------------------------------------------------------------

import sys, types, re, os, os.path, shutil, subprocess

from   layman.utils             import node_to_dict, dict_to_node, path

from   layman.debug             import OUT

#===============================================================================
#
# Class Overlay
#
#-------------------------------------------------------------------------------

class Overlay:
    ''' Derive the real implementations from this.'''

    type = 'None'

    def __init__(self, xml, ignore = 0, quiet = False):
        '''
        >>> here = os.path.dirname(os.path.realpath(__file__))
        >>> document = open(here + '/../tests/testfiles/global-overlays.xml').read()
        >>> import xml.dom.minidom
        >>> document = xml.dom.minidom.parseString(document)
        >>> overlays = document.getElementsByTagName('overlay')
        >>> a = Overlay(overlays[0])
        >>> a.name
        u'wrobel'
        >>> a.is_official()
        True
        >>> a.src
        u'https://overlays.gentoo.org/svn/dev/wrobel'
        >>> a.owner_email
        u'nobody@gentoo.org'
        >>> a.description
        u'Test'
        >>> a.priority
        10
        >>> b = Overlay(overlays[1])
        >>> b.is_official()
        False
        '''
        self.quiet = quiet

        self.data = node_to_dict(xml)

        if '<name>1' in self.data.keys():
            self.name = self.data['<name>1']['@'].strip()
        elif '&name' in self.data.keys():
            self.name = self.data['&name']
        else:
            raise Exception('Overlay is missing a "name" entry!')

        if '<source>1' in self.data.keys():
            self.src = self.data['<source>1']['@'].strip()
        elif '&src' in self.data.keys():
            self.src = self.data['&src']
        else:
            raise Exception('Overlay "' + self.name + '" is missing a "source" '
                            'entry!')

        if '<owner>1' in self.data.keys() and \
                '<email>1' in self.data['<owner>1']:
            self.owner_email = self.data['<owner>1']['<email>1']['@'].strip()
            if '<name>1' in self.data['<owner>1']:
                self.owner_name = self.data['<owner>1']['<name>1']['@'].strip()
            else:
                self.owner_name = None
        elif '&contact' in self.data.keys():
            self.owner_email = self.data['&contact']
            self.owner_name = None
        else:
            self.owner_email = ''
            self.owner_name = None
            if not ignore:
                raise Exception('Overlay "' + self.name + '" is missing a '
                                '"owner.email" entry!')
            elif ignore == 1:
                OUT.warn('Overlay "' + self.name + '" is missing a '
                         '"owner.email" entry!', 4)

        if '<description>1' in self.data.keys():
            self.description = self.data['<description>1']['@'].strip()
        else:
            self.description = ''
            if not ignore:
                raise Exception('Overlay "' + self.name + '" is missing a '
				'"description" entry!')
            elif ignore == 1:
                OUT.warn('Overlay "' + self.name + '" is missing a '
			 '"description" entry!', 4)

        if '&status' in self.data.keys():
            self.status = self.data['&status']
        else:
            self.status = ''

        if '&priority' in self.data.keys():
            self.priority = int(self.data['&priority'])
        else:
            self.priority = 50

    def set_priority(self, priority):
        '''Set the priority of this overlay.'''

        self.data['&priority'] = str(priority)
        self.priority = int(priority)

    def to_minidom(self, document):
        '''Convert to xml.'''

        return dict_to_node(self.data, document, 'overlay')

    def add(self, base, quiet = False):
        '''Add the overlay.'''

        mdir = path([base, self.name])

        if os.path.exists(mdir):
            raise Exception('Directory ' + mdir + ' already exists. Will not ov'
                            'erwrite its contents!')

        os.makedirs(mdir)

    def sync(self, base, quiet = False):
        '''Sync the overlay.'''
        pass

    def delete(self, base):
        '''Delete the overlay.'''
        mdir = path([base, self.name])

        if not os.path.exists(mdir):
            raise Exception('Directory ' + mdir + ' does not exist. Cannot remo'
                            've the overlay!')

        shutil.rmtree(mdir)

    def cmd(self, command):
        '''Run a command.'''

        OUT.info('Running command "' + command + '"...', 2)

        if hasattr(sys.stdout,'encoding'):
            enc = sys.stdout.encoding or sys.getfilesystemencoding()
            if enc:
                command = command.encode(enc)

        if not self.quiet:
            return os.system(command)
        else:
            cmd = subprocess.Popen([command], shell = True,
                                   stdout = subprocess.PIPE,
                                   stderr = subprocess.PIPE,
                                   close_fds = True)
            result = cmd.wait()
            return result

    def __str__(self):
        '''
        >>> here = os.path.dirname(os.path.realpath(__file__))
        >>> document = open(here + '/../tests/testfiles/global-overlays.xml').read()
        >>> import xml.dom.minidom
        >>> document = xml.dom.minidom.parseString(document)
        >>> overlays = document.getElementsByTagName('overlay')
        >>> a = Overlay(overlays[0])
        >>> print str(a)
        wrobel
        ~~~~~~
        Source  : https://overlays.gentoo.org/svn/dev/wrobel
        Contact : nobody@gentoo.org
        Type    : None; Priority: 10
        <BLANKLINE>
        Description:
          Test
        <BLANKLINE>
        '''

        result = u''

        result += self.name + u'\n' + (len(self.name) * u'~')

        result += u'\nSource  : ' + self.src
        if self.owner_name != None:
            result += u'\nContact : %s <%s>' % (self.owner_name, self.owner_email)
        else:
            result += u'\nContact : ' + self.owner_email
        result += u'\nType    : ' + self.type
        result += u'; Priority: ' + str(self.priority) + u'\n'

        description = self.description
        description = re.compile(u' +').sub(u' ', description)
        description = re.compile(u'\n ').sub(u'\n', description)
        result += u'\nDescription:'
        result += u'\n  '.join((u'\n' + description).split(u'\n'))
        result += u'\n'

        for key in (e for e in ('<homepage>1', '<link>1') if e in self.data.keys()):
            link = self.data[key]['@'].strip()
            link = re.compile(u' +').sub(u' ', link)
            link = re.compile(u'\n ').sub(u'\n', link)
            result += u'\nLink:\n'
            result += u'\n  '.join((u'\n' + link).split(u'\n'))
            result += u'\n'
            break

        return result

    def short_list(self, width = 0):
        '''
        >>> here = os.path.dirname(os.path.realpath(__file__))
        >>> document = open(here + '/../tests/testfiles/global-overlays.xml').read()
        >>> import xml.dom.minidom
        >>> document = xml.dom.minidom.parseString(document)
        >>> overlays = document.getElementsByTagName('overlay')
        >>> a = Overlay(overlays[0])
        >>> print a.short_list(80)
        wrobel                    [None      ] (https://o.g.o/svn/dev/wrobel         )
        '''

        def pad(string, length):
            '''Pad a string with spaces.'''
            if len(string) <= length:
                return string + ' ' * (length - len(string))
            else:
                return string[:length - 3] + '...'

        def terminal_width():
            '''Determine width of terminal window.'''
            try:
                width = int(os.environ['COLUMNS'])
                if width > 0:
                    return width
            except:
                pass
            try:
                import struct, fcntl, termios
                query = struct.pack('HHHH', 0, 0, 0, 0)
                response = fcntl.ioctl(1, termios.TIOCGWINSZ, query)
                width = struct.unpack('HHHH', response)[1]
                if width > 0:
                    return width
            except:
                pass
            return 80

        name   = pad(self.name, 25)
        mtype  = ' [' + pad(self.type, 10) + ']'
        if not width:
            width = terminal_width()
        srclen = width - 43
        source = self.src
        if len(source) > srclen:
            source = source.replace("overlays.gentoo.org", "o.g.o")
        source = ' (' + pad(source, srclen) + ')'

        return name + mtype + source

    def supported(self, binaries = []):
        '''Is the overlay type supported?'''

        if binaries:
            for mpath, mtype, package in binaries:
                if not os.path.exists(mpath):
                    raise Exception('Binary ' + mpath + ' seems to be missing!'
                                    ' Overlay type "' + mtype + '" not support'
                                    'ed. Did you emerge ' + package + '?')

        return True

    def is_supported(self):
        '''Is the overlay type supported?'''

        try:
            self.supported()
            return True
        except Exception, error:
            return False

    def is_official(self):
        '''Is the overlay official?'''

        return self.status == 'official'

#================================================================================
#
# Testing
#
#--------------------------------------------------------------------------------

if __name__ == '__main__':
    import doctest, sys
    doctest.testmod(sys.modules[__name__])
