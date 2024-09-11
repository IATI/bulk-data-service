import urllib3


def misc_global_initialisation(context: dict):
    # these warnings are turned off because many IATI XML files are served
    # from web servers with misconfigured certificates, so we can't verify
    # certificates, and without this the logs fill up with warnings saying we
    # should turn verification on
    urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)
