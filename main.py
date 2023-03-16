import discord
from discord_slash import SlashCommand
import discord_slash # Importing the newly installed library.
import os
from discord.ext import commands
#import keep_alive
import random
import requests
from bs4 import BeautifulSoup
import json
import asyncio


client = commands.Bot(command_prefix=[' '])
client.remove_command('help')
slash = SlashCommand(client, sync_commands=True) # Declares slash commands through the client.
token = os.environ.get('token')
guild_ids = [945418074121715782, 814607316107395093, 704482683857928222,961863482867847188, 962033686046466070]
roboteventskey = os.environ.get('robotevents_key')
def get_current_season():
	iq_seasons = 'https://www.robotevents.com/api/v2/seasons?program%5B%5D=41'
	headers = {"Authorization": f"Bearer {roboteventskey}"}
	seasondata = requests.get(iq_seasons, headers=headers).json()
	currentseasonid = seasondata['data'][1]['id']
	currentseasonname = seasondata['data'][1]['name']
	return currentseasonid, currentseasonname
	
currentseasonid, currentseasonname = get_current_season()

async def get_ranking(team):
	url = f'https://www.robotevents.com/teams/VIQC/{team.upper()}'
	res = requests.get(url)
	html_page = res.content
	soup = BeautifulSoup(html_page, 'html.parser')
	text = soup.find_all(text=True)
	
	output = ''
	blacklist = [
		'[document]',
		'noscript',
		'header',
		'html',
		'meta',
		'head', 
		'input',
		'script',
	]
	
	for t in text:
		if t.parent.name not in blacklist:
			output += '{} '.format(t)
	index = output.find("World Skills Rank:")
	rank = ''
	for x in range(0, 4):
		if output[index+21+x].isnumeric():
			rank+=output[index+21+x]
	return rank
@client.event
async def on_ready():
	print("Ready!")
	# channel = client.get_guild(945418074121715782).get_channel(992529252652158977)
	# e = await channel.create_webhook(name='counting').url
	# print(e)
	game = discord.Game("a skills run")
	await client.change_presence(activity=game)
 # Put your server ID in this array.
guild_ids = [945418074121715782, 814607316107395093, 704482683857928222,961863482867847188, 962033686046466070]
# This command is used to get the ranking of a VIQC team.

