import random
import re
import uuid
from fuzzywuzzy import process
from dataclasses import dataclass

@dataclass
class RainbowData:
    attackers = [
        "Striker", "Sledge", "Thatcher", "Ash", "Thermite", "Twitch", "Montagne", "Glaz", "Fuze", "Blitz", "IQ",
        "Buck", "Blackbeard", "Capitão", "Hibana", "Jackal", "Ying", "Zofia", "Dokkaebi", "Lion", "Finka",
        "Maverick", "Nomad", "Gridlock", "Nøkk", "Amaru", "Kali", "Iana", "Ace", "Zero", "Flores",
        "Osa", "Sens", "Grim", "Brava", "Ram", "Deimos"
    ]

    defenders = [
        "Sentry", "Smoke", "Mute", "Castle", "Pulse", "Doc", "Rook", "Kapkan", "Tachanka", "Jäger", "Bandit",
        "Frost", "Valkyrie", "Caveira", "Echo", "Mira", "Lesion", "Ela", "Vigil", "Alibi", "Maestro",
        "Clash", "Kaid", "Mozzie", "Warden", "Goyo", "Wamai", "Oryx", "Melusi", "Aruni", "Thunderbird",
        "Thorn", "Azami", "Solis", "Fenrir", "Tubarão", "Skopós"
    ]

    maps = {
        'Lair': ['2F Master Office/2F R6 Room', '1F Bunks/1F Briefing', '1F Armory/1F Weapon Maintenance', 'B Lab/B Lab Support'],
        'Club House': ['2F Bedroom/2F Gym', '2F Cash Room/2F CCTV Room', '1F Bar/1F Stage', 'B Church/B Arsenal Room'],
        'Consulate': ['2F Consul Office/2F Meeting Room', '1F Exposition Room/1F Piano Room', 'B Servers/1F Tellers', 'B Cafeteria/B Garage'],
        'Oregon': ['2F Kids\' Dorms/2F Dorms Main Hall', '1F Kitchen/1F Dining Hall', '1F Meeting Hall/1F Kitchen', 'B Laundry Room/B Supply Room'],
        'Kafe Dostoyevsky': ['3F Cocktail Lounge/3F Bar', '2F Fireplace Hall/2F Mining Room', '2F Fireplace Hall/2F Reading Room', '1F Kitchen Cooking/1F Kitchen Service'],
        'Villa': ['2F Games Room/2F Aviator Room', '2F Statuary Room/2F Trophy Room', '1F Living Room/1F Library', '1F Dining Room/1F Kitchen'],
        'Coastline': ['2F Billiards Room/2F Hookah Lounge', '2F Theater/2F Penthouse', '1F Kitchen/1F Service Entrance', '1F Blue Bar/1F Sunrise Bar'],
        'Border': ['2F Armory Lockers/2F Archives', '1F Ventilation Room/1F Workshop', '1F Bathroom/1F Tellers', '1F Customs Inspections/1F Supply Room'],
        'Bank': ['2F Executive Office/2F CEO Office', '1F Staff Room/1F Open Area', '1F Tellers\' Office/1F Archives', 'B Lockers/B CCTV Room'],
        'Chalet': ['2F Master Bedroom/2F Office', '1F Bar/1F Gaming Room', '1F Kitchen/1F Dining Room', 'B Wine Cellar/B Snowmobile Garage'],
        'Favela': ['2F Storage/2F Coin Farm', '2F Coin Farm/2F Bunks', '1F Pink Apartment/1F Pink Kitchen', '1F Blue Bedroom/1F Green Apartment'],
        'Yacht': ['4F Cockpit/4F Maps Room', '2F Engine Control/2F Kitchen', '2F Cafeteria/2F Staff Dormitory', '1F Server Room/1F Engine Storage'],
        'House': ['2F Car Room/2F Pink Room', '2F Master Bedroom/2F Car Room', '1F TV Room/1F Music Room', 'B Gym/B Garage'],
        'Hereford Base': ['3F Ammo Storage/3F Tractor Storage', '2F Master Bedroom/2F Kids Room', '1F Kitchen/1F Dining Room', 'B Brewery/B Fermentation Chamber'],
        'Kanal': ['2F Radar Room/2F Server Room', '1F Map Room/1F Security Room', '1F Coast Guard Meeting Room/1F Lounge', 'B1 Supply Room/B1 Kayaks'],
        'Fortress': ['2F Commander\'s Office/2F Bedroom', '2F Dormitory/2F Briefing Room', '1F Kitchen/1F Cafeteria', '1F Hammam/1F Sitting Room'],
        'Outback': ['2F Laundry/2F Piano Room', '2F Party Room/2F Office', '1F Green Bedroom/1F Red Bedroom', '1F Mechanic Shop/1F Kitchen'],
        'Tower': ['2F Lantern Room/2F Gift Shop', '2F Media Center/2F Exhibit Room', '1F Tea Room/1F Bar', '1F Restaurant/1F Bird Room'],
        'Presidential Plane': ['2F Executive Office/2F Meeting Room', '2F Executive Bedroom/2F Staff Section', '1F Cargo Hold/1F Luggage Hold'],
        'Theme Park': ['2F Initiation Room/2F Office', '2F Bunk/2F Day Care', '1F Armory/1F Throne Room', '1F Lab/1F Storage'],
        'Skyscraper': ['2F Karaoke/2F Tea Room', '2F Exhibition Room/2F Office', '1F BBQ/1F Kitchen', '1F Bathroom/1F Bedroom'],
        'Emerald Plains': ['2F Administration/2F CEO Office', '2F Private Gallery/2F Meeting', '1F Bar/1F Lounge', '1F Dining/1F Kitchen'],
        'Stadium Bravo': ['2F Armory Lockers/2F Archives', '2F Penthouse/2F VIP Lounge', '1F Showers/1F Server', '1F Service/1F Kitchen'],
        'Nighthaven Labs': ['2F Command Center/2F Servers', '1F Kitchen/1F Cafeteria', '1F Control Room/1F Storage', 'B Tank/B Assembly'],
        'UnknownMap': ['FIRST', 'SECOND', 'THIRD', 'FOURTH']
    }

