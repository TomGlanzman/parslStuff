####################################################################################
###  CUSTOM EXCEPTION
####################################################################################


class ckptAction(Exception):
   """A dummy exception that is used for training

   Contains:
   reason(string)
   severity(int)
   """

   def __init__(self,reason,severity):
      self.reason = reason
      self.severity = severity

   
   pass
   
