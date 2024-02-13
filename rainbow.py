import random
import re
from fuzzywuzzy import process


class Rainbow:
    def __init__(self):
        self.attackers = [
            "Sledge", "Thatcher", "Ash", "Thermite", "Twitch", "Montagne",
            "Glaz", "Fuze", "Blitz", "IQ", "Buck", "Blackbeard", "Capitao",
            "Hibana", "Jackal", "Ying", "Zofia", "Dokkaebi", "Lion", "Finka",
            "Maverick", "Nomad", "Gridlock", "Nokk", "Amaru", "Kali", "Iana",
            "Ace", "Zero", "Flores", "Osa", "Sens", "Grim", "Brava", "Ram"
        ]
        self.defenders = [
            "Smoke", "Mute", "Castle", "Pulse", "Doc", "Rook", "Kapkan",
            "Tachanka", "Jäger", "Bandit", "Frost", "Valkyrie", "Caveira",
            "Echo", "Mira", "Lesion", "Ela", "Vigil", "Alibi", "Maestro",
            "Clash", "Kaid", "Mozzie", "Warden", "Goyo", "Wamai", "Oryx",
            "Melusi", "Aruni", "Thunderbird", "Thorn", "Azami", "Solis",
            "Fenrir", "Tubarao"
        ]
        self.sites = list(range(1, 5))
        self.side = None
        self.currRound = 1
        self.scores = {"blue": 0, "red": 0}
        self.overtime = False
        self.players = []

    def getMapBan(self):
        mapStrings = ["FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH"]
        return random.sample(mapStrings, k=1)[0]
    
    def getPlayedSite(self):
        # Return a random site that hasn't been played yet
        # Choice one to four
        site = random.choice(self.sites)
        self.sites.remove(site)
        return site
    
    def resetSites(self):
        self.sites = list(range(1, 5))

    def getOperatorBans(self):
        attBans = random.sample(self.attackers, k=2)
        defBans = random.sample(self.defenders, k=2)
        return attBans, defBans

    def setBannedOperators(self, attBans, defBans):
        for op in attBans:
            self.attackers.remove(op)
        for op in defBans:
            self.defenders.remove(op)

    def matchOperatorNames(self, input_string):
        # Split the input string into words using non-alphanumeric characters followed by zero or more spaces as separators
        input_names = re.split(r'\W+\s*', input_string)

        # Use fuzzy matching to find the closest match for each input name in the operator list
        sanitized_names = []
        for name in input_names:
            match, score = process.extractOne(
                name, self.attackers + self.defenders)
            if score >= 60:
                sanitized_names.append(match)
                # TODO: Return a None or a special value for names that don't match, so the bot can say he didn't understand
                # TODO: Add a command !amendBans to add a singular new ban
            else:
                sanitized_names.append(None)
        
        # Ban the operators that were matched
        self.setBannedOperators(
            [name for name in sanitized_names if name in self.attackers],
            [name for name in sanitized_names if name in self.defenders]
        )

        return sanitized_names

    def setPlayerNames(self, playerNames):
        self.players = playerNames

    def setSide(self, side):
        self.side = side

    def getAttackers(self):
        return random.sample(self.attackers, k=len(self.players))

    def getDefenders(self):
        return random.sample(self.defenders, k=len(self.players))

    # Returns False if the match is over, True otherwise
    def resolveRound(self, result, overtimeSide):
        if result == "won":
            self.scores["blue"] += 1
        else:
            self.scores["red"] += 1

        if self.scores["blue"] == 3 and self.scores["red"] == 3:
            self.overtime = True
            self.setSide(overtimeSide)
            self.resetSites()
        elif not self.overtime and (self.scores["blue"] == 4 or self.scores["red"] == 4):
            return False
        elif self.overtime and (self.scores["blue"] == 5 or self.scores["red"] == 5):
            return False

        self.currRound += 1
        if self.currRound == 4 or self.currRound > 7:
            self.setSide("attack" if self.side == "defense" else "defense")

        return True