@slash.slash(name='skills', description='World Skills Rank')
async def skills(ctx, team):

	team = team.upper()
	await ctx.defer()
	rank = await get_ranking(team)
	teaminfo = f'https://www.robotevents.com/api/v2/teams?number={team}'
	headers = {"Authorization": f"Bearer {roboteventskey}"}
	teamdata = requests.get(teaminfo, headers=headers).json()

	try:
		for allteam in teamdata['data']:
			if allteam['program']['code'] == 'VIQC':
				id = allteam['id']
				teamname = allteam['team_name']
		teaminfo = f'https://www.robotevents.com/api/v2/teams/{id}/skills'
	except:
		await ctx.send(f"Sorry, we couldn't find team {team}.")
		return
		
	driverlist = []
	autonlist = []
	events = {}


	def eventdata(teaminfo, driverlist, autonlist, events):
		teamdata = requests.get(teaminfo, headers=headers).json()
		for event in teamdata['data']:
			if event['season']['id'] == currentseasonid:	
				if event['event']['name'] not in events:
					events[event['event']['name']] = {}
					events[event['event']['name']]['total'] = 0
					events[event['event']['name']]['driver'] = 0
					events[event['event']['name']]['auton'] = 0
				if event['type'] == 'driver':
					driverlist.append(event['score'])
					events[event['event']['name']]['total'] += event['score']
					events[event['event']['name']]['driver'] = event['score']
				elif event['type'] == 'programming':
					autonlist.append(event['score'])
					events[event['event']['name']]['total'] += event['score']	
					events[event['event']['name']]['auton'] = event['score']	
		if isinstance(teamdata['meta']['next_page_url'], str):
			teaminfo=teamdata['meta']['next_page_url']
			eventdata(teaminfo, driverlist, autonlist, events)
		return driverlist, autonlist, events

	eventdata(teaminfo, driverlist, autonlist, events)


	if driverlist:
		driverHigh = max(driverlist)
	else:
		driverHigh=0
	if autonlist:
		autonomousHigh = max(autonlist)
	else:
		autonomousHigh=0
	score = 0

	for total in events:
		if events[total]['total'] > score:
			score = events[total]['total']
			event = total
	try:
		autonomous = events[event]['auton']
	except:
		autonomous = 0
	try:
		driver = events[event]['driver']
	except:
		driver = 0 

	embed=discord.Embed(title="Current VIQC Event", url=f"https://www.vexrobotics.com/iq/competition/viqc-current-game", color=0x24c9ff)
	embed.set_author(name=f"VIQC {team} ({teamname})", url=f"https://www.robotevents.com/teams/VIQC/{team}")
	embed.add_field(name="Rank", value=rank, inline=True)
	embed.add_field(name="Score", value=score, inline=True)
	embed.add_field(name="Programming", value=autonomous, inline=True)
	embed.add_field(name="Driver", value=driver, inline=True)
	embed.add_field(name="Highest Programming", value=autonomousHigh, inline=True)
	embed.add_field(name="Highest Driver", value=driverHigh, inline=True)
	print(embed)
	try:
		await ctx.send(embed=embed)
	except:
		await ctx.send(f"Hmm, we couldn't fetch your skills rank. Check https://www.robotevents.com/robot-competitions/vex-iq-challenge/standings/skills to see if {team} ({teamname}) is on there.")

		
@slash.slash(name='about', description='Bot credits')
async def credits(ctx):
	await ctx.send('''Made by VIQC 84C in 2022:
<@!697535361315766322> 
<@!697913907528073296> 
<@!475315771086602241> 

Special thanks to makers of <@!329389228398215179>
				   
If you would like to add the slash commands to your server, click on my profile and press "Add to Server"!''',
	allowed_mentions=discord.AllowedMentions(
	users=False,		 # Whether to ping individual user @mentions
	everyone=False,	  # Whether to ping @everyone or @here mentions
	roles=False,		 # Whether to ping role @mentions
	replied_user=False,  # Whether to ping on replies to messages
), hidden = True)

# This command is used to get the awards of a VIQC team.

@slash.slash(name='awards', description='Specified Team\'s awards')
async def awards(ctx, team):

	team = team.upper()
	await ctx.defer()
	teaminfo = f'https://www.robotevents.com/api/v2/teams?number={team}'
	headers = {"Authorization": f"Bearer {roboteventskey}"}
	teamdata = requests.get(teaminfo, headers=headers).json()

	try:
		for allteam in teamdata['data']:
			if allteam['program']['code'] == 'VIQC':
				id = allteam['id']
				teamname = allteam['team_name']
		awardsUrl = f'https://www.robotevents.com/api/v2/teams/{id}/awards?season={currentseasonid}'
	except:
		await ctx.send(f"Sorry, we couldn't find team {team}.")
		return


	headers = {"Authorization": f"Bearer {roboteventskey}"}

	# Award Data Loop for Next Page

	awardsDict = {}
	def awardData(awardsUrl, awardsDict):
		
		teamAwards = requests.get(awardsUrl, headers=headers).json()
		print(awardsUrl)

		for event in teamAwards['data']:
			if event['event']['name'] not in awardsDict:
				awardsDict[event['event']['name']] = []
			awardsDict[event['event']['name']].append(event['title'])	
		if isinstance(teamAwards['meta']['next_page_url'], str):
			print('sus')
			awardsUrl=teamAwards['meta']['next_page_url']
			awardData(awardsUrl, awardsDict)	
		return awardsDict

	awardData(awardsUrl, awardsDict)
	orderedAwards = ''

	for event in awardsDict:
		orderedAwards+=f'\n\n**{event}**\n'
		for award in awardsDict[event]:
			orderedAwards+=f"{award}\n"

	if not orderedAwards:
		orderedAwards = "\n\nCouldn't find any awards this season!"

	await ctx.send(f"**{team.upper()} ({teamname})'s Awards**{orderedAwards}")

