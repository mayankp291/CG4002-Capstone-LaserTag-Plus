# from sshtunnel import open_tunnel

# def ssh_tunnel():
#     tunnel = open_tunnel(
#         ('stu.comp.nus.edu.sg', 22),
#         ssh_username="mayankp",
#         ssh_password="Sanchit@012345",
#         remote_bind_address=("localhost",22),
#         block_on_close=False
#     )
#     tunnel.start()
#     print("SUCCESS")

#     tunnel_u96 = open_tunnel(
#         ssh_address_or_host=('192.168.95.235', tunnel.local_bind_port),
#         remote_bind_address=('192.168.95.235', 22),
#         ssh_username="xilinx",
#         ssh_password="plsdonthackus",
#         local_bind_address=('192.168.95.235', 22),
#         block_on_close=False
#     )

#     tunnel_u96.start()
#     print(tunnel_u96.local_bind_port)
#     print("SUCCESS")

# ssh_tunnel()

# import sshtunnel
# from paramiko import SSHClient

# with sshtunnel.open_tunnel(
#     ssh_address_or_host=('stu.comp.nus.edu.sg', 22),
#     remote_bind_address=('192.168.95.219', 22),
# ) as tunnel1:
#     print('Connection to tunnel1 (GW1_ip:GW1_port) OK...')
#     with sshtunnel.open_tunnel(
#         ssh_address_or_host=('localhost', tunnel1.local_bind_port),
#         remote_bind_address=('192.168.95.235', 22),
#         ssh_username='mayankp',
#         ssh_password='Sanchit@012345',
#     ) as tunnel2:
#         print('Connection to tunnel2 (GW2_ip:GW2_port) OK...')
#         with SSHClient() as ssh:
#             ssh.connect('localhost',
#                 port=tunnel2.local_bind_port,
#                 username='xilinx',
#                 password='plsdonthackus',
#             )
#             ssh.exec_command(...)


# import paramiko
# import sshtunnel

# with sshtunnel.open_tunnel(
#     ('stu.comp.nus.edu.sg', 22),
#     ssh_username="mayankp",
#     ssh_pkey="/var/ssh/rsa_key",
#     ssh_private_key_password="Sanchit@012345",
#     remote_bind_address=('192.168.95.219', 22),
#     local_bind_address=('0.0.0.0', 10022)
# ) as tunnel:
#     client = paramiko.SSHClient()
#     client.load_system_host_keys()
#     client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#     client.connect('127.0.0.1', 10022)
#     # do some operations with client session
#     client.close()

# print('FINISH!')



# from sshtunnel import SSHTunnelForwarder

# server = SSHTunnelForwarder(
#     'stu.comp.nus.edu.sg',
#     ssh_username="mayankp",
#     ssh_password="Sanchit@012345",
#     remote_bind_address=('127.0.0.1', 8080)
# )

# server.start()

# print(server.local_bind_port)  # show assigned local port
# # work with `SECRET SERVICE` through `server.local_bind_port`.

# server.stop()