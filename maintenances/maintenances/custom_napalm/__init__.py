textfsm_optics = r"""Value Port (\d+\/\d+\/(\d+|CPU\d)\/\d+)
Value Optic (\S+)
Value Serial (\S+)

Start
  ^.*NAME: "\D+${Port}",
  ^.*PID: ${Optic}\s.*SN: ${Serial}
  ^-- -> Record
"""
