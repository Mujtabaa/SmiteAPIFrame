import hashlib
import json
import time
import requests
import string
import re
from functools import wraps
import os
from SmiteAPIFrameFolder import PersonalKeys 
#import PersonalKeys #Swap between this and the above for main (this) vs package (above)

# set your devId and authKey here
devId=PersonalKeys.devId
authKey=PersonalKeys.authKey


base_api_url_PC='https://api.smitegame.com/smiteapi.svc/'
base_api_url_XBOX='http://api.xbox.smitegame.com/smiteapi.svc/'
base_api_url_PS4='http://api.ps4.smitegame.com/smiteapi.svc/'


def valid_session_check(func):
    
    @wraps(func)
    def wrapper(session_id=None,*args, **kwargs):
            # check if a session is still valid, and generate a new session ID if necessary
        if is_session_valid():
            print(f"Session is valid.")
            # session is still valid, use the existing session ID    
            with open('CurrentSessionID.txt', 'r') as f:
                session_id = str(f.read())
        else:
            print(f"Session is expired.")
            # session has expired, generate a new session ID
            session_id = generate_session_id()
            print(f"New session created.")

        data = func(session_id=session_id,*args, **kwargs)
        return data
    
    return wrapper


def general_API_url(method = None, session_id = None, developer_id= None, authorization_key = None):
    """
    General Smite API url for endpoints in json.
                
        

    Parameters:
    - method (str): Specifies the api endpoint. Should be provided by other functions 
                  ex. 'endpoint'
    - session_id (str): Personal session_id needed to make api calls. Should be provided by other functions
                created by generate_session_id() function
    - developer_id (int): devID provided by HiRez
    - authorization_key (str): authKey provided by HiRez


    Returns:
    - [API_URL]/{method}[ResponseFormat]/{developerId}/{signature}/{session}/{timestamp} as a string
                Returns None if any parameter is missing


    Raises:
    - Nothing, there's no error catching yet
    """
    if devId:
        developer_id = devId
    if authKey:
        authorization_key = authKey
    params = (method, session_id, developer_id, authorization_key)
    
    if any(param is None for param in params):
        return None

    timestamp = time.strftime('%Y%m%d%H%M%S', time.gmtime())
    signature = hashlib.md5(f"{developer_id}{method}{authorization_key}{timestamp}".encode('utf-8')).hexdigest()
    url = f'https://api.smitegame.com/smiteapi.svc/{method}json/{developer_id}/{signature}/{session_id}/{timestamp}'
    return url

##############################################################################
########## APIs - Connectivity, Development, & System Status #################
##############################################################################

# pings to the hirez api
def api_ping(platform=0):
    """
    Send a ping request to the API.

    Parameters:
    - platform (int): Specifies the api platform (if applicable). 
                  0 for PC (default), 1 for Xbox, 2 for PS4

    Returns:
    - Response result as json.


    Raises:
    - ValueError: If platform is not 0, 1 or 2.
    """
    try:
        if platform not in (0, 1, 2):
            raise ValueError("Platform input can only be 0 (PC), 1 (XBOX), or 2 (PS4)")
    except ValueError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)
    

    url_list = [base_api_url_PC, base_api_url_XBOX, base_api_url_PS4]

    url = f'{url_list[platform]}pingJson'

    response = requests.get(url) 

    if response.status_code != 200:
        print("Error: Request failed.")
        return
    # print(response.headers)
    # ourcontent = response.content
    # print(f'the response body is {len(ourcontent.decode("utf-8"))} bytes i think \n')
    return response.json()

# create a function to generate a new session ID
def generate_session_id():
    """
    Creates a new session ID for the user, requires personal DeveloperID and AuthKey.

    Parameters:
    - platform (int): Specifies the api platform (if applicable). 
                  0 for PC (default), 1 for Xbox, 2 for PS4

    Returns:
    - Response result as json.


    Raises:
    - ValueError: If platform is not 0, 1 or 2.
    """
    method = "createsession"
    # get the current UTC time formatted as yyyyMMddHHmmss
    timestamp = time.strftime('%Y%m%d%H%M%S', time.gmtime())

    # create the signature by concatenating the devId, method name, authKey, and timestamp
    signature = hashlib.md5(f"{devId}{method}{authKey}{timestamp}".encode('utf-8')).hexdigest()

    # make the API request to generate a new session ID
    url = f"https://api.smitegame.com/smiteapi.svc/{method}Json/{devId}/{signature}/{timestamp}"
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Request failed.")
        return

    # parse the JSON response
    data = json.loads(response.text)
    print(data)
    print("the generate session id function called this\n")
    # extract the session ID from the response
    sessionId = data['session_id']

    # write the current timestamp value to a file
    with open('timestamp.txt', 'w') as f:
        f.write(str(int(time.time())))

    with open('CurrentSessionID.txt', 'w') as f:
        f.write(str(sessionId))

    return sessionId

# create a function to check if the session is still valid
def is_session_valid():
    """
    Checks the session timestamp for validity. Min-Max session creation limit.
    Limit is 15min but I changed it to 14min bc I would get kicked out mid get request

    Parameters:
    - None needed

    Errors:
    - Returns false if the 'timestamp.txt' or 'CurrentSessionID.txt' are not found

    Returns:
    - True: if 14 minutes has not passed (is valid)
    - False: if 14 minutes has passed (not valid)

    """
    #Timestamp is stored as int(time.time())
    if not os.path.exists('timestamp.txt'):
        return False
    if not os.path.exists('CurrentSessionID.txt'):
        return False
    
    with open('timestamp.txt', 'r') as f:
        stored_timestamp = int(f.read())

    current_time = int(time.time())
    elapsed_time = current_time - stored_timestamp
    session_length = 14 * 60 

    # Returns True if less than 14min has passed since last session creation
    return elapsed_time < session_length

