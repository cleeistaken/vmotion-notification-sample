from subprocess import Popen, PIPE
import shlex
from time import sleep
import json


def RunRPC(rpcName, paramdict):
   try:
      from shlex import quote
   except ImportError:
      from pipes import quote

   # handle none param dict
   param = ""
   if paramdict != None:
      param = json.dumps(paramdict)
   cmd = "vmtoolsd --cmd "
   cmd += quote(rpcName + " " + param)

   print("Running cmd : %s" % cmd)

   output = Popen(shlex.split(cmd), stdout=PIPE)
   stdout = output.communicate()
   reply = json.loads(stdout[0])
   assert(reply["result"] == True)
   return reply


def RegisterForNotification():
   params = {"appName": "demo", "notificationTypes": ["sla-miss"]}
   rpcName = "vm-operation-notification.register"
   reply = RunRPC(rpcName, params)
   print("\n Token returned on registration: %s \n" % reply["uniqueToken"])
   return reply["uniqueToken"]


def UnregisterForNotification(token):
   params = {"uniqueToken": token}
   rpcName = "vm-operation-notification.unregister"
   RunRPC(rpcName, params)
   print("\n Unregistered \n")


def AckEvent(token, opId):
   params = {"uniqueToken": token, "operationId": opId}
   rpcName = "vm-operation-notification.ack-event"
   print("\n Acknowledging notification \n")
   reply = RunRPC(rpcName, params)


def CheckForEvents(token):
   checkForEvent = True
   params = {"uniqueToken": token}
   rpcName = "vm-operation-notification.check-for-event"

   while checkForEvent:
      reply = RunRPC(rpcName, params)
      eventType = reply.get("eventType", None)

      if eventType == "start":
         opId = reply["operationId"]
         print("\n vMotion start notification for migration id %s \n" % opId)

         notificationTimeout = reply["notificationTimeoutInSec"]
         print("\n Notification timeout: %d seconds \n" % notificationTimeout)

         # Simulate preparing for operation
         if notificationTimeout > 2:
            waitTime = notificationTimeout - 2
         else:
            waitTime = 0
         print("\n App preparing for vMotion for %d seconds \n" % waitTime)
         sleep(waitTime)

         # Ack start event
         AckEvent(token, opId)

      elif eventType == "timeout-change":
         opId = reply["operationId"]
         print("\n Notification timeout change event received \n")

         newNotificationTimeout = reply["newNotificationTimeoutInSec"]
         print("\n New notification timeout: %d seconds \n" % newNotificationTimeout)

         AckEvent(token, opId)

      elif eventType == "end":
         opId = reply["operationId"]
         print("\n vMotion end notification for migration id %s \n" % opId)

         #checkForEvent = False

      # poll interval
      sleep(1)


def main():
   # Register for notification
   token = RegisterForNotification()

   # Check for vmotion events
   try:
      CheckForEvents(token)
   except:
      UnregisterForNotification(token)

   # Unregister
   #UnregisterForNotification(token)


if __name__ == "__main__":
    main()

