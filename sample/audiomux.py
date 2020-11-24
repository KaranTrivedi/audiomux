#!./venv/bin/python

"""
Docstring should be written for each file.
run `pylint filename.py` to find recommendations on improving format.
"""
import configparser
import json
import logging

#Define config and logger.
CONFIG = configparser.ConfigParser()
CONFIG.read("conf/config.ini")
SECTION = "audiomux"

logging.basicConfig(filename=CONFIG[SECTION]['log'],\
                    level=CONFIG[SECTION]['level'],\
                    format='%(asctime)s::%(name)s::%(funcName)s::%(levelname)s::%(message)s',\
                    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger(SECTION)

def show_sections():
    """
    Output all options for given section
    """

    conf_str = "\n\n"
    for sect in CONFIG.sections():
        conf_str += "[" + sect + "]\n"
        for var in list(CONFIG[sect]):
            conf_str += var + "\t\t=\t" + CONFIG[sect][var] + "\n"
    logger.info(conf_str)

class Audiomux:
    """
    Create sample class
    """

    def __init__(self, var):
        self.var = var

    def __str__(self):
        """
        stringify
        """
        return json.dumps(vars(self), indent=2)


def main():
    """
    Main function.
    """
    logger.info("####################STARTING####################")

    if CONFIG[SECTION]["level"] == "DEBUG":
        show_sections()

if __name__ == "__main__":
    main()
