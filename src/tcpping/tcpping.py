"""
Threaded Python TCP Ping Test (defaults to port 80, 3 packets)
Usage: ./tcpping.py -h host [-p port] [-s nsamples] [-t timeout] [-i intergreen]
- Ctrl-C Exits
Purpose:
    Measure socket.connect() latency.
    Measure the 3 way tcp handshake [client FoR] to first application gateway.
    Measure ACK SYN/ACK latency to first appliation gateway.


Based on:
  Jonathan Yantis, Blade.         
  https://github.com/yantisj/tcpping/blob/master/tcpping.py
  Andrey Belykh, Dundas Software. 
  https://stackoverflow.com/questions/48009669/using-for-python-tcp-ping-time-measure-difference-from-other-tools
TODO:
   Consider reviewing Willie, Akamai Technologies.  https://github.com/jwyllie83/tcpping
   Consider the pros and cons of threads vs multiprocessing
"""

import sys
import os
import errno
import socket
import time
import datetime
import json
import signal
from timeit import default_timer as timer
import threading
import isodate
import click

def signal_handler(signum, frame):
    """ Catch Ctrl-C and Exit """
    now = datetime.datetime.now().isoformat()
    name = signal.Signals(signum).name
    line = {'program':os.path.basename(sys.argv[0]),'signal':str(signum), 'msg':name, 'time':now}
    print(json.dumps(line),file=sys.stderr)
    sys.exit(0)


def real_tcpping(host,port,nsamples,intergreen,timeout):
    """
    A 'quick and dirty' tcp ping client
    Measures socket.connect()
    Measures the 3 way tcp handshake [client FoR]
    Measures ACK SYN/ACK latency.
    """

    #todo consider switching to ip ping
    #https://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml
    #https://tools.ietf.org/html/rfc793


    # Pass/Fail counters
    passed = 0
    failed = 0
    count  = 0

    # Register SIGINT Handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Loop while less than nsamples or until Ctrl-C caught
    while count < nsamples:

        # Increment Counter
        count += 1
        success = False

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

            s.settimeout(timeout)
            #s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 0)
            #s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 0)

            # Try to Connect
            try:
                #wait for connection or raise a TimeoutError
                t = threading.Thread(target=s.connect((host, int(port))))

                s_start = timer()                      #start timer
                t.start()                              #do thread

                t.join(timeout=timeout)                # wait until the thread terminates
                s_stop = timer()
                s.shutdown(socket.SHUT_RD)
                success = True

                if t.is_alive():
                    t.join()                           #wait for thread to return

            except socket.timeout as e:
                now = datetime.datetime.now().isoformat()
                msg = type(e).__name__
                line = {'program':os.path.basename(sys.argv[0]),'errno':e.errno, 'error':str(e),'msg':msg , 'host':host, 'port':port, 'count':count-1, 'time':now}
                print(json.dumps(line),file=sys.stderr)
                failed += 1
            except socket.gaierror as e:
                #https://docs.python.org/3/library/socket.html#socket.socket.connect
                now = datetime.datetime.now().isoformat()
                msg = type(e).__name__
                line = {'programn':os.path.basename(sys.argv[0]),'errno':e.errno, 'error':str(e),'msg':msg , 'host':host, 'port':port, 'count':count-1, 'time':now}
                print(json.dumps(line),file=sys.stderr)
                failed += 1
            except socket.error as e:
                #https://docs.python.org/2/library/errno.html
                now = datetime.datetime.now().isoformat()
                failed += 1
                msg = type(e).__name__
                if e.errno in (errno.ECONNREFUSED, errno.EHOSTUNREACH):
                    line = {'program':os.path.basename(sys.argv[0]),'errno':e.errno, 'error':str(e),'msg':msg, 'host':host, 'port':port, 'count':count-1, 'time':now}
                    print(json.dumps(line),file=sys.stderr)
                else:
                    line = {'program':os.path.basename(sys.argv[0]),'errno':e.errno,'error':str(e),'msg':msg, 'host':host, 'port':port, 'count':count-1, 'time':now}
                    print(json.dumps(line),file=sys.stderr)
                    raise
            except OSError as e:
                now = datetime.datetime.now().isoformat()
                msg = type(e).__name__
                line = {'program':os.path.basename(sys.argv[0]),'errno':e.errno, 'error':str(e),'msg':msg, 'host':host, 'port':port, 'count':count-1, 'time':now}
                print(json.dumps(line),file=sys.stderr)
                failed += 1

        if success:
            s_runtime = isodate.duration_isoformat(datetime.timedelta(seconds=s_stop - s_start))
            #s_runtime = f"{ms_rt:.3f}"
            now = datetime.datetime.now().isoformat()
            # Assume copper conductor is 80% efficient
            # max reach = 80 [% -  cu wire efficiency]* 299792458 [m/s - Resolution 1, 17th CGPM, 1983 / Giacomo P. IEEE Trans on Instr and Mea. 1985;IM-34:116] * time [round-trip] / 2 [trip]/[round-trip]

            max_reach_cu =  0.8*299792458*(s_stop-s_start)/2   # max copper reach in meters
            line = {'host':host, 'port':port, 'count':count-1, 'time':now, 'elapsed':s_runtime, 'est_max_reach_cu':f"{max_reach_cu:.2g}"} # estimate max reach to 2 sig figs
            print(json.dumps(line))
            passed += 1

        # intergreen rest
        if count < nsamples:
            time.sleep(intergreen)
            #print("sleep %s" % intergreen)

    #return failure count
    sys.exit(failed)

@click.command()
@click.option("-h","--host"       , default="google.com",      help="target host")
@click.option("-p","--port"       , default=443,                help="tcp port")
@click.option("-s","--nsamples"   , default=3,                 help="# of samples to attempt")
@click.option("-i","--intergreen" , default=0,                 help="wait time (sec)")
@click.option("-t","--timeout"    , default=1,                 help="socket timeout (sec)")
def tcpping(host,port,nsamples,intergreen,timeout):
    """
    UI routine 
    """
    real_tcpping(host,port,nsamples,intergreen,timeout)

if __name__ == "__main__":
    tcpping()
