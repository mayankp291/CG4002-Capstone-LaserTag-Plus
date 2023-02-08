import sshtunnel
import os
from dotenv import load_dotenv

# load environment variables
load_dotenv()

SOC_USERNAME = os.getenv("SOC_USERNAME")
SOC_PASSWORD = os.getenv("SOC_PASSWORD")
SOC_IP = os.getenv("SOC_IP")
PORT_BIND = int(os.getenv("PORT"))

ULTRA96_USERNAME = os.getenv("ULTRA96_USERNAME")
ULTRA96_PASSWORD = os.getenv("ULTRA96_PASSWORD")
ULTRA96_IP = os.getenv("ULTRA96_IP")

def tunnel_to_ultra96():
    # open tunnel to soc.comp.nus.edu.sg server
    tunnel_soc = sshtunnel.open_tunnel(
        ssh_address_or_host = (SOC_IP, 22),
        remote_bind_address = (ULTRA96_IP, 22),
        ssh_username = SOC_USERNAME,
        ssh_password = SOC_PASSWORD,
        block_on_close = False
        )
    tunnel_soc.start()
    
    print('Tunnel into SOC Server successful, at port: ' + str(tunnel_soc.local_bind_port))

    # open tunnel from soc.comp.nus.edu.sg server to ultra96
    tunnel_ultra96 = sshtunnel.open_tunnel(
        ssh_address_or_host = ('localhost', tunnel_soc.local_bind_port),
        # bind port from localhost to ultra96
        remote_bind_address=('localhost', PORT_BIND),
        ssh_username = ULTRA96_USERNAME,
        ssh_password = ULTRA96_PASSWORD,
        local_bind_address = ('localhost', PORT_BIND), #localhost to bind it to
        block_on_close = False
        )
    tunnel_ultra96.start()
    print('Tunnel into Ultra96 successful, local bind port: ' + str(tunnel_ultra96.local_bind_port))

tunnel_to_ultra96()