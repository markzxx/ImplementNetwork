import ICMP
from LinkLayer import util
local_ip = util.get_local_ipv4_address()
remote_ip = '10.20.117.131'
ICMP.request(local_ip, remote_ip)

