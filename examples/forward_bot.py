#!/usr/bin/env python3

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from discum import *

SAFARI_AGENT     = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.1 Safari/605.1.15"

DISCORD_ACCOUNT  = os.environ['ACCOUNT']
DISCORD_PASSWORD = os.environ['PASSWORD']

FORWARD_TASK = [{
                    'from': os.environ['FROM_ID1'],
                    'to': os.environ['TO_ID1']
                }, {
                    'from': os.environ['FROM_ID2'],
                    'to': os.environ['TO_ID2']
                }]
ADMIN = os.environ['ADMIN']

log_debug("FORWARD_TASK: %s" % FORWARD_TASK)

bot = Client(email=DISCORD_ACCOUNT, password=DISCORD_PASSWORD, user_agent=SAFARI_AGENT,log = True)

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
        log_debug("guilds: %s" % bot.gateway.session.guilds)
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

        if channelID == FORWARD_TASK[0]['from']:
            bot.sendMessage(FORWARD_TASK[0]['to'], "[{}]\n{}".format(username, content))
        if channelID == FORWARD_TASK[1]['from']:
            bot.sendMessage(FORWARD_TASK[1]['to'], "[{}]\n{}".format(username, content))

bot.gateway.run()
