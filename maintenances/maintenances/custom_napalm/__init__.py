textfsm_optics = r"""Value Port (\D+\d+\/\d+\/(\d+|CPU\d)\/\d+)
Value Optic (\S+)
Value Serial (\S+)

Start
  ^.*NAME: "${Port}",
  ^.*PID: ${Optic}\s.*SN: ${Serial}
  ^-- -> Record
"""
