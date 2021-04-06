import logging
from datetime import datetime

class logger:

    def __init__(self,handler:str):
        """Create a logger

        Args:
            handler (str): Handler for the logger
        """
        now = datetime.now()
        time = now.strftime("%Y-%m-%d-%H-%M-%S")
        
        logs_filename = f"logs/{handler}/{time}-log.txt"
        handle=handler
        logging.basicConfig(filename=logs_filename,filemode="w",level=logging.NOTSET)
        self.logger = logging.getLogger(handle)


    def log_info(self,msg: str):
        """ Functión to Log an info message in logs file
        Args:
        msg (str): Message to log
        """
        if not msg=="":
            now = datetime.now()
            logs_hour = now.strftime("%H:%M:%S")
            msg = f"{logs_hour}-{msg}"
            self.logger.info(msg)
        else:
            pass

    def log_warning(self,msg: str):
        """ Functión to Log an warning message in logs file
        Args:
        msg (str): Message to log
        """
        now = datetime.now()
        logs_hour = now.strftime("%H:%M:%S")
        msg = f"{logs_hour}-{msg}"
        self.logger.warning(msg)

    def log_error(self,msg: str):
        """ Functión to Log an error message in logs file
        Args:
        msg (str): Message to log
        """
        now = datetime.now()
        logs_hour = now.strftime("%H:%M:%S")
        msg = f"{logs_hour}-{msg}"
        self.logger.error(msg)

    def log_critical(self,msg: str):
        """ Functión to Log an critical error message in logs file
        Args:
        msg (str): Message to log
        """
        now = datetime.now()
        logs_hour = now.strftime("%H:%M:%S")
        msg = f"{logs_hour}-{msg}"
        self.logger.critical(msg)

    def log_debug(self,msg: str):
        """ Functión to Log an debug message in logs file
        Args:
        msg (str): Message to log
        """
        now = datetime.now()
        logs_hour = now.strftime("%H:%M:%S")
        msg = f"{logs_hour}-{msg}"
        self.logger.debug(msg)