# determines if a session is valid or not - endpoint
def _test_session():
    """
    Not sure how to differentiate between a fail or successful test; both return approved ret_msg and a 200 status code
    Probably not going to use this 
    """
    with open('CurrentSessionID.txt', 'r') as f:
        sesh = str(f.read())
    url = general_API_url(method='testsession',session_id=sesh)
    response = requests.get(url)
    if response.status_code != 200:
        print("Error: Request failed.")
        return
    print (response)
    print ("\n\n\n")
    wow = response.json()
    
    print (wow)
    return 

# user's api limits
@valid_session_check
def MyData(session_id=None):
    """
    Checks the user's # of active sessions, session/request limit (500/7500), and current amount of sessions/requests made today.

    Parameters:
    - None needed

    Returns:
    - Response result as json; a list containing 1 dictionary
    - Returns nothing if status code fails

    """
    url = general_API_url(method="getdataused",session_id=session_id)

    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Request failed.")
        return

    data = response.json()
    
    return data

# servers down ?
@valid_session_check
def get_hirez_server_status(session_id=None):
    """
    Checks the availability of HiRez servers of Smite for PC/Switch/Xbox/PS4.
    Also contains version information

    Parameters:
    - None needed

    Returns:
    - Response result as json; a list of dictionaries.
    - Returns nothing if status code fails
    
    Notes:
    - Most likely used when patch versions between platforms weren't sync'd
    - Also includes pts status !!!

    """
 

    url = general_API_url(method='gethirezserverstatus',session_id=session_id)
    response = requests.get(url)
    if response.status_code != 200:
        print("Error: Request failed.")
        return
 
    data = response.json()
  
    return data

# Patch info, very simple
@valid_session_check
def get_patch_info(session_id=None):
    """
    Checks the version of Smite on live servers.
    

    Parameters:
    - None needed

    Returns:
    - Response result as json; a list of dictionaries.
    - Returns nothing if status code fails

    Notes:
    - Similar to get_hirez_server_status() but only specifies patch

    """
 

    url = general_API_url(method='getpatchinfo',session_id=session_id)
    response = requests.get(url)
    if response.status_code != 200:
        print("Error: Request failed.")
        return
 
    data = response.json()
  
    return data

##############################################################################
################## APIs - Gods/Champions & Items #############################
##############################################################################

# all god info
@valid_session_check
def get_gods(session_id= None, language_code = 1):
    """
    Returns all Gods and their various attributes.

    Parameters:
    - language_code (int): Specifies the language return
    - (1) - English |	(2) - German | (3) - French | (5) - Chinese | (7) - Spanish | (9) - Spanish (Latin America) | 
    - (10) - Portuguese | (11) - Russian | (12) - Polish | (13) - Turkish |

    Data:
    - Returns literally everything about every god; abilities, lore, id's etc
    - No way to retrieve data on a specific god from the api

    Notes:
    - Probably want to save this in a database and use this to update databases every patch

    Returns:
    - Response result as json
    - Returns nothing if status code fails


    Raises:
    - ValueError: If invalid language code is entered
    """
    
    try:
        if language_code not in (1, 2, 3, 5, 7, 9, 10, 11, 12, 13):
            raise ValueError("Invalid language code")
    except ValueError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)
    
    base_url = general_API_url(method="getgods",session_id=session_id)
    
    url = base_url + '/' + str(language_code)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Request failed.")
        return

    data = response.json()
    
    return data

# top 100 leaderboard
@valid_session_check
def get_god_leaderboard(session_id= None, god_id = None, queue = 451):
    """
    Returns the current season's leaderboard for a god/queue combination.

    Parameters:
    - god_id (int): Unique identifier for a god (found in get_gods endpoint)
    - queue (int): Specifies the gamemode
    - (440) - Ranked Duel |	(450) - Ranked Joust | (451) - Ranked Conquest 
    

    Data:
    - Returns top 100 ranked players with a specific god

    Notes:
    - Not entirely accurate

    Returns:
    - Response result as json
    - Returns nothing if status code fails


    Raises:
    - ValueError: If invalid queue code is entered
    """
    try:
        if queue not in (440, 450, 451):
            raise ValueError("Invalid Queue")
    except ValueError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)
    

    base_url = general_API_url(method="getgodleaderboard",session_id=session_id)
    
    url = base_url + '/' + str(god_id) + '/' + str(queue)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Get God Leaderboard Request failed.")
        return

    data = response.json()
    
    return data

#Returns alt abilities for all gods.
@valid_session_check
def get_god_alt_abilities(session_id=None):
    """
    Returns alt abilities for all gods.

    Parameters:
    - None needed

    Returns:
    - Response result as json
    - Returns nothing if status code fails

    Data:
    - Alt abilities per god with their id

    Notes:
    - Not up to date (missing ix chel at least)
    - Weird naming scheme and non-intuitive alt abilities
    - Probably not entirely useful, only for like merlin, tia, KA, lulu

    """
    url = general_API_url(method='getgodaltabilities',session_id=session_id)
    response = requests.get(url)
    if response.status_code != 200:
        print("Error: Request failed.")
        return
 
    data = response.json()
  
    return data

# skin details for a particular god
@valid_session_check
def get_god_skins(session_id=None, god_id = None, language_code = 1):
    """
    Returns the current season's leaderboard for a god/queue combination.

    Parameters:
    - god_id (int): Unique identifier for a god (found in get_gods endpoint)
    - language_code (int): Specifies the language return
    - (1) - English |	(2) - German | (3) - French | (5) - Chinese | (7) - Spanish | (9) - Spanish (Latin America) | 
    - (10) - Portuguese | (11) - Russian | (12) - Polish | (13) - Turkish |
    

    Data:
    - God skins for a particular god
    - Includes its cardart, rarity, skin name and skin id

    Notes:
    - Legendary/Diamond does not have card art URLs

    Returns:
    - Response result as json
    - Returns nothing if status code fails


    Raises:
    - ValueError: If invalid language code is entered
    """

    try:
        if language_code not in (1, 2, 3, 5, 7, 9, 10, 11, 12, 13):
            raise ValueError("Invalid language code")
    except ValueError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)
    
    base_url = general_API_url(method="getgodskins",session_id=session_id)
    
    url = base_url + '/' + str(god_id) + '/' + str(language_code)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Get God Skins request failed.")
        return

    data = response.json()
    
    return data

