"""
Threaded Python TCP Ping Test (defaults to port 80, 3 packets)
Usage: ./tcpping.py host [port] [maxcount]
- Ctrl-C Exits
Derived from
  Jonathan Yantis, Blade.            https://github.com/yantisj/tcpping/blob/master/tcpping.py
  Andrey Belykh, Dundas Software.    https://stackoverflow.com/questions/48009669/using-for-python-tcp-ping-time-measure-difference-from-other-tools
TODO:
   review and/or incorporate Jim Willie, Akamai Technologies.  https://github.com/jwyllie83/tcpping
"""

import sys
import os
import errno
import socket
import time
import datetime
import signal
from timeit import default_timer as timer
import threading
import click

def signal_handler(signal, frame):
    """ Catch Ctrl-C and Exit """
    sys.exit(0)


@click.command()
@click.option("--host"       , default="",              help="host")
@click.option("--port"       , default=80,                help="tcp port")
@click.option("--maxcount"   , default=3,                 help="# of samples")
@click.option("--intergreen" , default=0,                 help="wait time (sec)")
@click.option("--proto"      , default=6,                 help="protocol number (TCP=6)")
def tcpping(host,port,maxcount,intergreen,proto):
    """
    A 'quick and dirty' tcp ping client
    """

    #https://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml
    #https://tools.ietf.org/html/rfc793


    # Pass/Fail counters
    passed = 0
    failed = 0
    count  = 0
    
    # Register SIGINT Handler
    signal.signal(signal.SIGINT, signal_handler)

    # Loop while less than max count or until Ctrl-C caught
    while count < maxcount:

        # Increment Counter
        count += 1
        success = False

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 1sec Timeout
        # todo consider making timeout a parameter
        s.settimeout(1)

        # Try to Connect
        try:
            t = threading.Thread(target=s.connect((host, int(port))))
            s_start = timer()
            t.start()     #do thread
            t.join(timeout=1)
            s_stop = timer()
            s.shutdown(socket.SHUT_RD)
            success = True
            s.close()

            if t.is_alive():
                t.join()  #wait for thread to return

        # todo consider switching to json
        except socket.timeout as e:
            s.close()
            print("Connection timed out!\n", file=sys.stderr)
            print("%s,%s,%s,%s,%s,%s" % (host, port, proto, (count-1), datetime.datetime.now(), 9999))
            failed += 1
        except socket.gaierror as estr:
            #https://docs.python.org/3/library/socket.html#socket.socket.connect
            s.close()
            print(str(estr), file=sys.stderr)
            print("\n",file=sys.stderr)
            print("%s,%s,%s,%s,%s,%s" % (host, port, proto, (count-1), datetime.datetime.now(),9999))
            failed += 1
        except socket.error as e:
            #https://docs.python.org/2/library/errno.html
            s.close()
            print("Socket Error!\n", file=sys.stderr)
            print("%s,%s,%s,%s,%s,%s" % (host, port, proto, (count-1), datetime.datetime.now(),9999))
            failed += 1
            if e.errno == errno.ECONNREFUSED or e.errno==errno.EHOSTUNREACH:
                print(os.strerror(e.errno), file=sys.stderr)
                print("", file=sys.stderr)
            else:
                raise
        except OSError as e:
            s.close()
            print("OS Error:\n", file=sys.stderr)
            print(os.strerror(e.errno), file=sys.stderr)
            print("%s,%s,%s,%s,%s,%s" % (host, port, proto, (count-1), datetime.datetime.now(),9999))
            failed += 1

        if success:
            s_runtime = "%.3f" % (1000 * (s_stop - s_start))
            print("%s,%s,%s,%s,%s,%s" % (host, port, proto, (count-1), datetime.datetime.now(), s_runtime))
            passed += 1

        # intergreen rest
        if count < maxcount:
            time.sleep(intergreen)
            #print("sleep %s" % intergreen)

    #return failure count
    sys.exit(failed)

if __name__ == "__main__":
    tcpping()
