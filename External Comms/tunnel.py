from sshtunnel import open_tunnel

def ssh_tunnel():
    tunnel = open_tunnel(
        ('stu.comp.nus.edu.sg', 22),
        ssh_username="mayankp",
        ssh_password="Sanchit@012345",
        remote_bind_address=("localhost",22),
        block_on_close=False
    )
    tunnel.start()
    print("SUCCESS")

    tunnel_u96 = open_tunnel(
        ssh_address_or_host=('192.168.95.235', tunnel.local_bind_port),
        remote_bind_address=('192.168.95.235', 22),
        ssh_username="xilinx",
        ssh_password="plsdonthackus",
        local_bind_address=('192.168.95.235', 22),
        block_on_close=False
    )

    tunnel_u96.start()
    print(tunnel_u96.local_bind_port)
    print("SUCCESS")

ssh_tunnel()