class RainbowMatch:
    def __init__(self, existingMatch=None):
        if existingMatch:
            self.matchId = existingMatch['matchId']
            self.bannedOperators = existingMatch['bannedOperators']
            self.map = existingMatch['map']
            self.sites = existingMatch['sites']
            self.playingOnSide = existingMatch['playingOnSide']
            self.currRound = existingMatch['currRound']
            self.rounds = existingMatch['rounds']
            self.scores = existingMatch['scores']
            self.players = existingMatch['players']
            self.playersString = existingMatch['playersString']
            self.playerStats = existingMatch['playerStats']
        else:
            self.matchId = str(uuid.uuid4())
            self.bannedOperators = []
            self.map = None
            self.sites = self._resetSites()
            self.playingOnSide = None
            self.currRound = 0
            self.rounds = []
            self.scores = {"blue": 0, "red": 0}
            self.players = []
            self.playersString = ''
            self.playerStats = []

    def _getOperators(self):
        """Returns a dictionary with the list of attacker and defender operators."""
        return {
            "attackers": RainbowData.attackers,
            "defenders": RainbowData.defenders
        }
    
    def _getMap(self, map):
        if map is None:
            map = 'UnknownMap'

        maps = RainbowData.maps

        best_match, score = process.extractOne(map, maps.keys())
        if score > 70:
            return [best_match, maps[best_match]]
        return [None, maps['UnknownMap']]

    def _resetSites(self):
        """Resets the sites for the current map."""
        return list(range(len(self._getMap(self.map)[1])))

    def setPlayers(self, playerNames):
        """Sets the players in the current match."""
        for i in range(len(playerNames)):
            if isinstance(playerNames[i], dict):
                continue
            player = playerNames[i]
            playerNames[i] = {
                "id": player.id,
                "mention": player.mention,
                "name": player.name,
                "nick": player.nick,
                "global_name": player.global_name
            }
        
        playerNames = [dict(t) for t in {tuple(d.items()) for d in playerNames}]
        self.players = sorted(playerNames, key=lambda player: (player['nick'].lower() if player['nick'] else (player['global_name'].lower() if player['global_name'] else player['name'].lower())))
        self._constructPlayersString()

    def removePlayers(self, playerNames):
        """Removes the given players from the list of players."""
        originalPlayers = self.players.copy()
        for guildMember in playerNames:
            self.players = [player for player in self.players if player['id'] != guildMember.id]

        if len(self.players) == 0:
            self.players = originalPlayers
            return False

        self._constructPlayersString()
        return True

    def _constructPlayersString(self):
        """Constructs the string of players for the current match."""
        players = [player['mention'] for player in self.players]
        if len(players) > 1:
            lastTwoPlayers = ' and '.join(players[-2:])
            otherPlayers = players[:-2]
            playersString = ', '.join(otherPlayers + [lastTwoPlayers])
        else:
            playersString = players[0] if players else ''
        self.playersString = playersString

    def getMapBan(self):
        """Returns a choice of map that should be banned."""
        mapStrings = ["FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH"]
        return random.sample(mapStrings, k=1)[0]

    def getOperatorBanChoices(self):
        """Returns a choice of operators that should be banned, two for each side (main and backup)."""
        attackers, defenders = self._getOperators().values()
        attBans = random.sample(attackers, k=2)
        defBans = random.sample(defenders, k=2)
        return attBans, defBans

    def banOperators(self, inputString, ban=True):
        """Removes the given operators from the list of available operators, and returns the sanitized list of operators."""
        attackers, defenders = self._getOperators().values()
        input_names = re.split(r'\W+\s*', inputString)

        if not input_names or all(name == '' for name in input_names):
            return []

        sanitized_names = []
        for name in input_names:
            match, score = process.extractOne(name, attackers + defenders) if ban else process.extractOne(name, self.bannedOperators)
            if score >= 75:
                sanitized_names.append(match)
            else:
                sanitized_names.append(None)

        for op in sanitized_names:
            if ban:
                if op in attackers:
                    self.bannedOperators.append(op)
                elif op in defenders:
                    self.bannedOperators.append(op)
            else:
                if op in self.bannedOperators:
                    self.bannedOperators.remove(op)

        return sanitized_names
    
    def swapOperator(self, player, newOperator):
        """Swaps the operator a given player is playing in the current round. The player and new operator are assumed to have been validated already."""
        attackers, defenders = self._getOperators().values()
        playerIndex = next((i for i, p in enumerate(self.players) if p['id'] == player.id), None)

        if newOperator in attackers:
            self.rounds[-1]["operators"][playerIndex] = attackers.index(newOperator) + 1
        else:
            self.rounds[-1]["operators"][playerIndex] = -(defenders.index(newOperator) + 1)

        return [attackers[abs(op) - 1] if op > 0 else defenders[abs(op) - 1] for op in self.rounds[-1]["operators"]], self.rounds[-1]["backupOperators"]

    def setMap(self, map):
        """Sets the map for the current match. Returns True if the map has been set successfully."""
        mapMapping = self._getMap(map)
        if not mapMapping:
            return False

        self.map = mapMapping[0]
        if len(self._getMap(map)[1]) < len(self.sites):
            for site in self.sites:
                if site >= len(self._getMap(map)[1]):
                    self.sites.remove(site)
        return True
    
    def setupRound(self):
        """Starts a new round, returning the chosen operators and site."""
        siteIndex, playedSite = self.getRandomSite() if self.playingOnSide == "defense" else (None, None)
        playedOperators = self.getRandomOperators()
        attackers, defenders = self._getOperators().values()

        self.rounds.append({
            "site": siteIndex,
            # The 1-indexed index of the current operator, negated if it is a defender
            "operators": [(attackers.index(op) + 1) if self.playingOnSide == "attack" else -(defenders.index(op) + 1) for op in playedOperators[:len(self.players)]],
            "backupOperators": playedOperators[len(self.players):],
            "result": None,
            "playerStats": {}
        })
        return playedOperators, playedSite

    def getRandomSite(self):
        """Returns a choice of site that should be played."""
        siteIndex = random.choice(self.sites)
        return siteIndex, self._getMap(self.map)[1][siteIndex]
    
    def trySetSite(self, siteIndex):
        """Attempts to set a new site for the current round. Returns the name of the new site if successful, or None if the site is invalid."""
        # The site index is 1-indexed when input by the user
        siteIndex -= 1
        if siteIndex in self.sites:
            self.rounds[-1]["site"] = siteIndex
            return self._getMap(self.map)[1][siteIndex]
        return None
    
    def getCurrentSiteName(self):
        """Returns the name of the site currently being played."""
        return self._getMap(self.map)[1][self.rounds[-1]["site"]] if self.rounds else None

    def getRandomOperators(self):
        """Returns a random list of operators for the specified side, excluding any banned operators."""
        attackers, defenders = self._getOperators().values()
        available_operators = [op for op in (attackers if self.playingOnSide == "attack" else defenders) if op not in self.bannedOperators]
        return random.sample(available_operators, k=min(5, len(available_operators)))

    def resolveRound(self, result, overtimeSide):
        """Resolves the round, updating the scores and the side, and returns True if the match is still ongoing."""
        self.rounds[-1].pop("backupOperators")

        if result == "won":
            self.scores["blue"] += 1
            self.rounds[-1]["result"] = 1
            if self.playingOnSide == "defense":
                self.sites.remove(self.rounds[-1]["site"])
        else:
            self.scores["red"] += 1
            self.rounds[-1]["result"] = 0

        if self.scores["blue"] == 3 and self.scores["red"] == 3:
            self.playingOnSide = overtimeSide
            self.sites = self._resetSites()
        
        if self.isMatchFinished():
            return False

        self.currRound += 1
        if self.currRound == 4 or self.currRound > 7:
            self.playingOnSide = "attack" if self.playingOnSide == "defense" else "defense"

        return True
    
    def isMatchFinished(self):
        """Returns True if the match is finished."""
        if self.scores["blue"] == 4 and self.scores["red"] < 3:
            return True
        if self.scores["red"] == 4 and self.scores["blue"] < 3:
            return True
        if self.scores["blue"] == 5 or self.scores["red"] == 5:
            return True
        return False

    def addPlayerStat(self, playerId, statType):
        """Adds a player stat to the list of player stats for this match."""
        statTypes = ['interrogations', 'aces']
        if statType in statTypes:
            if self.rounds[-1]['playerStats'].get(statType) is None:
                self.rounds[-1]['playerStats'][statType] = {}
            if self.rounds[-1]['playerStats'][statType].get(str(playerId)) is None:
                self.rounds[-1]['playerStats'][statType][str(playerId)] = 0
            self.rounds[-1]['playerStats'][statType][str(playerId)] += 1

    def getPlayerStat(self, playerId, statType):
        """Returns the number of times a player has gotten a certain stat during the current match."""
        count = 0
        for round in self.rounds:
            if round['playerStats'].get(statType) and round['playerStats'][statType].get(str(playerId)):
                count += round['playerStats'][statType][str(playerId)]
        return count
