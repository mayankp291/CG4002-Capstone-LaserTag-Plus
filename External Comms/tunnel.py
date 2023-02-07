import sshtunnel
import os


USER = os.environ.get('SUNFIRE_USERNAME')

def tunnel():
    tunnel1 = sshtunnel.open_tunnel(
        ssh_address_or_host = ('