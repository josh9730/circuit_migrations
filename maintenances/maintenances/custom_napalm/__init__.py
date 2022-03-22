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
