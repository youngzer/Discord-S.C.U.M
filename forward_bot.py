#!/usr/bin/env python3

import sys
import os

CUR_DIR = os.path.abspath(os.path.dirname(__file__))
#sys.path.append(os.path.abspath(CUR_DIR + "/../"))

from configparser import ConfigParser
from discum import *


SAFARI_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15"
ADMIN = ""
FORWARD_TASK = [{'from':"", 'to':""}, {'from':"", 'to':""}]

config = ConfigParser()
config.read(CUR_DIR + "/bot.cfg", encoding='UTF-8')

ADMIN = config['bot']['admin']

FORWARD_TASK[0]['from'] = config['bot']['from_id1']
FORWARD_TASK[0]['to']   = config['bot']['to_id1']
FORWARD_TASK[1]['from'] = config['bot']['from_id2']
FORWARD_TASK[1]['to']   = config['bot']['to_id2']

log_info("Forward Task: %s -> %s" % (FORWARD_TASK[0]['from'], FORWARD_TASK[0]['to']))
log_info("Forward Task: %s -> %s" % (FORWARD_TASK[1]['from'], FORWARD_TASK[1]['to']))

bot = Client(email=config['bot']['account'], password=config['bot']['password'], user_agent=SAFARI_AGENT, debug = False)

def find_chnl_id(guild_name, chnl_name):
    global bot
    gids = bot.gateway.session.guilds
    for g in gids:
        if g['name'] == guild_name:
            for ch in g['channels']:
                if ch['type'] == 0 and ch['name'] == chnl_name:
                    return ch['id']
    return None

@bot.gateway.command
def recvMsg(resp):
    global FORWARD_TASK

    #ready_supplemental is sent after ready
    if resp['t'] == "READY_SUPPLEMENTAL":
        #log_debug("guilds: %s" % bot.gateway.session.guilds)
        user = bot.gateway.session.user
        log_info("Logged in as {}#{}".format(user['username'], user['discriminator']))
    if resp['t'] == "MESSAGE_CREATE":
        m = resp['d']
        guildID = m['guild_id'] if 'guild_id' in m else None #because DMs are technically channels too
        channelID = m['channel_id']
        username = m['author']['username']
        discriminator = m['author']['discriminator']
        content = m['content']
        log_info("> guild {} channel {} | {}#{}: {}".format(guildID, channelID, username, discriminator, content))

        if not content:
            return

        if guildID is None and ADMIN == username:
            #from 1 XXX xxx
            if not content.startswith('#'):
                return
            ct = content.split(" ", 2)
            if "#from" in content:
                tid = int(ct[1])
                ch = find_chnl_id(ct[2], ct[3])
                if ch and FORWARD_TASK[tid - 1]:
                    FORWARD_TASK[tid - 1]['from'] = ch
                    bot.sendMessage(channelID, "set FROM({}) channel: {}".format(tid, FORWARD_TASK[tid - 1]['from']))
                    print("set FROM channel: %s" % FORWARD_TASK[tid - 1]['from'])
            if "#to" in content:
                tid = int(ct[1])
                ch = find_chnl_id(ct[2], ct[3])
                if ch and FORWARD_TASK[tid - 1]:
                    FORWARD_TASK[tid - 1]['to'] = ch
                    bot.sendMessage(channelID, "set TO({}) channel: {}".format(tid, FORWARD_TASK[tid - 1]['to']))
                    print("set TO channel: %s" % FORWARD_TASK[tid - 1]['to'])
            if "#ding" in content:
                bot.sendMessage(channelID, "dong")

        for tsk in FORWARD_TASK:
            if channelID == tsk['from']:
                bot.sendMessage(tsk['to'], "[{}]\n{}\n{}".format(username, content, '-' * 40))


bot.gateway.run()