#items on the recc part of the item store
@valid_session_check
def get_god_recommended_items(session_id=None, god_id = None, language_code = 1):
    """
    Returns the Recommended Items for a particular God. 

    Parameters:
    - god_id (int): Unique identifier for a god (found in get_gods endpoint)
    - language_code (int): Specifies the language return
    - (1) - English |	(2) - German | (3) - French | (5) - Chinese | (7) - Spanish | (9) - Spanish (Latin America) | 
    - (10) - Portuguese | (11) - Russian | (12) - Polish | (13) - Turkish |
    

    Data:
    - Recommended items with its category, item name, item id, and role (gamemode)

    Notes:
    - Includes legacy items for some reason, "role_value_id" probably has something to do with it

    Returns:
    - Response result as json
    - Returns nothing if status code fails


    Raises:
    - ValueError: If invalid language code is entered
    """

    try:
        if language_code not in (1, 2, 3, 5, 7, 9, 10, 11, 12, 13):
            raise ValueError("Invalid language code")
    except ValueError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)
    
    base_url = general_API_url(method="getgodrecommendeditems",session_id=session_id)
    
    url = base_url + '/' + str(god_id) + '/' + str(language_code)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Get God Recc Items request failed.")
        return

    data = response.json()
    
    return data

#stats and descr of all store items/revamped items/retired items
@valid_session_check
def get_items(session_id= None, language_code = 1):
    """
    Returns all Items and their various attributes.

    Parameters:
    - language_code (int): Specifies the language return
    - (1) - English |	(2) - German | (3) - French | (5) - Chinese | (7) - Spanish | (9) - Spanish (Latin America) | 
    - (10) - Portuguese | (11) - Russian | (12) - Polish | (13) - Turkish |

    Data:
    - Returns information of all items in the game, stats, icon urls and descriptions
    - Has an "Active_Flag" to show if it is currently enabled in the game

    Notes:
    - Some icon url's are screwed up, i believe some can be fixed, but it will need to be done manually

    Returns:
    - Response result as json
    - Returns nothing if status code fails


    Raises:
    - ValueError: If invalid language code is entered
    """
    
    try:
        if language_code not in (1, 2, 3, 5, 7, 9, 10, 11, 12, 13):
            raise ValueError("Invalid language code")
    except ValueError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)
    
    base_url = general_API_url(method="getitems",session_id=session_id)
    
    url = base_url + '/' + str(language_code)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Request failed.")
        return

    data = response.json()
    
    return data

##############################################################################
#################### APIs - Players & PlayerIds ##############################
##############################################################################

# the most useful endpoint
@valid_session_check
def get_player(session_id=None, player_name: str=None, portal_id: int=None):
    """
    Returns league and other high level data for a particular player.

    Parameters:
    - player_name (str): IGN of the player, not sure how to handle special characters
    - portal_id (int): Specifies the language return
    - (1) - Hirez | (5) - Steam | (9) - PS4 | (10) - XBOX | (22) - Switch | (25) - Discord | (28) - Epic |

    Returns:
    - Response as json; a list of dictionaries
    - Returns nothing if status code fails

    Data:
    - Various accurate stats on ranked modes, wins/losses, games played
    - Account merge data of players, creation date, last log in etc.
    - SHOWS ACTUAL TOTAL NUMBER OF HOURS SOMEONE HAS PLAYED

    Raises:
    - ValueError: If portal id is invald
    - TypeError: If player name is None or an empty string

    Notes:
    - Not sure what the difference between account_id and player_id is

    """
    if not (portal_id is None):
        try:
            if portal_id not in (1, 5, 9, 10, 22, 25, 28):
                raise ValueError("Invalid portal id")
        except ValueError as e:
            error = {
                "status" : "error",
                "message" : str(e)
            }
            return json.dumps(error)
    
    try:
        if (player_name is None) or (player_name == ""):
            raise TypeError("Expected a non-empty string for the player name.")
    except TypeError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)
    

    base_url = general_API_url(method="getplayer",session_id=session_id)
    
    url = base_url + '/' + str(player_name)

    if not (portal_id is None):
        url += '/' + str(portal_id)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Request failed.")
        return

    data = response.json()
    
    return data

#doesnt work for smite api, so i took out the decorator
def _get_player_batch(session_id=None, player_name: str=None, portal_id: int=1):
    """
    doesn't work :(
    """
    player_name="wow"
    player_name_list = ["1111111", "22222222", "33333333"]
    try:
        if portal_id not in (1, 5, 9, 10, 22, 25, 28):
            raise ValueError("Invalid portal id")
    except ValueError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)
    
    try:
        if (player_name is None) or (player_name == ""):
            raise TypeError("Expected a non-empty string for the player name.")
    except TypeError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)
    

    base_url = general_API_url(method="getplayerbatch",session_id=session_id)
    
    url = base_url + '/' #+ str(player_name)
    for index, player in enumerate(player_name_list):
        url += player
        if index < (len(player_name_list) - 1):
            url += ","
    print (url)
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Request failed.")
        return

    data = response.json()
    
    return data

