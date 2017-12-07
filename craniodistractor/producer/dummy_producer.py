'''
MODULE DESCRIPTION

Copyright (C) 2017  Simo Tumelius

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
import sys

from multiprocessing import Process, Queue




def run_producer(q):
    while 1:
        '''
        if sys.stdin.isatty():
            data = sys.stdin.readline()
        else:
            data = 'nothing to read\n'
        '''
        #data = sys.stdin.readline()
        sys.stdout.write('nothing to read\n')
        #sys.stdout.flush()

if __name__ == '__main__':
    run_producer()
