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
    along with audio_date_formatter.
    If not, see <http://www.gnu.org/licenses/>.
'''

from configobj import ConfigObj
from os import listdir, symlink, chdir, unlink, rename
from os.path import join, isdir, realpath, getmtime, splitext, basename
from datetime import date, datetime
from subprocess import check_output, CalledProcessError
from logging import getLogger, FileHandler, Formatter, INFO
from time import gmtime

config = ConfigObj('config')
handler = FileHandler(config['dir']['log'])

# Don't touch nothing below this line

'''
Logic:

1. The script will be run at 00:01
2. If the file in the loop is from today nothing else will be done
3. If at time of update the symlink the file is open, nothing will be done
'''

class NoAudioFile(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

logger = getLogger('audio_date_formatter')
formatter = Formatter( '%(asctime)s - %(lineno)s: %(levelname)s %(message)s' )
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(INFO)

today = date.today().strftime(config['broadcast_date_format'])

def if_audio_ensure_mp3(path_file):
    "If audio file makes sure is .mp3 file, if not it converts to it"
    # TODO: sndhdr not working
    # https://docs.python.org/2/library/sndhdr.html#module-sndhdr
    file_type = check_output(['file', path_file]).split(': ')[1].strip()
    if any(tag in file_type for tag in config['audio_tags']['mp3']):
        pass
    elif any(tag in file_type for tag in config['audio_tags']['ogg']):
        path_file_ogg, extension_ogg = splitext(path_file)
        path_file_mp3 = path_file_ogg + '.mp3'
        try:
            check_output(['ffmpeg', '-y', '-loglevel', '-8', '-y', '-i',
                         path_file, '-acodec', 'libmp3lame', path_file_mp3])
        except CalledProcessError, e:
            logger.error(
                 'Not able to convert from .ogg to .mp3 file %s. Eception: %s'\
                         %(path_file, e)) 
        else:
            try:
                unlink(path_file)
            except OSError, e:
                logger.warning('Not able to remove file %s. Eception: %s'\
                               %(path_file, e))
            return path_file_mp3
    else:
        raise NoAudioFile(path_file)
    return path_file

def is_after(file, compared_date):
    "Returns true if next_broadcast has yyyymmdd date which is newer than file"
    if file.split('-')[0] > compared_date:
        return True
    return False

def safe_link(parent_path, program, file):
    "Creates a symlink if not already linked"
    # Check symlink is not already pointing to file
    # TODO: if aras recorder maybe the program.mp3 is a real file
    if (realpath(join(config['dir']['audio'], dir, program + '.mp3')) !=
        join(config['dir']['audio'], dir, file)):
        link_name = program + '.mp3'
        chdir(join(config['dir']['audio'], dir)) 
        # Check if there's already a symlink pointing to a different file
        try:
            symlink(file, link_name)
        except OSError, e:
            current_symlinked_file_path = realpath(join(\
                                                   config['dir']['audio'],
                                                   dir, link_name))
            # Check if the current symlink is NOT being reproduced now
            if check_output('lsof').find(current_symlinked_file_path) == -1:
                unlink(link_name)
                symlink(file, link_name)
            else:
                logger.error(
                     'Symlink "%s" is currently being reproduced. Not able to'\
                             ' change it to point to "%s"' % (link_name, file))

def date_format(audio_dir, program, filename):
    "Validates date format or rename the file to make it date format compliant"
    path_file = join(audio_dir, program, filename)
    broadcast_date = path_file.split('/')[-1].split('-')[0]
    try:
        datetime.strptime(broadcast_date, config['broadcast_date_format'])
    except ValueError:
        if config['wrong_date_format_action'] == 'rename':
            struct_time = gmtime(getmtime(path_file))
            # time.struct_time(tm_year=2015, tm_mon=6, tm_mday=3, tm_hour=18,
            # tm_min=49, tm_sec=24, tm_wday=2, tm_yday=154, tm_isdst=0)
            st_list = [str(ele).zfill(2) for ele in struct_time]
            formatted_filename = '%s%s%s-%s%s%s-%s' %(st_list[0], st_list[1],\
                                                      st_list[2], st_list[3],\
                                                      st_list[4], st_list[5],\
                                                      filename.replace(' ',''))
            rename(join(audio_dir, program, filename),
                   join(audio_dir, program, formatted_filename))
            filename = formatted_filename
    finally:
        return filename

for dir in listdir(config['dir']['audio']):
    path_dir = join(config['dir']['audio'],dir)
    file_list = listdir(path_dir)

    # TODO: skip config['dir']['ignore']
    #if isdir(path_dir) and (len(file_list) > 0):
    if isdir(path_dir) and (len(file_list) > 0) and\
    not any(dir in ignored_dir for ignored_dir in config['dir']['ignore']):
        program = dir
        next_broadcast = ''
        for file in file_list:
            path_file = join(config['dir']['audio'], dir, file)
            try:
                path_file = if_audio_ensure_mp3(path_file)
            except NoAudioFile:
                if config['dir'] == 'remove':
                    # TODO: implement
                    pass
                logger.warning('No audio file. Ignoring "%s"' % (path_file))
                break
            else:
                # TODO: I need to set again file variable, since it can .mp3
                file = basename(path_file)
                file = date_format(config['dir']['audio'], dir, file)
                file_date = file.split('-')[0]
                if next_broadcast == '':
                    next_broadcast = file
                # If file between today and next_broadcast time to update link
                elif ((next_broadcast < today and file_date > next_broadcast)\
                     or (next_broadcast > today and file_date <\
                         next_broadcast)):
                    next_broadcast = file
        if next_broadcast == '':
            logger.warning('No suitable audio file for program "%s"' %\
                           (program))
        else:
            safe_link(config['dir']['audio'], program, next_broadcast)
