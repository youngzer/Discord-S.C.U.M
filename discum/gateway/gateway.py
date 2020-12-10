import websocket
import json
import time
import random
import base64

if __import__('sys').version.split(' ')[0] < '3.0.0':
    import thread
else:
    import _thread as thread

from .session import session
from ..Logger import *

class GatewayServer:

    class LogLevel:
        SEND = '\033[94m'
        RECEIVE = '\033[92m'
        WARNING = '\033[93m'
        DEFAULT = '\033[m'

    class OPCODE: #https://discordapp.com/developers/docs/topics/opcodes-and-status-codes
        # Name                  Code    Client Action   Description
        DISPATCH =              0  #    Receive         dispatches an event
        HEARTBEAT =             1  #    Send/Receive    used for ping checking
        IDENTIFY =              2  #    Send            used for client handshake
        STATUS_UPDATE =         3  #    Send            used to update the client status
        VOICE_UPDATE =          4  #    Send            used to join/move/leave voice channels
        #                       5  #    ???             ???
        RESUME =                6  #    Send            used to resume a closed connection
        RECONNECT =             7  #    Receive         used to tell clients to reconnect to the gateway
        REQUEST_GUILD_MEMBERS = 8  #    Send            used to request guild members
        INVALID_SESSION =       9  #    Receive         used to notify client they have an invalid session id
        HELLO =                 10 #    Receive         sent immediately after connecting, contains heartbeat and server debug information
        HEARTBEAT_ACK =         11 #    Sent immediately following a client heartbeat that was received
        GUILD_SYNC =            12 #

    def __init__(self, websocketurl, token, ua_data, proxy_host=None, proxy_port=None):
        self.token = token
        self.ua_data = ua_data
        self.auth = {
                "token": self.token,
                "capabilities": 61,
                "properties": {
                    "os": self.ua_data["os"],
                    "browser": self.ua_data["browser"],
                    "device": self.ua_data["device"],
                    "browser_user_agent": self.ua_data["browser_user_agent"],
                    "browser_version": self.ua_data["browser_version"],
                    "os_version": self.ua_data["os_version"],
                    "referrer": "",
                    "referring_domain": "",
                    "referrer_current": "",
                    "referring_domain_current": "",
                    "release_channel": "stable",
                    "client_build_number": 72814,
                    "client_event_source": None
                },
                "presence": {
                    "status": "online",
                    "since": 0,
                    "activities": [],
                    "afk": False
                },
                "compress": False,
                "client_state": {
                    "guild_hashes": {},
                    "highest_last_message_id": "0",
                    "read_state_version": 0,
                    "user_guild_settings_version": -1
                }
            }
        if 'build_num' in self.ua_data and self.ua_data['build_num']!=72814:
            self.auth['properties']['client_build_number'] = self.ua_data['build_num']

        self.proxy_host = None if proxy_host in (None,False) else proxy_host
        self.proxy_port = None if proxy_port in (None,False) else proxy_port

        self.interval = None
        self.session_id = None
        self.sequence = 0
        self.READY = False #becomes True once READY_SUPPLEMENTAL is received
        self.settings_ready = {}
        self.settings_ready_supp = {}

        #websocket.enableTrace(True)
        self.ws = self._get_ws_app(websocketurl)

        self._after_message_hooks = []
        self._last_err = None

        self.connected = False
        self.resumable = False

        self.voice_data = {} #voice connections dependent on current (connected) session

    #WebSocketApp, more info here: https://github.com/websocket-client/websocket-client/blob/master/websocket/_app.py#L79
    def _get_ws_app(self, websocketurl):
        sec_websocket_key = base64.b64encode(bytes(random.getrandbits(8) for _ in range(16))).decode() #https://websockets.readthedocs.io/en/stable/_modules/websockets/handshake.html
        headers = {
            "Host": "gateway.discord.gg",
            "Connection": "Upgrade",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "User-Agent": self.ua_data["browser_user_agent"],
            "Upgrade": "websocket",
            "Origin": "https://discord.com",
            "Sec-WebSocket-Version": "13",
            "Accept-Language": "en-US",
            "Sec-WebSocket-Key": sec_websocket_key
        } #more info: https://stackoverflow.com/a/40675547

        #ws_log = logging.StreamHandler()
        #formatter = logging.Formatter(
        #    '%(asctime)s %(levelname)s %(funcName)s: %(message)s',
        #    datefmt='%Y-%m-%d %H:%M:%S'
        #)
        #ws_log.setFormatter(formatter)
        #websocket.enableTrace(True, handler = ws_log)

        ws = websocket.WebSocketApp(websocketurl,
                                    header = headers,
                                    on_open    = lambda ws: self.on_open(ws),
                                    on_message = lambda ws, msg: self.on_message(ws, msg),
                                    on_error   = lambda ws, msg: self.on_error(ws, msg),
                                    on_close   = self.on_close)
        return ws

    def on_open(self, ws):
        self.connected = True
        log_info("Connected to websocket.")
        if self.resumable:
            self.resumable = False
            self.send({"op": self.OPCODE.RESUME, "d": {"token": self.token, "session_id": self.session_id, "seq": self.sequence-1 if self.sequence>0 else self.sequence}})
        else:
            self.send({"op": self.OPCODE.IDENTIFY, "d": self.auth})

    def on_message(self, ws, message):
        self.sequence += 1
        resp = json.loads(message)
        log_info("< t: {}, session: {}, op: {}".format(resp['t'], resp['s'], resp['op']))
        if resp['op'] == self.OPCODE.HELLO: #only happens once, first message sent to client
            self.interval = (resp["d"]["heartbeat_interval"]-2000)/1000
            thread.start_new_thread(self._heartbeat, ())
        elif resp['op'] == self.OPCODE.INVALID_SESSION:
            log_info("Invalid session.")
            self.sequence = 0
            self.close()
            if self.resumable:
                self.resumable = False
        if self.interval == None:
            log_info("Identify failed.")
            self.close()
        if resp['t'] == "READY":
            self.session_id = resp['d']['session_id']
            self.settings_ready = resp['d']
        elif resp['t'] == "READY_SUPPLEMENTAL":
            self.resumable = True #completely successful identify
            self.settings_ready_supp = resp['d']
            self.session = session(self.settings_ready, self.settings_ready_supp)
            self.READY = True
        thread.start_new_thread(self._response_loop, (resp,))

    def on_error(self, ws, error):
        log_warning('%s' % error)
        self._last_err = error

    def on_close(self, ws, close_args):
        self.connected = False
        self.READY = False #reset self.READY
        log_info('websocket closed: %s' % close_args)

    #Discord needs heartbeats, or else connection will sever
    def _heartbeat(self):
        log_info("entering heartbeat")
        while self.connected:
            time.sleep(self.interval)
            if not self.connected:
                break
            self.send({"op": self.OPCODE.HEARTBEAT,"d": self.sequence-1 if self.sequence>0 else self.sequence})

    #just a wrapper for ws.send
    def send(self, payload):
        log_info('> %s' % payload)
        self.ws.send(json.dumps(payload))

    def close(self):
        self.connected = False
        self.READY = False #reset self.READY
        log_info('websocket closed') #sometimes this message will print twice. Don't worry, that's not an error.
        self.ws.close()


    #the next 2 functions come from https://github.com/scrubjay55/Reddit_ChatBot_Python/blob/master/Reddit_ChatBot_Python/Utils/WebSockClient.py (Apache License 2.0)
    def command(self, func):
        self._after_message_hooks.append(func)
        return func

    def _response_loop(self, resp):
        for func in self._after_message_hooks:
            if func:
                func(resp)

    def removeCommand(self, func):
        try:
            self._after_message_hooks.remove(func)
        except ValueError:
            log_info('%s not found in _after_message_hooks.' % func)            

    def clearCommands(self):
        self._after_message_hooks = []

    def resetSession(self): #just resets some variables that in-turn, resets the session (client side). Do not run this while running run().
        self.interval = None
        self.session_id = None
        self.sequence = 0
        self.READY = False #becomes True once READY_SUPPLEMENTAL is received
        self.settings_ready = {}
        self.settings_ready_supp = {}
        self._last_err = None
        self.voice_data = {}
        self.resumable = False #you can't resume anyways without session_id and sequence

    #modified version of function run_4ever from https://github.com/scrubjay55/Reddit_ChatBot_Python/blob/master/Reddit_ChatBot_Python/Utils/WebSockClient.py (Apache License 2.0)
    def run(self):
        while True:
            self.ws.run_forever(ping_interval=5, ping_timeout=2, http_proxy_host=self.proxy_host, http_proxy_port=self.proxy_port)
            self.close()
            self.resumable = False
            self.sequence = 0
            log_warning("WebSocket run error, Retrying in 10 seconds.")
            time.sleep(random.randrange(3, 10))