@slash.slash(name='compare', description="Compare two teams by skills ranking")
async def compare(ctx, team1, team2):

	team1 = team1.upper()
	team2 = team2.upper()
	await ctx.defer()
	rank1 = await get_ranking(team1)
	rank2 = await get_ranking(team2)
	team1info = f'https://www.robotevents.com/api/v2/teams?number={team1}'
	team2info = f'https://www.robotevents.com/api/v2/teams?number={team2}'
	headers = {"Authorization": f"Bearer {roboteventskey}"}
	team1data = requests.get(team1info, headers=headers).json()
	team2data = requests.get(team2info, headers=headers).json()

	try:
		for allteam in team1data['data']:
			if allteam['program']['code'] == 'VIQC':
				id1 = allteam['id']
				team1name = allteam['team_name']
		for allteam2 in team2data['data']:
			if allteam['program']['code'] == 'VIQC':
				id2 = allteam2['id']
				team2name = allteam2['team_name']
	except:
		await ctx.send(f"Sorry, we couldn't find a team specified.")
		return
		
	team1info = f'https://www.robotevents.com/api/v2/teams/{id1}/skills'
	driverlist1 = []
	autonlist1 = []
	events1 = {}
	team2info = f'https://www.robotevents.com/api/v2/teams/{id2}/skills'
	driverlist2 = []
	autonlist2 = []
	events2 = {}


	def eventdata(teaminfo, driverlist, autonlist, events):
		teamdata = requests.get(teaminfo, headers=headers).json()
		for event in teamdata['data']:
			if event['season']['id'] == currentseasonid:	
				if event['event']['name'] not in events:
					events[event['event']['name']] = {}
					events[event['event']['name']]['total'] = 0
					events[event['event']['name']]['driver'] = 0
					events[event['event']['name']]['auton'] = 0
				if event['type'] == 'driver':
					driverlist.append(event['score'])
					events[event['event']['name']]['total'] += event['score']
					events[event['event']['name']]['driver'] = event['score']
				elif event['type'] == 'programming':
					autonlist.append(event['score'])
					events[event['event']['name']]['total'] += event['score']	
					events[event['event']['name']]['auton'] = event['score']	
		if isinstance(teamdata['meta']['next_page_url'], str):
			teaminfo=teamdata['meta']['next_page_url']
			eventdata(teaminfo, driverlist, autonlist, events)
		return driverlist, autonlist, events

	eventdata(team1info, driverlist1, autonlist1, events1)
	eventdata(team2info, driverlist2, autonlist2, events2)


	if driverlist1:
		driverHigh1 = max(driverlist1)
	else:
		driverHigh1=0
	if autonlist1:
		autonomousHigh1 = max(autonlist1)
	else:
		autonomousHigh1=0
	score1 = 0

	for total in events1:
		if events1[total]['total'] > score1:
			score1 = events1[total]['total']
			event = total
	try:
		autonomous1 = events1[event]['auton']
	except:
		autonomous1 = 0
	try:
		driver1 = events1[event]['driver']
	except:
		driver1 = 0 
		
	if driverlist2:
		driverHigh2 = max(driverlist2)
	else:
		driverHigh2=0
	if autonlist2:
		autonomousHigh2 = max(autonlist2)
	else:
		autonomousHigh2=0
	score2 = 0

	for total in events2:
		if events2[total]['total'] > score2:
			score2 = events2[total]['total']
			event = total
	try:
		autonomous2 = events2[event]['auton']
	except:
		autonomous2 = 0
	try:
		driver2 = events2[event]['driver']
	except:
		driver2 = 0 

	rank1 = int(rank1)
	rank2 = int(rank2)
	if rank1 < rank2:
		rankdif = rank2-rank1
		r1 = f"{rankdif} ⬆️🟩"
		r2 = f"{rankdif} ⬇️🟥"
	else:
		rankdif = rank1-rank2
		r2 = f"{rankdif} ⬆️🟩"
		r1 = f"{rankdif} ⬇️🟥"
	if driver1 > driver2:
		driverdif = driver1-driver2
		d1 = f"{driverdif} ⬆️🟩"
		d2 = f"{driverdif} ⬇️🟥"
	elif driver2 > driver1:
		driverdif = driver2-driver1
		d2 = f"{driverdif} ⬆️🟩"
		d1 = f"{driverdif} ⬇️🟥"
	else:
		d1 = "↔️⏺️"
		d2 = "↔️⏺️"
	if autonomous1 > autonomous2:
		autonomousdif = autonomous1-autonomous2
		a1 = f"{autonomousdif} ⬆️🟩"
		a2 = f"{autonomousdif} ⬇️🟥"
	elif autonomous2 > autonomous1:
		autonomousdif = autonomous2-autonomous1
		a2 = f"{autonomousdif} ⬆️🟩"
		a1 = f"{autonomousdif} ⬇️🟥"
	else:
		a1 = "↔️⏺️"
		a2 = "↔️⏺️"
		
	if score1 > score2:
		scoredif = score1-score2
		s1 = f"{scoredif} ⬆️🟩"
		s2 = f"{scoredif} ⬇️🟥"
	elif score2 > score1:
		scoredif = score2-score1
		s2 = f"{scoredif} ⬆️🟩"
		s1 = f"{scoredif} ⬇️🟥"
	else:
		s1 = "↔️⏺️"
		s2 = "↔️⏺️"
	if autonomousHigh1 > autonomousHigh2:
		ahdif = autonomousHigh1-autonomousHigh2
		ah1 = f"{ahdif} ⬆️🟩"
		ah2 = f"{ahdif} ⬇️🟥"
	elif autonomousHigh2 > autonomousHigh1:
		ahdif = autonomousHigh2-autonomousHigh1
		ah2 = f"{ahdif} ⬆️🟩"
		ah1 = f"{ahdif} ⬇️🟥"
	else:
		ah1 = "↔️⏺️"
		ah2 = "↔️⏺️"
	if driverHigh1 > driverHigh2:
		addif = driverHigh1-driverHigh2
		ad1 = f"{addif} ⬆️🟩"
		ad2 = f"{addif} ⬇️🟥"
	elif driverHigh2 > driverHigh1:
		addif = driverHigh2-driverHigh1
		ad2 = f"{addif} ⬆️🟩"
		ad1 = f"{addif} ⬇️🟥"
	else:
		ad1 = "↔️⏺️"
		ad2 = "↔️⏺️"
	
	embed=discord.Embed(title="Current VIQC Event", url=f"https://www.vexrobotics.com/iq/competition/viqc-current-game", color=0x24c9ff)
	embed.set_author(name=f"Comparing VIQC {team1} vs. {team2}")
	embed.add_field(name=f"{team1} ({team1name}):", value=f"Rank: {rank1} ({r1})\nScore: {score1} ({s1})\nProgramming: {autonomous1} ({a1})\nDriver: {driver1} ({d1})\nHighest Programming: {autonomousHigh1} ({ah1})\nHighest Driver: {driverHigh1} ({ad1})")
	embed.add_field(name=f"{team2} ({team2name}):", value=f"Rank: {rank2} ({r2})\nScore: {score2} ({s2})\nProgramming: {autonomous2} ({a2})\nDriver: {driver2} ({d2})\nHighest Programming: {autonomousHigh2} ({ah2})\nHighest Driver: {driverHigh2} ({ad2})")
	await ctx.send(embed=embed)
# keep_alive.keep_alive()
client.run(token)
