import random

mapStrings = ["FIRST", "SECOND", "THIRD", "FOURTH", "FIFTH"]

attackers = [
    "Sledge", "Thatcher", "Ash", "Thermite", "Twitch", "Montagne",
    "Glaz", "Fuze", "Blitz", "IQ", "Buck", "Blackbeard", "Capitao",
    "Hibana", "Jackal", "Ying", "Zofia", "Dokkaebi", "Lion", "Finka",
    "Maverick", "Nomad", "Gridlock", "Nokk", "Amaru", "Kali", "Iana",
    "Ace", "Zero", "Flores", "Osa", "Sens", "Grim", "Brava", "Ram"
]

defenders = [
    "Smoke", "Mute", "Castle", "Pulse", "Doc", "Rook", "Kapkan",
    "Tachanka", "Jäger", "Bandit", "Frost", "Valkyrie", "Caveira",
    "Echo", "Mira", "Lesion", "Ela", "Vigil", "Alibi", "Maestro",
    "Clash", "Kaid", "Mozzie", "Warden", "Goyo", "Wamai", "Oryx",
    "Melusi", "Aruni", "Thunderbird", "Thorn", "Azami", "Solis",
    "Fenrir", "Tubarao"
]

if __name__ == "__main__":
    print("Welcome to the Rainbow Six Siege randomizer!\n")

    while True:
        print(f"Ban the {random.sample(mapStrings, k=1)[0]} map in the selection, and these operators:")
        print(f"Attack:  {random.sample(attackers, k=2)}")
        print(f"Defense: {random.sample(defenders, k=2)}")
        print()
        print("Enter banned operators, separated by space:")

        print("Attackers")
        attBans = input().split()
        for op in attBans:
            attackers.remove(op) if op in attackers else print(f"Skipping \"{op}\", as it is not a valid attacker.")

        print("Defenders")
        defBans = input().split()
        for op in defBans:
            defenders.remove(op) if op in defenders else print(f"Skipping \"{op}\", as it is not a valid defender.")

        print("Bans processed.\n\nStarting rounds...")
        while True:
            print("Get operators: a for attack, d for defense, r to reset, x to exit:")
            inp = input()
            if inp == "a" or inp =="A":
                lis = random.sample(attackers, k=5)
            elif inp == "d" or inp =="D":
                lis = random.sample(defenders, k=5)
            elif inp == "r" or inp =="R":
                print("\n\nResetting...\n")
                break
            elif inp == "x" or inp =="X":
                print("Exiting...")
                exit()
            else:
                print("Invalid input.")
                continue
            for i in range(5):
                print(f"Player {i}: {lis[i]}")
