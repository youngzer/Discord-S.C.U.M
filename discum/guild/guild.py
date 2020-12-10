import requests
import json
from ..Logger import *

if __import__('sys').version.split(' ')[0] < '3.0.0':
    from urllib import quote
else:
    from urllib.parse import quote

class Guild(object):
	def __init__(self, discord, s): #s is the requests session object
		self.discord = discord
		self.s = s
		

	'''
	invite codes / server info
	'''
	#get guild info from invite code
	def getInfoFromInviteCode(self,inviteCode):
		url = self.discord+"invites/"+inviteCode+"?with_counts=true"
		log_info('Get -> {}'.format(url))
		response = self.s.get(url)
		log_info('Response <- {}'.format(response.text))
		return response

	#join guild with invite code
	def joinGuild(self,inviteCode):
		url = self.discord+"invites/"+inviteCode
		log_info('Post -> {}'.format(url))
		response = self.s.get(url)
		log_info('Response <- {}'.format(response.text))
		return response

	'''
	server moderation
	'''
	#kick a user
	def kick(self,guildID,userID,reason):
		url = self.discord+"guilds/%s/members/%s?reason=%s" % (guildID, userID, quote(reason))
		log_info('Delete -> {}'.format(url))
		response = self.s.delete(url)
		log_info('Response <- {}'.format(response.text))
		return response

	#ban a user
	def ban(self,guildID,userID,deleteMessagesDays,reason):
		url = self.discord+"guilds/%s/bans/%s" % (guildID, userID)
		body = {"delete_message_days": str(deleteMessagesDays), "reason": reason}
		log_info('Put -> {}'.format(url))
		log_info('{}'.format(str(body)))
		response = self.s.put(url, data=json.dumps(body))
		log_info('Response <- {}'.format(response.text))
		return response

	#lookup a user in a guild. thx Echocage for finding this api endpoint
	'''Note, user clients do not run this api request, however it currently works without a problem. 
	Once discum's gatewayserver is improved, we'll add the actual api to discum (to best mimic the web client)
	'''
	def getGuildMember(self, guildID, userID):
		url = self.discord+"/guilds/%s/members/%s" % (guildID, userID)
		log_info('Get -> {}'.format(url))
		response = self.s.get(url)
		log_info('Response <- {}'.format(response.text))
		return response