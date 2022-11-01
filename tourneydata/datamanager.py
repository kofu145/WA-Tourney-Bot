import json
from osuapi import osu_wrapper

class TDataManager():
    def __init__(self, osu_handler: osu_wrapper.OsuWrapper, matches: str, users: str, teams:str, localdata:str):
        self.osu_handler = osu_handler

        self.match_path = matches
        self.users_path = users
        self.teams_path = teams
        self.localdata_path = localdata

        with open(matches, "r") as f:
            self.matches = json.load(f)
        with open(users, "r") as f:
            self.users = json.load(f)
        with open(teams, "r") as f:
            self.teams = json.load(f)
        with open(localdata, "r") as f:
            self.localdata = json.load(f)

    def add_match(self, match_id, local_id, red_id, blue_id, referee_id, protects, bans, warmups):
        if local_id in self.matches:
            raise Exception("match id already exists within played matches!")

        adding_match = self.osu_handler.get_match(match_id)

        adding_match["suijidata"] = {
            "teams": {
                "red": red_id,
                "blue": blue_id
            },
            "protects": protects,
            "bans": bans,
            "referee": referee_id,
            "warmups": warmups
            # warmups
        }

        self.matches[local_id] = adding_match

        # this is here thanks to the fact that match result names are saved as the same
        self.matches[local_id]['match']['name'] = f"WSB: ({self.get_team(red_id)['name']}) vs ({self.get_team(blue_id)['name']})"

        self.matches = dict(sorted(self.matches.items()))
        self.update()

    def get_match(self, match_id, is_local_id=True):
        if is_local_id:
            return self.matches[str(match_id)]

        else:
            return self.osu_handler.get_match(match_id)


    def parse_match_data(self, match, ignore=2):
        # ignore param is for warmups
        ignore = match['suijidata']['warmups']
        maps = []
        for i in match["events"]:
            payload = {
                "name": "",
                "image_url": "",
                "red_score": 0,
                "blue_score": 0,
                "scores": [],
                "url": ""
            }

            if i["detail"]["type"] == "other":
                if ignore > 0:
                    ignore -= 1
                    continue 
                payload["name"] = f"{i['game']['beatmap']['beatmapset']['title']} [{i['game']['beatmap']['version']}]"
                payload["image_url"] = i['game']['beatmap']['beatmapset']['covers']['cover']
                payload["url"] = f"https://osu.ppy.sh/beatmapsets/{i['game']['beatmap']['beatmapset_id']}#osu/{i['game']['beatmap']['id']}"

                for j in i["game"]["scores"]:
                    if j['match']['pass']:
                        if j['match']['team'] == 'red':
                            payload["red_score"] += j["score"]
                        elif j['match']['team'] == 'blue':
                            payload["blue_score"] += j["score"]

                    payload["scores"].append(j)
                
                maps.append(payload)
        return maps


    def get_team(self, team_id: int):
        return self.teams[team_id]

    def get_user(self, user_id: int):
        return self.users[user_id] if user_id in self.users else self.osu_handler.get_user(user_id)

    def validate_staff(self, user_id):
        return True if user_id in self.teams[0]["users"] else False

    def get_leaderboards(self):
        return self.localdata['total_score']

    def recalc_leaderboards(self):
        self.localdata["total_score"] = {}
        self.localdata["score_averages"] = {}

        for team in self.teams:
            if team['name'] != "Staff":
                for j in team['users']:
                    self.localdata['total_score'][j] = 0
                    self.localdata['score_averages'][j] = []

        for match in self.matches:
            for i in self.matches[match]["events"]:
                if i["detail"]["type"] == "other":
                    for j in i["game"]["scores"]:
                        self.localdata['total_score'][j['user_id']] += j['score']
                        self.localdata['score_averages'][j['user_id']].append(j['score'])
    

    def update(self) -> None:
        with open(self.match_path, "w") as f:
            json.dump(self.matches, f, indent=2)

        with open(self.users_path, "w") as f:
            json.dump(self.users, f, indent=2)

        with open(self.teams_path, "w") as f:
            json.dump(self.teams, f, indent=2)

        with open(self.localdata_path, "w") as f:
            json.dump(self.localdata, f, indent=2)