#player id using hirez name
@valid_session_check
def get_player_id_by_name(session_id=None, player_name: str=None):
    """
    - Function returns a list of Hi-Rez playerId values (expected list size = 1) for playerName provided.  
    - The playerId returned is expected to be used in various other endpoints to represent the player/individual regardless of platform.

    Parameters:
    - player_name (str): IGN of the player, not sure how to handle special characters

    Returns:
    - Response as json
    - Returns nothing if status code fails

    Data:
    - "player_id": 
        "portal": 
        "portal_id": 
        "privacy_flag":

    Raises:
    - TypeError: If player name is None or an empty string

    Notes:
    - Not sure what the difference between account_id and player_id is

    """
    try:
        if (player_name is None) or (player_name == ""):
            raise TypeError("Expected a non-empty string for the player name.")
    except TypeError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)
    

    base_url = general_API_url(method="getplayeridbyname",session_id=session_id)
    
    url = base_url + '/' + str(player_name)

    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Request failed.")
        return

    data = response.json()
    
    return data

#player id using non-hirez unique identifiers
@valid_session_check
def get_playerid_by_portal_userid(session_id=None, portal_id:int =None, portalUSER_id: str=None):
    """
    - Function returns a list of Hi-Rez playerId values (expected list size = 1) for {portalId}/{portalUserId} combination provided.
    - The playerId returned is expected to be used in various other endpoints to represent the player/individual regardless of platform.

    Parameters:
    - portal_id (int): Specifies the language return
    - (1) - Hirez | (5) - Steam | (9) - PS4 | (10) - XBOX | (22) - Switch | (25) - Discord | (28) - Epic |
    - PortalUserId- The (usually) 3rd-Party identifier for a Portal. | Examples:  Steam ID, PS4 GamerTag, Xbox GamerTag, Switch GamerTag.

    Returns:
    - Response as json
    - Returns nothing if status code fails

    Data:
    - "player_id": 
        "portal": 
        "portal_id": 
        "privacy_flag":

    Raises:
    - ValueError: If portal id is invald
    - TypeError: If player name is None or an empty string

    Notes:

    """
    try:
        if portal_id not in (1, 5, 9, 10, 22, 25, 28):
            raise ValueError("Invalid portal id")
    except ValueError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)
    
    try:
        if (portalUSER_id is None) or (portalUSER_id == ""):
            raise TypeError("Expected a non-empty string for the player name.")
    except TypeError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)
    

    base_url = general_API_url(method="getplayeridbyportaluserid",session_id=session_id)
    
    url = base_url + '/' + str(portal_id)

    
    url += '/' + str(portalUSER_id)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Request failed.")
        return

    data = response.json()
    
    return data

#cant get this to work unfort
def _get_playerid_by_gamertag(session_id=None, portal_id:int =None, gamertag_name: str=None):
    """
    - Function returns a list of Hi-Rez playerId values (expected list size = 1) for {portalId}/{portalUserId} combination provided.
    - The playerId returned is expected to be used in various other endpoints to represent the player/individual regardless of platform.

    Parameters:
    - portal_id (int): Specifies the language return
    - (1) - Hirez | (5) - Steam | (9) - PS4 | (10) - XBOX | (22) - Switch | (25) - Discord | (28) - Epic |
    - PortalUserId- The (usually) 3rd-Party identifier for a Portal. | Examples:  Steam ID, PS4 GamerTag, Xbox GamerTag, Switch GamerTag.

    Returns:
    - Response as json
    - Returns nothing if status code fails

    Data:
    - "player_id": 
        "portal": 
        "portal_id": 
        "privacy_flag":

    Raises:
    - ValueError: If portal id is invald
    - TypeError: If player name is None or an empty string

    Notes:
    - Can't get it to work, took out validation decorator
    """
    try:
        if portal_id not in (1, 5, 9, 10, 22, 25, 28):
            raise ValueError("Invalid portal id")
    except ValueError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)
    
    try:
        if (gamertag_name is None) or (gamertag_name == ""):
            raise TypeError("Expected a non-empty string for the player name.")
    except TypeError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)
    

    base_url = general_API_url(method="getplayeridsbygamertag",session_id=session_id)
    
    url = base_url + '/' + str(portal_id)

    
    url += '/' + str(gamertag_name)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Request failed.")
        return

    data = response.json()
    
    return data


##############################################################################
########################## APIs - PlayerId Info ##############################
##############################################################################

#what are friends
@valid_session_check
def get_friends(session_id=None, player_name=None):
    """
    Returns the Smite User names of each of the player's friends.  [PC only]


    Parameters:
    - player_name (str): IGN of the player, not sure how to handle special characters

    Returns:
    - Response as json; a list of dictionaries
    - Returns nothing if status code fails

    Data:
    - "friend_flags":"1" - Currently Friends, "2" - Outgoing, "32" - Blocked
    - "portal_id" : "1" - Probably Standalone Client, "5" - Steam, "9" - ???
    - "player_id" - unique per player

    Notes:
    - Not sure what the difference between account_id and player_id is

    """
    
    try:
        if (player_name is None) or (player_name == ""):
            raise TypeError("Expected a non-empty string for the player name.")
    except TypeError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)


    base_url = general_API_url(method="getfriends",session_id=session_id)
    
    url = base_url + '/' + str(player_name)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Request failed.")
        return

    data = response.json()
    
    return data

#see if someone is a 1 trick
@valid_session_check
def get_god_ranks(session_id=None, player_name=None):
    """
    Returns the Rank and Worshippers value for each God a player has played.


    Parameters:
    - player_name (str): IGN of the player, not sure how to handle special characters

    Returns:
    - Response as json; a list of dictionaries
    - Returns nothing if status code fails

    Data:
    - "Assists": 
        "Deaths":
        "Kills":
        "Losses":
        "MinionKills": 
        "Rank": 
        "Wins":
        "Worshippers": 
        "god": 
        "god_id": 
        "player_id":

    Notes:
    - Not sure what the difference between account_id and player_id is

    """
    
    try:
        if (player_name is None) or (player_name == ""):
            raise TypeError("Expected a non-empty string for the player name.")
    except TypeError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)


    base_url = general_API_url(method="getgodranks",session_id=session_id)
    
    url = base_url + '/' + str(player_name)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Request failed.")
        return

    data = response.json()
    
    return data

