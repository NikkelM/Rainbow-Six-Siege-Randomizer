import random
import re
from fuzzywuzzy import process

class RainbowMatch:
    def __init__(self):
        self.attackers, self.defenders = self._getOperators().values()
        self.bannedOperators = []
        self.sites = self._resetSites()
        self.playingOnSide = None
        self.currSite = None
        self.currRound = 0
        self.scores = {"blue": 0, "red": 0}
        self.overtime = False
        self.players = []

    def _getOperators(self):
        """Returns a dictionary with the list of attacker and defender operators."""
        return {
            "attackers": [
                "Sledge", "Thatcher", "Ash", "Thermite", "Twitch", "Montagne",
                "Glaz", "Fuze", "Blitz", "IQ", "Buck", "Blackbeard", "Capitão",
                "Hibana", "Jackal", "Ying", "Zofia", "Dokkaebi", "Lion", "Finka",
                "Maverick", "Nomad", "Gridlock", "Nøkk", "Amaru", "Kali", "Iana",
                "Ace", "Zero", "Flores", "Osa", "Sens", "Grim", "Brava", "Ram"
            ],
            "defenders": [
                "Smoke", "Mute", "Castle", "Pulse", "Doc", "Rook", "Kapkan",
                "Tachanka", "Jäger", "Bandit", "Frost", "Valkyrie", "Caveira",
                "Echo", "Mira", "Lesion", "Ela", "Vigil", "Alibi", "Maestro",
                "Clash", "Kaid", "Mozzie", "Warden", "Goyo", "Wamai", "Oryx",
                "Melusi", "Aruni", "Thunderbird", "Thorn", "Azami", "Solis",
                "Fenrir", "Tubarão"
            ]
        }
    
    def _getMaps(self):
        return {
            'Lair': ['2F Master Office/2F R6 Room', '1F Bunks/1F Briefing', '1F Armory/1F Weapon Maintenance', 'B Lab/B Lab Support'],
            'Clubhouse': ['2F Bedroom/2F Gym', '2F Cash Room/2F CCTV Room', '1F Bar/1F Stage', 'B Church/B Arsenal Room'],
            'Consulate': ['2F Consul Office/2F Meeting Room', '1F Exposition Room/1F Piano Room', 'B Servers/1F Tellers', 'B Cafeteria/B Garage'],
            'Oregon': ['2F Kids\' Dorms/2F Dorms Main Hall', '1F Kitchen/1F Dining Hall', '1F Meeting Hall/1F Kitchen', 'B Laundry Room/B Supply Room'],
            'Kafe Dostoyevsky': ['3F Cocktail Lounge/3F Bar', '2F Fireplace Hall/2F Mining Room', '2F Fireplace Hall/2F Reading Room', '1F Kitchen Cooking/1F Kitchen Service'],
            'Villa': ['2F Games Room/2F Aviator Room', '2F Statuary Room/2F Trophy Room', 'B Living Room/B Library', '1F Dining Room/1F Kitchen'],
            'Coastline': ['2F Billiards Room/2F Hookah Lounge', '2F Theater/2F Penthouse', '1F Kitchen/1F Service Entrance', 'B Blue Bar/B Sunrise Bar'],
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
        }

    def _resetSites(self):
        """Returns a list of site choices, between 1-4."""
        return ["FIRST", "SECOND", "THIRD", "FOURTH"]

    def getMapBan(self):
        """Returns a choice of map that should be banned."""
        mapStrings = ["FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH"]
        return random.sample(mapStrings, k=1)[0]

    def getPlayedSite(self):
        """Returns a choice of site that should be played, and removes the choice from the pool."""
        self.currSite = random.choice(self.sites)
        return self.currSite

    def getOperatorBanChoices(self):
        """Returns a choice of operators that should be banned, two for each side (main and backup)."""
        attBans = random.sample(self.attackers, k=2)
        defBans = random.sample(self.defenders, k=2)
        return attBans, defBans

    def banOperators(self, input_string, ban=True):
        """Removes the given operators from the list of available operators, and returns the sanitized list of operators."""
        input_names = re.split(r'\W+\s*', input_string)

        if not input_names or all(name == '' for name in input_names):
            return []

        sanitized_names = []
        for name in input_names:
            match, score = process.extractOne(name, self.attackers + self.defenders) if ban else process.extractOne(name, self.bannedOperators)
            if score >= 75:
                sanitized_names.append(match)
            else:
                sanitized_names.append(None)

        for op in sanitized_names:
            if ban:
                if op in self.attackers:
                    self.bannedOperators.append(op)
                elif op in self.defenders:
                    self.bannedOperators.append(op)
            else:
                if op in self.bannedOperators:
                    self.bannedOperators.remove(op)

        return sanitized_names

    def setPlayers(self, playerNames):
        """Sets the players in the current match."""
        playerNames = list(set(playerNames))
        self.players = sorted(playerNames, key=lambda player: player.nick if player.nick else (player.global_name if player.global_name else player.name))
        
        self.constructPlayersString()
    
    def removePlayers(self, playerNames):
        """Removes the given players from the list of players."""
        originalPlayers = self.players.copy()
        for player in playerNames:
            if player in self.players:
                self.players.remove(player)

        if len(self.players) == 0:
            self.players = originalPlayers
            return False
        
        self.constructPlayersString()
        return True
    
    def constructPlayersString(self):
        """Constructs the string of players for the current match."""
        players = [player.mention for player in self.players]
        if len(players) > 1:
            lastTwoPlayers = ' and '.join(players[-2:])
            otherPlayers = players[:-2]
            playersString = ', '.join(otherPlayers + [lastTwoPlayers])
        else:
            playersString = players[0] if players else ''
        self.playersString = playersString

    def getPlayedOperators(self, side):
        """Returns a list of operators for the specified side, excluding any banned operators."""
        available_operators = [op for op in (self.attackers if side == "attack" else self.defenders) if op not in self.bannedOperators]
        return random.sample(available_operators, k=min(5, len(available_operators)))

    def resolveRound(self, result, overtimeSide):
        """Resolves the round, updating the scores and the side, and returns True if the match is still ongoing."""
        if result == "won":
            self.scores["blue"] += 1
            if self.playingOnSide == "defense":
                self.sites.remove(self.currSite)
        else:
            self.scores["red"] += 1

        if self.scores["blue"] == 3 and self.scores["red"] == 3:
            self.overtime = True
            self.playingOnSide = overtimeSide
            self.sites = self._resetSites()
        elif not self.overtime and (self.scores["blue"] == 4 or self.scores["red"] == 4):
            return False
        elif self.overtime and (self.scores["blue"] == 5 or self.scores["red"] == 5):
            return False

        self.currRound += 1
        if self.currRound == 4 or self.currRound > 7:
            self.playingOnSide = "attack" if self.playingOnSide == "defense" else "defense"

        return True
