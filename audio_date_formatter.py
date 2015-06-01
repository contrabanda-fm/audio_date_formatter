#!/usr/bin/python
'''
    Copyright 2015 Javier Legido javi@legido.com

    rss_py is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    rss_py is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with audio_date_formatter.  If not, see <http://www.gnu.org/licenses/>.
'''

from configobj import ConfigObj
from os import listdir, symlink, chdir, unlink
from os.path import join, isdir, realpath
from datetime import date, datetime
from subprocess import check_output
from logging import getLogger, FileHandler, Formatter, INFO

config = ConfigObj('config')
handler = FileHandler(config['dir']['log'])

# Don't touch nothing below this line

'''
Logic:

1. The script will be run at 00:01
2. If the file in the loop is from today nothing else will be done
3. If at time of update the symlink the file is open, nothing will be done
'''

logger = getLogger('audio_date_formatter')
formatter = Formatter( '%(asctime)s - %(lineno)s: %(levelname)s %(message)s' )
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(INFO)

today = date.today().strftime(config['broadcast_date_format'])

def is_audio_file(filename):
    "Returns true if is an audio file"
    # TODO: sndhdr not working https://docs.python.org/2/library/sndhdr.html#module-sndhdr
    if 'Audio' in check_output(['file', filename]).split(': ')[1].strip():
        return True
    else:
        return False

def is_valid_date(path_file):
    "Returns true if date is compliant with config['broadcast_date_format']"
    broadcast_date = path_file.split('/')[-1].split('-')[0]
    try:
        datetime.strptime(broadcast_date, config['broadcast_date_format'])
    except ValueError:
        #raise ValueError("Incorrect data format, should be YYYY-MM-DD")
        logger.warning('Wrong file name data format. File "%s"' % (path_file))
        return False
    return True

def is_after(file, compared_date):
    "Returns true if next_broadcast has yyyymmdd date which is newer than file"
    if file.split('-')[0] > compared_date:
        return True
    return False

def safe_link(parent_path, program, file):
    "Creates a symlink if not already linked"
    # Check symlink is not already pointing to file
    if (realpath(join(config['dir']['audio'], dir, program + '.mp3')) !=
        join(config['dir']['audio'], dir, file)):
        link_name = program + '.mp3'
        chdir(join(config['dir']['audio'], dir)) 
        # Check if there's already a symlink pointing to a different file
        try:
            symlink(file, link_name)
        except OSError, e:
            current_symlinked_file_path = realpath(join(config['dir']['audio'], dir,
                                                  link_name))
            # Check if the current symlink is NOT being reproduced now
            if check_output('lsof').find(current_symlinked_file_path) == -1:
                unlink(link_name)
                symlink(file, link_name)
            else:
                logger.error('Symlink "%s" is currently being reproduced. Not able to'\
                             ' change it to point to "%s"' % (link_name, file))    

for dir in listdir(config['dir']['audio']):
    path_dir = join(config['dir']['audio'],dir)
    file_list = listdir(path_dir)

    if isdir(path_dir) and (len(file_list) > 0):
        program = dir
        next_broadcast = ''
        for file in file_list:
            path_file = join(config['dir']['audio'], dir, file)
            if is_audio_file(path_file):
                if is_valid_date(path_file):
                    file_date = file.split('-')[0]
                    if next_broadcast == '':
                        next_broadcast = file
                        # I'll arrange the symlinks at the end of the program files loop
                        #safe_link(config['dir']['audio'], program, file)
                    # If file is between today and next_broadcast time to update the link
                    elif ((next_broadcast < today and file_date > next_broadcast) or
                         (next_broadcast > today and file_date < next_broadcast)):
                        next_broadcast = file
            else:
                if config['dir'] == 'remove':
                    # TODO: implement
                    pass
                elif config['dir'] == 'move':
                    # TODO: implement
                    pass
                else:
                    logger.warning('No audio file. Ignoring "%s"' % (path_file))
        if next_broadcast == '':
            logger.warning('No suitable audio file for program "%s"' % (program))    
        else:
            safe_link(config['dir']['audio'], program, next_broadcast)
