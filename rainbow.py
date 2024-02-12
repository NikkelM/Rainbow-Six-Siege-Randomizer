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

    def getMapBan(self):
        mapStrings = ["FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH"]
        return random.sample(mapStrings, k=1)[0]

    def getOperatorBans(self):
        attBans = random.sample(self.attackers, k=2)
        defBans = random.sample(self.defenders, k=2)
        return attBans, defBans

    def setBannedOperators(self, attBans, defBans):
        for op in attBans:
            self.attackers.remove(op)
        for op in defBans:
            self.defenders.remove(op)

    def matchOperatorName(self, input_string):
        # Split the input string into words using non-alphanumeric characters followed by zero or more spaces as separators
        input_names = re.split(r'\W+\s*', input_string)
        print(input_names)

        # Use fuzzy matching to find the closest match for each input name in the operator list
        sanitized_names = []
        for name in input_names:
            match, score = process.extractOne(name, self.attackers + self.defenders)
            print(f"Matched {name} to {match} with a score of {score}")
            if score >= 80:  # You can adjust this threshold as needed
                sanitized_names.append(match)
                # TODO: Return a None or a special value for names that don't match, so the bot can say he didn't understand
                # TODO: Add a command !amendBans to add a singular new ban

        return sanitized_names

    def run(self):
        print("Welcome to the Rainbow Six Siege randomizer!\n")

        while True:
            print(
                f"Ban the {self.getMapBan()} map in rotation, and these operators:")
            attBans, defBans = self.getOperatorBans()
            print(f"Attack:  {attBans}")
            print(f"Defense: {defBans}")
            print()
            print("Enter banned operators, separated by space:")

            print("Attackers")
            attBans = input().split()
            for op in attBans:
                if op in self.attackers:
                    self.attackers.remove(op)
                else:
                    print(f"Skipping \"{op}\", as it is not a valid attacker.")

            print("Defenders")
            defBans = input().split()
            for op in defBans:
                if op in self.defenders:
                    self.defenders.remove(op)
                else:
                    print(f"Skipping \"{op}\", as it is not a valid defender.")

            print("Bans processed.\n\nStarting rounds...")
            while True:
                print(
                    "Get operators: a for attack, d for defense, r to reset, x to exit:")
                inp = input()
                if inp == "a" or inp == "A":
                    lis = random.sample(self.attackers, k=5)
                elif inp == "d" or inp == "D":
                    lis = random.sample(self.defenders, k=5)
                    random.shuffle(self.sites)
                    print(f"Numbers 1 to 4 in random order: {self.sites}")
                elif inp == "r" or inp == "R":
                    print("\n\nResetting...\n")
                    break
                elif inp == "x" or inp == "X":
                    print("Exiting...")
                    exit()
                else:
                    print("Invalid input.")
                    continue
                for i in range(5):
                    print(f"Player {i+1}: {lis[i]}")


if __name__ == "__main__":
    Rainbow().run()
