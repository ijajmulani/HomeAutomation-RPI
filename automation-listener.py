from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNOperationType, PNStatusCategory
import logging
import json
import RPi.GPIO as GPIO

logging.basicConfig()

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
chan_list = [9, 10, 11, 17, 22 , 23, 24, 27]
GPIO.setup(chan_list, GPIO.OUT)

pnconfig = PNConfiguration()
pnconfig.subscribe_key = "sub-c-abbae878-e7e5-11e6-81cc-0619f8945a4f"
pnconfig.publish_key = "pub-c-fd75bdb3-a6bb-4110-a1e4-947620adf37d"
pubnub = PubNub(pnconfig)

def my_publish_callback(envelope, status):
    # Check whether request successfully completed or not
    if not status.is_error():
        # Message successfully published to specified channel.
        print ("Message uploaded !")
    else:
        # Handle message publish error. Check 'category' property to find out possible issue
        # because of which request did fail.
        # Request can be resent using: [status retry];
        print ("Error : Message not uploaded !")

class MySubscribeCallback(SubscribeCallback):
    def status(self, pubnub, status):
        # The status object returned is always related to subscribe but could contain
        # information about subscribe, heartbeat, or errors
        # use the operationType to switch on different options
        if status.operation == PNOperationType.PNSubscribeOperation:
            if status.category == PNStatusCategory.PNConnectedCategory:
                print ("Connected")
                # This is expected for a subscribe, this means there is no error or issue whatsoever
                # pubnub.publish().channel("automation").message("hello!!").async(my_publish_callback)
            elif status.category == PNStatusCategory.PNReconnectedCategory:
                pass
                # This usually occurs if subscribe temporarily fails but reconnects. This means
                # there was an error but there is no longer any issue
            elif status.category == PNStatusCategory.PNDisconnectedCategory:
                # This is the expected category for an unsubscribe. This means there
                # was no error in unsubscribing from everything
                print ("Reconnecting...")
                pubnub.reconnect()
            elif status.category == PNStatusCategory.PNUnexpectedDisconnectCategory:
                # This is usually an issue with the internet connection, this is an error, handle
                # appropriately retry will be called automatically
                print ("Reconnecting...")
                pubnub.reconnect()
            elif status.category == PNStatusCategory.PNAccessDeniedCategory:
                # This means that PAM does allow this client to subscribe to this
                # channel and channel group configuration. This is another explicit error
                print ("Access Deined")
            else:
                # This is usually an issue with the internet connection, this is an error, handle appropriately
                # retry will be called automatically
                print ("Internet error")
        else:
            # Encountered unknown status type
            print ("Unknown status error")

    def presence(self, pubnub, presence):
        pass  # handle incoming presence data

    def message(self, pubnub, message):
        # handle incoming messages
        parsed = message.message
        print (parsed)
        if 'operation' in parsed and parsed['operation'] == 'get_status':
            state_array = {}
            for pin in chan_list:
                state_array[pin] = GPIO.input(pin)
            pubnub.publish().channel("automation").message({'sender_id' : 'pi', 'type' : 'status',
                'state' : state_array}).async(my_publish_callback)
        elif 'pin_number' in parsed:
            pinNumber = parsed['pin_number']
            state = parsed['state']
            if (pinNumber in chan_list):
                GPIO.output(pinNumber, state)
                state_array = {}
                for pin in chan_list:
                    state_array[pin] = GPIO.input(pin)
                pubnub.publish().channel("automation").message({'sender_id' : 'pi', 'type' : 'status',
                'state' : state_array}).async(my_publish_callback)
            else:
                print("Wrong Pin")
                #print("Channnel  %d  is not set for output", pinNumber)
            

pubnub.add_listener(MySubscribeCallback())
pubnub.subscribe().channels('automation').execute()
