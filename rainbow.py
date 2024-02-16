import random
import re
from fuzzywuzzy import process


class RainbowMatch:
    def __init__(self):
        self.attackers, self.defenders = self._getOperators().values()
        self.sites = self._resetSites()
        self.playingOnSide = None
        self.currRound = 1
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

    def _resetSites(self):
        """Returns a list of site choices, between 1-4."""
        return list(range(1, 5))

    def getMapBan(self):
        """Returns a choice of map that should be banned."""
        mapStrings = ["FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH"]
        return random.sample(mapStrings, k=1)[0]

    def getPlayedSite(self):
        """Returns a choice of site that should be played, and removes the choice from the pool."""
        site = random.choice(self.sites)
        self.sites.remove(site)
        return site

    def getOperatorBanChoices(self):
        """Returns a choice of operators that should be banned, two for each side (main and backup)."""
        attBans = random.sample(self.attackers, k=2)
        defBans = random.sample(self.defenders, k=2)
        return attBans, defBans

    def banOperators(self, input_string):
        """Removes the given operators from the list of available operators, and returns the sanitized list of operators."""
        input_names = re.split(r'\W+\s*', input_string)

        if not input_names or all(name == '' for name in input_names):
            return []

        sanitized_names = []
        for name in input_names:
            match, score = process.extractOne(
                name, self.attackers + self.defenders)
            if score >= 60:
                sanitized_names.append(match)
                # TODO: Add a command !amendBans to add a singular new ban
            else:
                sanitized_names.append(None)

        for op in sanitized_names:
            if op is not None:
                if op in self.attackers:
                    self.attackers.remove(op)
                else:
                    self.defenders.remove(op)

        return sanitized_names

    def setPlayerNames(self, playerNames):
        """Sets the players in the current match."""
        self.players = playerNames

    def getAttackers(self):
        """Returns a list of attackers, one for each player in the match."""
        return random.sample(self.attackers, k=len(self.players))

    def getDefenders(self):
        """Returns a list of defenders, one for each player in the match."""
        return random.sample(self.defenders, k=len(self.players))

    def resolveRound(self, result, overtimeSide):
        """Resolves the round, updating the scores and the side, and returns True if the match is still ongoing."""
        if result == "won":
            self.scores["blue"] += 1
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
