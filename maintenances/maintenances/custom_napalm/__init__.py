textfsm_optics = r"""Value Port (\D+\d+\/\d+\/(\d+|CPU\d)\/\d+)
Value Optic (\S+)
Value Serial (\S+)

Start
  ^.*NAME: "${Port}",
  ^.*PID: ${Optic}\s.*SN: ${Serial}
  ^-- -> Record
"""

textfsm_nd = r"""Value Neighbor (\d\S+)
Value MAC (\S+)
Value Port (\S+)

Start
  ^${Neighbor}\s+\d+\s+${MAC}\s+\S+\s+${Port}\s+\S+ -> Record
"""

textfsm_bgp_rx = r"""Value Route ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\/[0-9]{1,2})

Start
  ^\D{1,3}${Route} -> Record
"""
