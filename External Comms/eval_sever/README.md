To install:

`python3 -m venv <virtual_env_name>`
`source <virtual_env_name>/bin/activate`
`pip3 install -r requirements.txt`

To run:

# Start virtual env
`source <virtual_env_name>/bin/activate`
`python3 eval_server.py <PORT> <GROUP_ID> <NUM_PLAYERS>`

JSON Format:
{
	"p1": Player_1_JSON,
	"p2": Player_2_JSON
}
Player_JSON
{
	"hp":           integer value of current player health,
	"action":       string representing the current action performed by the player
		        Taking values from "grenade, reload, shoot, logout, shield",
	"bullets":      integer value of number of bullets left in the magazine,
	"grenades":     integer value of number of grenades left,
	"shield_time": 	integer value of number of seconds remaining in the shield,
	"shield_health":integer value of amount damage the shield can take,
	"num_deaths":   integer value of number of times the player died,
	"num_shield":   integer value of number of shield left
}

eg:
{
	"p1": {
		"hp": 10,
		"action": "grenade",
		"bullets": 1,
		"grenades": 1,
		"shield_time": 0,
		"shield_health": 3,
		"num_deaths": 1,
		"num_shield": 0
	},
	"p2": {
		"hp": 100,
		"action": "shield",
		"bullets": 2,
		"grenades": 2,
		"shield_time": 1,
		"shield_health": 0,
		"num_deaths": 5,
		"num_shield": 2
	}
}

Packet Format, sent by eval_server: Len_JSON
1) "Len" is the length of "JSON#" sent as plain text
2) "JSON" is the JSON represented as string
3) "Len" and "JSON" are separated by a "_"
Kindly refer the function GameState.send_plaintext in GameState.py for more details.

Packet Format, received by eval_server: Len_crypt(JSON)
1) "Len" is the length of "JSON" sent as plain text
2) "JSON" is the JSON represented as string
3) crypt(JSON) is the AES encrypted form of JSON
4) "Len" and "crypt(JSON)" are separated by a "_"
5) AES encyption mode: CBC
Kindly refer the function Server.recv_game_state and Server.decrypt_message in eval_server.py for more details.

NOTE:
We have conciously avoided commenting our code, except for the "eval_server.py". ;-)