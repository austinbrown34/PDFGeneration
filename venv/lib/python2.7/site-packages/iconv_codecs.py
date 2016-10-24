#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


r"""
iconv_codec: module to register python codecs to encode/decode any char 
supported by system's iconv command.

Usage:
   iconv supports codecs unsupported by python:

   >>> u'testing'.encode('ansi_x3.110-1983')
   Traceback (most recent call last):
   ...
   LookupError: unknown encoding: ansi_x3.110-1983
   >>> import iconv_codecs
   >>> 'ansi_x3.110-1983' in iconv_codecs.get_supported_codecs()
   True
   
   Just register the codec you want:
   
   >>> iconv_codecs.register('ansi_x3.110-1983')
   
   Then you can use it:
   
   >>> u'testing'.encode('ansi_x3.110-1983')
   'testing'

   If you want to force iconv usage for an encoding already supported by python, 
   just use the encoding name with an 'iconv:' prefix (no need to register):

   >>> '\x87'.decode('iconv:CP860')
   u'\xe7'

   To register all python unsupported codecs, just call register() without
   parameters:
   
   >>> iconv_codecs.register()
   >>> u'\xe7'.encode('utf32')
   '\xff\xfe\x00\x00\xe7\x00\x00\x00'
   
   That will poll iconv for a list of codecs it supports and register the ones
   python doesn't support already.   


The module will look for iconv in the path. If you need a different iconv
location just set it:

   >>> iconv_codecs.ICONV_EXECUTABLE = '/usr/bin/iconv'
"""

import codecs
import subprocess
import os

#: change this to reflect your installation path
ICONV_EXECUTABLE='iconv' 

#: Global with the names of registered codecs
_codecs = set() 

def _get_unregistered_codecs():
    """Returns a list of iconv codecs that aren't supported by python directly"""
    for codec in get_supported_codecs():
        try:
            u'a'.encode(codec)
        except UnicodeEncodeError:
            pass
        except LookupError:
            yield codec

def register(*codecs):
    """ 
    Register the codecs passed for iconv usage. Codecs previously registered
    will be unregistered.
    
    >>> import iconv_codecs
    >>> iconv_codecs.register('ansi_x3.110-1983')

    Then you can use it:

    >>> u'testing'.encode('ansi_x3.110-1983')
    'testing'

    If you want to register all codecs not already supported by python, just
    suppress all arguments:

    >>> iconv_codecs.register()
    """
    if not codecs:
        codecs = _get_unregistered_codecs()
    _codecs.update(codec.lower() for codec in codecs)


def get_supported_codecs():
    """
    Returns a list of iconv supported codecs
    """
    cmd = [ICONV_EXECUTABLE, '--list']
    iconv = subprocess.Popen(cmd, env={'LANG': 'C'}, 
                             stdout=subprocess.PIPE,
                             stdin=open(os.devnull, 'w+'),
                             stderr=open(os.devnull, 'w+'))
    return set(line.strip('/').lower() for line in iconv.communicate()[0].splitlines())
    
def _run_iconv(from_codec, to_codec, extra_params=None):
    cmd = [ICONV_EXECUTABLE, '-f', from_codec, '-t', to_codec, '-s']
    if extra_params is not None:
        cmd.extend(extra_params)
    iconv = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                  stdin=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  env={'LANG': 'C'})
    return iconv    

def _iconv_factory(codec_name):
    codec_name = codec_name.lower()
    if codec_name.startswith('iconv:'):
        name = codec_name[6:]
    elif codec_name in _codecs:
        name = codec_name
    else:  # unsuported or unregistered codec
        return

    def iconvencode(input, errors='strict', encoding=name):
        extra = []
        if errors == 'ignore':
            extra.append('-c')
        elif errors != 'strict':
            raise NotImplementedError("%r error handling not implemented"
                                      " for codec %r" % (errors, encoding))

        _input = input.encode('utf-8')
        iconv = _run_iconv('utf-8', encoding, extra)
        output, error = iconv.communicate(_input)
        if error:
            error = error.splitlines()[0]
            raise UnicodeEncodeError(encoding, input, 0, len(input), error)
        return output, len(input)

    def iconvdecode(input, errors='strict', encoding=name):
        extra = []
        if errors == 'ignore':
            extra.append('-c')
        elif errors != 'strict':
            raise NotImplementedError('%r error handling not implemented' 
                                      ' for codec %r' % (errors, encoding))
        _input = str(input)
        iconv = _run_iconv(encoding, 'utf-8', extra)
        output, error = iconv.communicate(_input)
        if error:
            error = error.splitlines()[0]
            raise UnicodeDecodeError(encoding, input, 0, len(input), error)
        output = output.decode('utf-8')
        return output, len(input)

    class IncrementalEncoder(codecs.IncrementalEncoder):
        def encode(self, input, final=False):
            return iconvencode(input, self.errors)[0]

    class IncrementalDecoder(codecs.BufferedIncrementalDecoder):
        _buffer_decode = staticmethod(iconvdecode)

    class StreamWriter(codecs.StreamWriter):
        pass
    StreamWriter.encode = staticmethod(iconvencode)

    class StreamReader(codecs.StreamReader):
        pass
    StreamReader.decode = staticmethod(iconvdecode)

    return codecs.CodecInfo(
            name=codec_name,
            encode=iconvencode,
            decode=iconvdecode,
            incrementalencoder=IncrementalEncoder,
            incrementaldecoder=IncrementalDecoder,
            streamreader=StreamReader,
            streamwriter=StreamWriter,
        )

codecs.register(_iconv_factory)

if __name__ == '__main__':
    x = u'áéíóúççç'
    assert x == x.encode('iconv:utf-8').decode('iconv:utf-8')
    import doctest
    doctest.testmod()