#could probably use this in a discord bot
@valid_session_check
def get_player_acievements(session_id=None, player_id=None):
    """
    Returns select achievement totals (Double kills, Tower Kills, First Bloods, etc) for the specified playerId.

    Parameters:
    - player_name (str): MUST USE PLAYER ID

    Returns:
    - Response as json; a list of dictionaries
    - Returns nothing if status code fails

    Data:
    - All achievements shown on the accolades screen in smite

    Notes:
    - Does not show total match types played

    """
    
    try:
        if (player_id is None) or (player_id == ""):
            raise TypeError("Expected a non-empty string for the player name.")
    except TypeError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)


    base_url = general_API_url(method="getplayerachievements",session_id=session_id)
    
    url = base_url + '/' + str(player_id)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Request failed.")
        return

    data = response.json()
    
    return data

#are the friends online ?
@valid_session_check
def get_player_status(session_id=None, player_id=None):
    """
    Returns player status


    Parameters:
    - player_name (str): MUST USE PLAYER ID

    Returns:
    - Response as json; a list of dictionaries
    - Returns nothing if status code fails

    Data:
    - 0 - Offline
        1 - In Lobby  (basically anywhere except god selection or in game)
        2 - god Selection (player has accepted match and is selecting god before start of game)
      	3 - In Game (match has started)
      	4 - Online (player is logged in, but may be blocking broadcast of player state)
	    5 - Unknown (player not found)


    Notes:
    - Everything is empty or '0' when player is offline

    """
    
    try:
        if (player_id is None) or (player_id == ""):
            raise TypeError("Expected a non-empty string for the player name.")
    except TypeError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)


    base_url = general_API_url(method="getplayerstatus",session_id=session_id)
    
    url = base_url + '/' + str(player_id)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Request failed.")
        return

    data = response.json()
    
    return data

# Games in your recents
@valid_session_check
def get_match_history(session_id=None, player_id=None):
    """
    Gets recent matches and high level match statistics for a particular player


    Parameters:
    - player_id (str): MUST USE PLAYER ID

    Returns:
    - Response as json; a list of dictionaries
    - Returns nothing if status code fails

    Data:
    - A little more than basic data about player's recent matches
    - Player's items, gold, w/l, dmg, mit, etc.
    - Includes gamemode, bans, tix remaining


    Notes:
    - "first_ban_side" is empty when the first ban is skipped (cringe)
    - INCLUDES MOTD!!!!!
    

    """
    
    try:
        if (player_id is None) or (player_id == ""):
            raise TypeError("Expected a non-empty string for the player name.")
    except TypeError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)


    base_url = general_API_url(method="getmatchhistory",session_id=session_id)
    
    url = base_url + '/' + str(player_id)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Request failed.")
        return

    data = response.json()
    
    return data

#one of my new favorite endpoints
@valid_session_check
def get_queue_stats(session_id= None, player_id = None, queue = None):
    """
    Returns match summary statistics for a (player, queue) combination grouped by gods played.


    Parameters:
    - player_id (str): MUST USE PLAYER ID
    - queue (int): Specifies the gamemode 
    

    Data:
    - Returns god data for specific game mode; time played, last played, kda etc.

    Notes:
    - VERY USEFUL AND COOL

    Returns:
    - Response result as json
    - Returns nothing if status code fails


    Raises:
    - ValueError: If invalid queue code is entered
    """
    # try:
    #     if queue not in (440, 450, 451, 468):
    #         raise ValueError("Invalid Queue")
    # except ValueError as e:
    #     error = {
    #         "status" : "error",
    #         "message" : str(e)
    #     }
    #     return json.dumps(error)
    
    try:
        if (player_id is None) or (player_id == ""):
            raise TypeError("Expected a non-empty string for the player name.")
    except TypeError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)

    base_url = general_API_url(method="getqueuestats",session_id=session_id)
    
    url = base_url + '/' + str(player_id) + '/' + str(queue)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Get God Leaderboard Request failed.")
        return

    data = response.json()
    
    return data

#one of my new favorite endpoints as a BATCH
@valid_session_check
def get_queue_stats_batch(session_id=None, player_id = None, queue_list: list = None):
    """
    Returns BATCH match summary statistics for a (player, queue) combination grouped by gods played.


    Parameters:
    - player_id (str): MUST USE PLAYER ID
    - queue (int): Specifies the gamemode 
    

    Data:
    - Returns god data for specific game mode; time played, last played, kda etc.

    Notes:
    - VERY USEFUL AND COOL

    Returns:
    - Response result as json
    - Returns nothing if status code fails


    Raises:
    - ValueError: If invalid queue code is entered
    """
    # try:
    #     if queue not in (440, 450, 451, 468):
    #         raise ValueError("Invalid Queue")
    # except ValueError as e:
    #     error = {
    #         "status" : "error",
    #         "message" : str(e)
    #     }
    #     return json.dumps(error)
    
    try:
        if (player_id is None) or (player_id == ""):
            raise TypeError("Expected a non-empty string for the player name.")
    except TypeError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)

    base_url = general_API_url(method="getqueuestatsbatch",session_id=session_id)
    
    url = base_url + '/' + str(player_id) + '/'

    # url = base_url + '/' #+ str(player_name)
    for index, queue in enumerate(queue_list):
        url += queue
        if index < (len(queue_list) - 1):
            url += ","
    
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Get God Leaderboard Request failed.")
        return

    data = response.json()
    
    return data

