import argparse
import yaml
import re
import sys
import logging
import shutil
import datetime
import os

from logging.handlers import RotatingFileHandler

# Files for this program
MAIN_DIRECTORY = "/home/chandan/Documents/timeMachine"
# Backup Directory
PARAM_DIR = MAIN_DIRECTORY+'/'+'backupFolder'
# Config File
CONFIG_FILE = MAIN_DIRECTORY+'/'+'config.dat'
# location of log file
LOG_FILENAME = 'timeMachine.log'
#ArgParse is the one setting up all the CLI commands we are to give and parse them into a dictionary so as we can access
parser = argparse.ArgumentParser(
                    description='Match files for certain matches & run program on matches')
parser.add_argument('-d', '--dir',
                    help = 'Storage Directory for file copies', default ="./")
parser.add_argument('-c', '--configfile', default="./\config.dat",
                    help='file to read the config from')
parser.add_argument('-R', '--remove',
                    help='remove a file from configuration')
parser.add_argument('-A', '--add',
                    help='add a file to configuration')
parser.add_argument('-L', '--list',
                    help='list files configuration')

args = parser.parse_args()
# After Parsing we have a args dictionary and accessing the values inside using .
param_config = args.configfile
param_dir = args.dir
param_remove = args.remove
param_add = args.add

# This function is the one creating a new log file when maxBytes are reached. This concept is called log rotation
rotating_handler = RotatingFileHandler(LOG_FILENAME,
                                       maxBytes=10000000,
                                       backupCount=3)

formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
rotating_handler.setFormatter(formatter)

# Here Setting up app name and DEBUG Level depicting logs are provided when we want to solve an issue or information logs
logger = logging.getLogger('timeMachine')
logger.setLevel(logging.DEBUG)
logger.addHandler(rotating_handler)


def display_files():
        # if args.list is not None:
        triggers = list_files(CONFIG_FILE)
#        print(triggers)
        print("List of files:")
        for t in triggers:
            print("\t", t['file'])
        sys.exit(0)

# List the files in YAML format after taking out the files from config dat. This function will be used in add, remove, update functionality
def list_files(filename):
    try:
        logger.debug("Reading config from {0}".format(filename))
        with open(filename,"r") as f:
            return yaml.load(f)
    except FileNotFoundError:
        logger.error("Config file {0} not found".format(filename))
        print("Config file {0} not found",format(filename))
        sys.exit(1)

#This function is intermediate function to create the desired path[2]
def get_output_directory(targetDirectory, path):
    return targetDirectory + "/" + re.sub("^-", "", path.replace("/", "-"))
#This function is the final step in creating the copy directory according to algorithm[3]. These functions are used for code cleanup
def full_dest(output_directory, path):
    return output_directory + "/" + os.path.basename(path) + datetime.datetime.now().strftime("-%y%m%d%H%M%S")

# This function will be removing from actual location and thus we are using os operation here
def remove_file(param_config, remove):
    try:
        data_config = list_files(param_config)
        newdata = []
        if data_config is not None:
            for d in data_config:
                if d['file'] != remove:
                    newdata.append(d['file'])
        # Removing file from location
        os.remove(remove)
        # writing back to config
        with open(CONFIG_FILE, 'w') as file:
            for i in newdata:
                file.write("- file: {}\n".format(str(i)))
        logger.info("Removed {0}".format(remove))

    except FileNotFoundError:
        logger.error("File {0} not found".format(remove))
        print("File {0} not found".format(remove))
        sys.exit(1)
    pass
# This function doing addition of desired path into the config.dat file at the same time in backup folder adding the directory and file as the first update

def add_file(config, add):
    try:
        logger.info("Added {0}".format(add))
        data_config = list_files(config)
        # data_config.append(add)
        # print(data_config)
        # add file directory to configfile
        newdata = []
        print('data_config',data_config)
        if data_config is not None:
          for d in data_config:
            newdata.append(d['file'])
          newdata.append(add)
        
          with open(CONFIG_FILE, 'w') as file:
            for i in newdata:
                print("i",i)
                file.write("- file: {}\n".format(str(i)))

    except FileNotFoundError:
        logger.error("Config file {0} not found".format(add))
        print("Config file {0} not found".format(add))
        sys.exit(1)
    pass
#This function will be the update function allowing us to check and add the files to backup folder by creating a directory for new files

def check_files_and_copy(configData, paramDir):
    print ('paramDir',paramDir)
    targetDirectory = paramDir
    paths = []
    filesList = list_files(configData)
    #configData is data from our config.dat file in yaml format. This is checked regularly for any changes later in cron
    for file in filesList:
        paths.append(file['file'])
    if not os.path.exists(targetDirectory):
     #Here We will avoid an error and create a directory to backup if directory is not present ie first time we run the program
        os.makedirs(targetDirectory)

    for path in paths:
        '''
        Format the output directory as subdirectory with the source filename+path as the directory.
        '''
        output_directory = get_output_directory(targetDirectory, path)
        if os.path.exists(path):
            print("path",path,os.path.getmtime(path))
            fulldst = full_dest(output_directory, path)
            # print("output", os.path.getmtime(output_directory))                            # function creating path according to algorithm
            if not os.path.exists(output_directory):             # - First pass, create the directory
                os.makedirs(output_directory)
                shutil.copy2(path, fulldst)
        # Exist version, check and copy if required
        # If the mod time on the directory is greater than the file then it doesn't need to be copied.
        # Assumption is that nothing is added or deleted to the target directory outside of this tool.
        elif os.path.getmtime(path) > os.path.getmtime(output_directory):
            # The destination file is the absolute path the filename and the timestamp yyyymmddHHMMSS
            shutil.copy2(path, fulldst)
    display_files()
    pass


if __name__ == '__main__':
    # check for CLI of 3 types add remove list
    print('sys arg', sys.argv,param_add)
    if len(sys.argv) > 1:
        if param_add is not None:
            add_file(CONFIG_FILE, param_add)
            print("\nFILE ADDED")
        if param_remove is not None:
            remove_file(CONFIG_FILE, sys.argv[2])
            print("\nFILE REMOVED")
        if sys.argv[1] == 'list':
            display_files()

    print("\tUpdating config file...")
    check_files_and_copy(CONFIG_FILE, PARAM_DIR)
