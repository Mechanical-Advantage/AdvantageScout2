import random
import string
import threading
import time

import cherrypy

from config import *
from util import *


class Scheduler:
    """Manages the scout scheduling system."""

    def _auto_schedule_thread(self):
        """Automatically reschedules the next match as necessary."""
        last_event = ""
        last_match = -1
        while True:
            time.sleep(2)

            conn_game = gamedb_connect()
            cur_game = conn_game.cursor()
            conn_global = sql.connect(db_global)
            cur_global = conn_global.cursor()

            event = cur_global.execute(
                "SELECT value FROM config WHERE key = 'event_cached'").fetchall()[0][0]
            enabled = cur_global.execute(
                "SELECT value FROM config WHERE key = 'auto_schedule'").fetchall()[0][0] == "1"
            to_schedule = self.get_next_match(cur_game, cur_global)

            if (to_schedule != last_match or event != last_event) and enabled:
                if self.schedule_match(cur_game, cur_global, conn_global, to_schedule):
                    last_event = event
                    last_match = to_schedule

    def start(self):
        """Launches the auto scheduling thread."""
        threading.Thread(target=self._auto_schedule_thread,
                         daemon=True).start()

    def get_next_match(self, cur_game, cur_global):
        """Returns the next match that hasn't been played (based on submitted teams)."""
        event = cur_global.execute(
            "SELECT value FROM config WHERE key = 'event_cached'").fetchall()[0][0]
        data = cur_game.execute(
            "SELECT match, COUNT(match) FROM match WHERE Event=? GROUP BY match ORDER BY match DESC", (event,)).fetchall()
        to_schedule = -1
        for i in data:
            if i[1] >= auto_schedule_min_count:
                to_schedule = i[0] + 1
                break
        if to_schedule == -1:
            to_schedule = 1
        return to_schedule

    def schedule_match(self, cur_game, cur_global, conn_global, match):
        """Updates the schedule based on the provided match number. Returns a boolean indicating success."""

        event = cur_global.execute(
            "SELECT value FROM config WHERE key = 'event_cached'").fetchall()[0][0]
        cherrypy.log("Creating new schedule for match " + str(match))

        # Find teams in match
        teams = cur_global.execute(
            "SELECT b1,b2,b3,r1,r2,r3 FROM schedule WHERE match=?", (match,)).fetchall()
        if len(teams) == 0:
            cherrypy.log("Could not create schedule for match " + str(match))
            return False
        teams = teams[0]

        # Get scout records
        scouts = [x[0] for x in cur_global.execute(
            "SELECT name FROM scouts WHERE enabled='1' ORDER BY name").fetchall()]
        if len(scouts) < 6:
            cherrypy.log("Not enough scouts to schedule match " + str(match))
            return False

        scout_records = []
        for scout in scouts:
            scoutdata = {"name": scout}
            records = cur_game.execute(
                "SELECT Team, COUNT(*) FROM match WHERE ScoutName=? GROUP BY Team", (scout,)).fetchall()
            for row in records:
                scoutdata[row[0]] = row[1]
            pit_records = cur_game.execute(
                "SELECT Team, COUNT(*) FROM pit WHERE ScoutName=? GROUP BY Team", (scout,)).fetchall()
            for row in pit_records:
                if row[0] in scoutdata:
                    scoutdata[row[0]] += row[1] * 2
                else:
                    scoutdata[row[0]] = row[1] * 2
            scoutdata["total"] = cur_game.execute(
                "SELECT COUNT(*) FROM match WHERE Event=? AND ScoutName=?", (event, scout)).fetchall()[0][0]
            scout_records.append(scoutdata)

        # Get scout preferences
        scout_prefs = []
        pref_data = cur_global.execute(
            "SELECT team, scout FROM scout_prefs ORDER BY priority").fetchall()
        for record in pref_data:
            scout_prefs.append({
                "team": record[0],
                "scout": record[1]
            })

        schedule = self._calc_optimal(
            teams=teams, scout_records=scout_records, total_priority=schedule_total_priority, prefs=scout_prefs)

        # Write to db
        cur_global.execute("DELETE FROM schedule_next")
        cur_global.execute(
            "UPDATE config SET value=? WHERE key='schedule_match'", (match,))
        key = ''.join(random.choices(string.ascii_lowercase +
                                     string.ascii_uppercase + string.digits, k=15))
        cur_global.execute(
            "UPDATE config SET value=? WHERE key='schedule_key'", (key,))
        for team in teams:
            cur_global.execute(
                "INSERT INTO schedule_next(team,scout) VALUES (?,?)", (team, schedule[team]))
        conn_global.commit()
        return True

    def _calc_optimal(self, teams, scout_records, total_priority, prefs):
        """Finds the optimal schedule for a single match."""

        # Check for 6 scouts
        if len(scout_records) < 6:
            return "Error - needs 6 scouts"

        # Add ids and totals to scout records array
        for i in range(len(scout_records)):
            scout_records[i]['id'] = i

        # Update scout records array (to add teams)
        for i in range(len(scout_records)):
            for teamnumber in range(len(teams)):
                if teams[teamnumber] not in scout_records[i].keys():
                    scout_records[i][teams[teamnumber]] = 0

        # Update from prefs
        prefs = prefs[::-1]
        for i in range(len(prefs)):
            index = [index for index, value in enumerate(
                scout_records) if value["name"] == prefs[i]["scout"]]
            if len(index) < 1:
                continue
            index = index[0]
            scout_records[index][prefs[i]["team"]] = 100000 * (i + 1)

        # Create priority lists
        def priority_list(team):
            sorted_scouts = []
            for i in range(len(scout_records)):
                sorted_scouts.append({"id": scout_records[i]['id'], "priority": float(scout_records[i][team]) - float(
                    scout_records[i]['total'])*(total_priority), "total": scout_records[i]['total']})
            sorted_scouts = sorted(
                sorted_scouts, key=lambda x: (-x['priority'], x['total']))
            temp_output = []
            for i in range(len(sorted_scouts)):
                temp_output.append(sorted_scouts[i]['id'])
            return temp_output

        # Create match schedule
        scheduled = {}

        # Generate priority lists
        priority_lists = {}
        for teamnumber in range(6):
            priority_lists[teams[teamnumber]] = priority_list(
                team=teams[teamnumber])

        # Function for removing a scout from priority lists (once assigned)
        def remove_from_priority(scout):
            for team, list in priority_lists.items():
                while scout in priority_lists[team]:
                    priority_lists[team].remove(scout)

        # Function for one cycle of assignments
        def assign_scouts():
            # Generate lists of scout requests
            scout_requests = []
            for i in range(len(scout_records)):
                scout_requests.append([])
            for team, list in priority_lists.items():
                if len(list) > 0:
                    scout_requests[priority_lists[team][0]].append(team)

            # Iterate through scout requests (resolving conflicts when neccessary)
            for scout_request_number in range(len(scout_requests)):
                if len(scout_requests[scout_request_number]) == 1:
                    # No conflict (scout requested by one team)
                    scheduled[scout_requests[scout_request_number][0]
                              ] = scout_request_number  # Add to schedule
                    # Clear priority list for team
                    priority_lists[scout_requests[scout_request_number][0]] = []
                    # Remove scout from priority lists (so cannot be selected for another team)
                    remove_from_priority(scout=scout_request_number)
                elif len(scout_requests[scout_request_number]) > 1:
                    # Conflict found (scout requested by multiple teams)
                    # Resolved by comparing potential 'loss of experience' if each team used secondary scout
                    comparison_data = []
                    for i in range(len(scout_requests[scout_request_number])):
                        first_value = scout_records[priority_lists[scout_requests[scout_request_number]
                                                                   [i]][0]][scout_requests[scout_request_number][i]]
                        first_value -= float(
                            scout_records[priority_lists[scout_requests[scout_request_number][i]][0]]['total'])*total_priority
                        second_value = scout_records[priority_lists[scout_requests[scout_request_number]
                                                                    [i]][1]][scout_requests[scout_request_number][i]]
                        second_value -= float(
                            scout_records[priority_lists[scout_requests[scout_request_number][i]][1]]['total'])*total_priority
                        # Find difference between experience of primary and secondary scout
                        comparison_data.append(first_value - second_value)

                    maxid = 0
                    for i in range(len(comparison_data)):
                        if comparison_data[i] > comparison_data[maxid]:
                            maxid = i
                    scheduled[scout_requests[scout_request_number][maxid]
                              ] = scout_request_number  # Add to schedule
                    # Clear priority list for team
                    priority_lists[scout_requests[scout_request_number][maxid]] = [
                    ]
                    # Remove scout from priority lists (so cannot be selected for another team)
                    remove_from_priority(scout=scout_request_number)

        # Run cycles of assignment until schedule created
        while len(scheduled) < 6:
            assign_scouts()

        # Update with scout names
        for team, scoutnumber in scheduled.items():
            scheduled[team] = scout_records[scoutnumber]["name"]

        return scheduled