#for those pesky console players
@valid_session_check
def search_player(session_id=None, player_name=None):
    """
    Returns player_id values for all names and/or gamer_tags containing the “searchPlayer” string. 


    Parameters:
    - player_name (str): gamertag
    

    Data:
    - Returns god data for specific game mode; time played, last played, kda etc.

    Notes:
    - VERY USEFUL AND COOL

    Returns:
    - Response result as json
    - Returns nothing if status code fails


    Raises:
    - ValueError: If invalid queue code is entered
    """
    try:
        if (player_name is None) or (player_name == ""):
            raise TypeError("Expected a non-empty string for the player name.")
    except TypeError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)

    base_url = general_API_url(method="searchplayers",session_id=session_id)
    
    url = base_url + '/' + str(player_name) 
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: searchplayers Request failed.")
        return

    data = response.json()
    
    return data

##############################################################################
########################## APIs - Match Info #################################
##############################################################################

@valid_session_check
def _get_demo_details(session_id=None,match_id=None):
    """
    Gives some brief detail about a game; most likely used for spectator

    Parameters:
    - match_id (str): Can be inputted as an int

    Returns:
    - Response result as json; a list containing 1 dictionary
    - Returns nothing if status code fails

    Data:
    - Provides ban data, a 'queue', match duration, kills, and total gold for teams

    Notes:
    - According to the API, "Rarely used in lieu of getmatchdetails()"

    """
    # match_id = 1326174762 
    if not match_id:
        print("Requires a match ID")
        return 
    base_url = general_API_url(method="getdemodetails",session_id=session_id)
    url = base_url + '/' + str(match_id)
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Request failed.")
        return

    data = response.json()
    
    return data

@valid_session_check
def get_match_details(session_id=None, match_id=None):
    """
    Returns the statistics for a particular completed match.

    Parameters:
    - match_id (str): ID of the match

    Returns:
    - Response as json; a list of dictionaries
    - Returns nothing if status code fails

    Data:
    - Like a singular match history result, but for all players in lobby
    - Has multikill stat and time dead stat


    Notes:
    - "first_ban_side" is empty when the first ban is skipped (cringe)
    - INCLUDES MOTD!!!!!
    

    """
    
    try:
        if (match_id is None) or (match_id == ""):
            raise TypeError("Expected a non-empty string for the player name.")
    except TypeError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)


    base_url = general_API_url(method="getmatchdetails",session_id=session_id)
    
    url = base_url + '/' + str(match_id)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Request failed.")
        return

    data = response.json()
    
    return data

@valid_session_check
def get_match_details_BATCH(session_id=None, match_id_list: list=None):
    """
    Returns the statistics for a particular completed match.

    Parameters:
    - match_id (str): ID of the match

    Returns:
    - Response as json; a list of dictionaries
    - Returns nothing if status code fails

    Data:
    - Like a singular match history result, but for all players in lobby
    - Has multikill stat and time dead stat


    Notes:
    - "first_ban_side" is empty when the first ban is skipped (cringe)
    - INCLUDES MOTD!!!!!
    

    """
    
    try:
        if (match_id_list is None) or (match_id_list == []):
            raise TypeError("Expected a non-empty list of strings for the match id.")
    except TypeError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)


    base_url = general_API_url(method="getmatchdetailsbatch",session_id=session_id)
    
    url = base_url + '/' 

    for index, queue in enumerate(match_id_list):
        url += queue
        if index < (len(match_id_list) - 1):
            url += ","
    print (url)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Request failed.")
        return

    data = response.json()
    
    return data

#a lil confusing, but v good to track all matches played ever
####come back to this to buffer up
@valid_session_check
def get_matchids_by_queue(session_id=None,queue =None, date:str = None, hour:str = None):
    """
    Lists all Match IDs for a particular Match Queue

    Parameters:
    - queue (int/str): ID of the match
    - date (str): in the format “20171231” (for Dec 31, 2017, as an example)
    - hour (str): in the format of "h,mm" ; where h=hour/mm=minute and mm is optional


    Returns:
    - Response as json; a list of dictionaries
    - Returns nothing if status code fails

    Data:
    - Like a singular match history result, but for all players in lobby
    - Has multikill stat and time dead stat


    Notes:
    - Server side is 4 hours ahead of EST
    - Hour can be split in 10min intervals, for hour 3 to 3:09, you would specify {hour} as “3,00”
    

    """
    try:
        if (queue is None) or (queue == ""):
            raise TypeError("Expected a non-empty string for the player name.")
    except TypeError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)

    base_url = general_API_url(method="getmatchidsbyqueue",session_id=session_id)
    
    url = base_url + '/' + str(queue) + '/' + str(date) + '/' + str(hour)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: get_matchids_by_queue Request failed.")
        return

    data = response.json()
    
    return data

#the only endpoint to give live match details
@valid_session_check
def get_match_player_details(session_id=None, match_id=None):
    """
    Returns player information for a live match.

    Parameters:
    - match_id (str): ID of the match

    Returns:
    - Response as json; a list of dictionaries
    - Returns nothing if status code fails

    Data:
    - Like a singular match history result, but for all players in lobby
    - Has multikill stat and time dead stat


    Notes:
    - "first_ban_side" is empty when the first ban is skipped (cringe)
    - INCLUDES MOTD!!!!!
    

    """
    
    try:
        if (match_id is None) or (match_id == ""):
            raise TypeError("Expected a non-empty string for the player name.")
    except TypeError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)


    base_url = general_API_url(method="getmatchplayerdetails",session_id=session_id)
    
    url = base_url + '/' + str(match_id)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Request failed.")
        return

    data = response.json()
    
    return data

#This one seems like a very useless endpoint
@valid_session_check
def get_top_matches(session_id=None):
    """
    Lists the 50 most watched / most recent recorded matches.

    

    Parameters:
    - None needed

    Returns:
    - Response result as json; a list of dictionaries.
    - Returns nothing if status code fails

    Notes:
    - Similar to get_hirez_server_status() but only specifies patch

    """
 

    url = general_API_url(method='gettopmatches',session_id=session_id)
    response = requests.get(url)
    if response.status_code != 200:
        print("Error: Request failed.")
        return
 
    data = response.json()
  
    return data

##############################################################################
################### APIs - Leagues, Seasons & Rounds #########################
##############################################################################

@valid_session_check
def get_league_seasons(session_id=None, queue:int =None):
    """
    Provides a list of seasons and rounds (including the single active season) for a match queue.


    Parameters:
    
    - queue (int): Specifies the gamemode 
    

    Data:
    - Returns god data for specific game mode; time played, last played, kda etc.

    Notes:
    - VERY USEFUL AND COOL

    Returns:
    - Response result as json
    - Returns nothing if status code fails


    Raises:
    - ValueError: If invalid queue code is entered
    """
    try:
        if queue not in (440, 450, 451):
            raise ValueError("Invalid Queue")
    except ValueError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)
    
    # try:
    #     if (player_id is None) or (player_id == ""):
    #         raise TypeError("Expected a non-empty string for the player name.")
    # except TypeError as e:
    #     error = {
    #         "status" : "error",
    #         "message" : str(e)
    #     }
    #     return json.dumps(error)

    base_url = general_API_url(method="getleagueseasons",session_id=session_id)
    
    url = base_url + '/' + str(queue)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Get God Leaderboard Request failed.")
        return

    data = response.json()
    
    return data

@valid_session_check
def get_league_leaderboard(session_id= None, queue=None, tier: int=None, split=None):
    """
    Returns the top players for a particular league (as indicated by the queue/tier/split parameters). 

    Parameters:
    - queue (int/str): ID of the match
    - tier (int): Bronze V - I ==> (1 - 5) | Silver V - I ==> (6 - 10) | Gold V - I ==> (11 - 15) | Plat V - I ==> (16 - 20) | Dia V - I ==> (21 - 25) | Masters/GM ==> (26/27)
    - split (int): The ranked season's split


    Returns:
    - Response as json; a list of dictionaries
    - Returns nothing if status code fails

    Data:
    - Wins/Loss/Leaves of split
    - For non-private profiles: IGN, current joust/conq mmr


    Notes:
    - Doesn't save previous mmr pre split, only uses current one
    - Pretty useless endpoint since private profiles makes things hidden
    

    """
    try:
        if queue not in (440, 450, 451):
            raise ValueError("Invalid Queue")
    except ValueError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)
    
    
    try:
        if (tier < 1) or (tier > 27):
            raise ValueError("Tier must be [1-27].")
    except ValueError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)
    
    try:
        if split not in (1, 2, 3, 4):
            raise ValueError("Invalid Queue")
    except ValueError as e:
        error = {
            "status" : "error",
            "message" : str(e)
        }
        return json.dumps(error)
    

    base_url = general_API_url(method="getleagueleaderboard",session_id=session_id)
    
    url = base_url + '/' + str(queue) + '/' + str(tier) + '/' + str(split)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: getleagueleaderboard Request failed.")
        return

    data = response.json()
    
    return data


@valid_session_check
def get_esports(session_id=None):
    """
    Gives esport data for this season and previous seasons (not all)

    Parameters:
    - None needed

    Returns:
    - Response as json; a list of dictionaries
    - Returns nothing if status code fails

    Data:
    - Seems horribly outdated; Team names with team id's no where stated
    - Team id '1017' seems to be used as a possible "forfeit" or seed skip

    Notes:
    - According to the API, " An important return value is “match_status” which represents a match being scheduled (1), in-progress (2), or complete (3)"
    - This is untrue and should not be used, ['match_status'] contains "not-started" and "ended" values

    """
    url = general_API_url(method="getesportsproleaguedetails",session_id=session_id)
    
    response = requests.get(url)

    if response.status_code != 200:
        print("Error: Request failed.")
        return

    data = response.json()
    
    return data

@valid_session_check
def get_motd(session_id=None):
    """
    Returns information about the 20 most recent Match-of-the-Days.

    

    Parameters:
    - None needed

    Returns:
    - Response result as json; a list of dictionaries.
    - Returns nothing if status code fails

    Notes:
    - motd pog

    """
 

    url = general_API_url(method='getmotd',session_id=session_id)
    response = requests.get(url)
    if response.status_code != 200:
        print("Error: Request failed.")
        return
 
    data = response.json()
  
    return data


def extractGodData(godData):
    with open('gods_data_modified_NEW1.json', 'w') as f:
    # Write the gods data to the file
        firstAbilityCD_list = []
        for Gods in godData:
            #if not Gods['Name'].startswith('S'):
            if ( Gods['Name'][0].isalpha() ) and ( Gods['Name'][0].upper() >= 'A' and Gods['Name'][0].upper() <= 'Z' ):
                firstAbilityCD = {"Name" : Gods['Name'], "Cooldown" : Gods['Ability_1']['Description']['itemDescription']['cooldown'] ,"GodID" : Gods['id']}
                firstAbilityCD_list.append(firstAbilityCD)
            #json.dump(item['Name'], f, indent=2)
            #json.dump(item['Ability_1']['Description']['itemDescription']['cooldown'], f, indent=2)
            #f.write("\n")
        json.dump(firstAbilityCD_list, f, indent=2)
        print("Dumped")
        return
  
def GodID ():
    with open('gods_data_modified_NEW1.json', 'r') as GodFile:
        godids_list = []
        data = json.load(GodFile)
        for item in data:
        
            godids=int(item["GodID"])
            godids_list.append(godids)
        print(godids_list)
        print(godids_list[0])
    return godids_list

def Cooldowns(godname=None):
        # Load the JSON file
    with open('gods_data_modified_NEW1.json', 'r') as Godfile:
        data = json.load(Godfile)

    if godname is None:
        # Iterate through the dictionaries
        for item in data:
            cooldown = item['Cooldown']
            
            # Use a regular expression to match the numbers
            match = re.findall(r'\d+\.\d+', cooldown) # <--------- Need to figure out what this does again
            
            if match:
                # Extract the matched numbers
                cooldown_numbers = [float(num) for num in match]
                
                # Remove the 's' suffix
                #cooldown_numbers = [num[0] for num in cooldown_numbers]
                
                # Print the extracted numbers
                print(cooldown_numbers)
            else:
                print("No number found in Cooldown")
    else:
        for item in data:
            print (f'{str(item["Name"]).lower()} is the name from file. \t{str(godname).lower()} is the name from our input\n' )
            if (str(item["Name"])).lower() == str(godname).lower():
                cooldown = item['Cooldown']
                print (cooldown)
                match = re.findall(r'\d+\.\d+', cooldown)
                if match:
                    # Extract the matched numbers
                    cooldown_numbers = [float(num) for num in match]
                    
                    # Remove the 's' suffix
                    #cooldown_numbers = [num[0] for num in cooldown_numbers]
                    
                    # Print the extracted numbers
                    return (f"{item['Name']}'s cooldown for their first ability is **{cooldown}!**")
                elif cooldown == "":
                    return (f"No number found in {godname}'s Cooldown.")
                else: 
                    return (f"{item['Name']}'s cooldown for their first ability is a flat **{cooldown}!**")
        return ("God name is invalid.")
                    
def findingGodURL(godname):
    first_letter = str(godname[0]).upper()
    with open(f'CARDART_FOR_{first_letter}_GODS.json', 'r') as GodIconFile:
        data = json.load(GodIconFile)
        for item in data:
            print(item)
            if (str(item["god_name"])).lower() == str(godname).lower():
                return item["godIcon_URL"]
        
        return "[No icon]"
    
def findingGodCardArts(godname):
    cardart_list = []
    first_letter = str(godname[0]).upper()
    with open(f'CARDART_FOR_{first_letter}_GODS.json', 'r') as CardArtFile:
        data = json.load(CardArtFile)
        for item in data:
            print(item)
            if (str(item["god_name"])).lower() == str(godname).lower():
                if item["godSkin_URL"] != "":
                    cardart = item["godSkin_URL"]
                    cardart_list.append(cardart)
        
        return cardart_list

def extractGodURL(godSkinData):
    godlist = []
    if len(godSkinData) != 0:
        for letter in string.ascii_uppercase:
            with open(f'CARDART_FOR_{letter}_GODS.json', 'w') as f:
                for eachgod in godSkinData:
                    for each_god_item in eachgod: # <--- Chatgpt did this line and it fixed everything
                        #print (len(godSkinData))
                        
                        if (each_god_item['god_name'][0] == letter):
                            godlist.append(each_god_item)
                            #godSkinData.pop(-1)
                            #print(f"popped, this is " + each_god_item['god_name'] +" "+ each_god_item['skin_name'] +" for the " + letter + " letter. \n")
                        elif (godlist != []): #This conditional prevents extra [] in the output
                            #print (f'About to Write in the {letter} Gods.\n')
                            json.dump(godlist, f, indent=2)
                            godlist = []
                            print (f'Wrote in the {letter} Gods.\n')
                        if len(godSkinData) == 0: #I dont even think this part runs ever

                        #if eachgod == godSkinData[-1]:
                            # json.dump(godlist, f, indent=2)
                            # print (f'Wrote in the {letter} Gods. Super Done.\n')
                            # print(eachgod)
                            # print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                            # print(godSkinData[-1])
                            return
                    #godSkinData.pop(-1)
                #print (f'This is in the {letter} Gods.\n') 
                if (letter == 'Z'):
                    json.dump(godlist, f, indent=2)

                # Write the gods data to the file
            
                # json.dump(godSkinData, f, indent=2)
                # print("Dumped2")
    return



if __name__ == '__main__':

    # sessionId = valid_session_check()
    # # use the session ID to make API requests
    # godDataAPI = get_godsAPI(sessionId)
    # extractGodData(godDataAPI)
    # OurGodID = GodID()

    # #godSkinAPI = GodSkins(sessionId, OurGodID)
    # #extractGodURL (godSkinAPI)

    # MyData(sessionId)
    # Cooldowns()
    # response = api_ping()
    # print(response)
    # generate_session_id()
    # _test_session()
    # info = get_friends(player_name='Mujtabaa')
    # info = get_match_history(player_id='5952041')
    #info = get_match_details_BATCH(match_id_list=["1335043543","1335043531", "1335042724"])
    #info = get_match_details(match_id="1338225929")
    #info = get_gods()
    #info = get_matchids_by_queue(queue=451,date='20230926', hour="4,10")
    # info = get_friends(player_name="Háter")
    # # for profile in info:
    # #     if (profile['match_queue_id'] ==  451):
    # #         info2 = get_match_player_details(match_id=profile['Match'])
    # #         #print(f"The current match id is: {profile['Match']}")

    # #         print(f"Info 2: {info2}")
    # #         with open('cheatermatch3.json', 'w') as newfile:
    # #             json.dump(info2, newfile, indent=4)
    # with open('cheaterfriendsHαter.json', 'w') as newfile:
    #     json.dump(info, newfile, indent=4)
    wow = get_match_details(match_id='1363671177')
    #print (wow)
    with open('getmatchtest_june15.json', 'w') as newfile:
        json.dump(wow, newfile, indent=4)
    # info = get_motd()
    #info = MyData()
    # list123 = []
    # with open('response101.json', 'w') as file:
    #      for dictionary in info:
    #          for key in dictionary:
    #              if key != 'Name':
    #                  continue
    #              else:
    #                  list123.append(f"{dictionary[key]}")
    #      json.dump(list123, file, indent=4)

    # myinfo = get_matchids_by_queue(queue='451', date='20231115', hour='11,00')
    # for dictionary in myinfo:
    #     for key in dictionary:
    #             if key != 'Match':
    #                 continue
    #             print (dictionary[key])
    #print (info)
    # for list1 in info:
    #     for key in list1:
    #         print (key)
    #         print (info[0][key])
        