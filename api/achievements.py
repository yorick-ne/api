from faf.api.achievement_schema import AchievementSchema
from faf.api.player_achievement_schema import PlayerAchievementSchema
from flask_jwt import jwt_required, current_identity
from api import *
import faf.db as db
from api.query_commons import fetch_data

MAX_PAGE_SIZE = 1000

ACHIEVEMENTS_TABLE = """achievement_definitions ach
                LEFT OUTER JOIN messages name_langReg
                    ON ach.name_key = name_langReg.key
                        AND name_langReg.language = %(language)s
                        AND name_langReg.region = %(region)s
                LEFT OUTER JOIN messages name_lang
                    ON ach.name_key = name_lang.key
                        AND name_lang.language = %(language)s
                LEFT OUTER JOIN messages name_def
                    ON ach.name_key = name_def.key
                        AND name_def.language = 'en'
                        AND name_def.region = 'US'
                LEFT OUTER JOIN messages desc_langReg
                    ON ach.description_key = desc_langReg.key
                        AND desc_langReg.language = %(language)s
                        AND desc_langReg.region = %(region)s
                LEFT OUTER JOIN messages desc_lang
                    ON ach.description_key = desc_lang.key
                        AND desc_lang.language = %(language)s
                LEFT OUTER JOIN messages desc_def
                    ON ach.description_key = desc_def.key
                        AND desc_def.language = 'en'
                        AND desc_def.region = 'US'"""

ACHIEVEMENT_SELECT_EXPRESSIONS = {
    'id': 'ach.id',
    'type': 'ach.type',
    'order': 'ach.order',
    'total_steps': 'ach.total_steps',
    'revealed_icon_url': 'ach.revealed_icon_url',
    'unlocked_icon_url': 'ach.unlocked_icon_url',
    'experience_points': 'ach.experience_points',
    'initial_state': 'ach.initial_state',
    'name': 'COALESCE(name_langReg.value, name_lang.value, name_def.value)',
    'description': 'COALESCE(desc_langReg.value, desc_lang.value, desc_def.value)',
}

PLAYER_ACHIEVEMENT_SELECT_EXPRESSIONS = {
    'id': 'id',
    'achievement_id': 'achievement_id',
    'state': 'state',
    'current_steps': 'current_steps',
    'create_time': 'create_time',
    'update_time': 'update_time'
}


@app.route('/achievements')
def achievements_list():
    """Lists all achievement definitions.

    HTTP Parameters::

        language    string  The preferred language to use for strings returned by this method
        region      string  The preferred region to use for strings returned by this method

    :return:
        If successful, this method returns a response body with the following structure::

            {
              "updated_achievements": [
                {
                  "id": string,
                  "name": string,
                  "description": string,
                  "type": string,
                  "total_steps": integer,
                  "initial_state": string,
                  "experience_points": integer,
                  "revealed_icon_url": string,
                  "unlocked_icon_url": string
                }
              ]
            }
    """
    language = request.args.get('language', 'en')
    region = request.args.get('region', 'US')

    return fetch_data(AchievementSchema(), ACHIEVEMENTS_TABLE, ACHIEVEMENT_SELECT_EXPRESSIONS, MAX_PAGE_SIZE, request,
                      args={'language': language, 'region': region})


@app.route('/achievements/<achievement_id>')
def achievements_get(achievement_id):
    """Gets an achievement definition.

    HTTP Parameters::

        language    string  The preferred language to use for strings returned by this method
        region      string  The preferred region to use for strings returned by this method

    :param achievement_id: ID of the achievement to get

    :return:
        If successful, this method returns a response body with the following structure::

            {
              "id": string,
              "name": string,
              "description": string,
              "type": string,
              "total_steps": integer,
              "initial_state": string,
              "experience_points": integer,
              "revealed_icon_url": string,
              "unlocked_icon_url": string
            }
    """
    language = request.args.get('language', 'en')
    region = request.args.get('region', 'US')

    return fetch_data(AchievementSchema(), ACHIEVEMENTS_TABLE, ACHIEVEMENT_SELECT_EXPRESSIONS, MAX_PAGE_SIZE, request,
                      where='WHERE ach.id = %(id)s',
                      args={'id': achievement_id, 'language': language, 'region': region},
                      many=False)


@app.route('/achievements/<achievement_id>/increment', methods=['POST'])
@oauth.require_oauth('write_achievements')
def achievements_increment(achievement_id):
    """Increments the steps of the achievement with the given ID for the currently authenticated player.

    HTTP Parameters::

        steps string  The number of steps to increment

    :param achievement_id: ID of the achievement to increment

    :return:
        If successful, this method returns a response body with the following structure::

            {
              "current_steps": integer,
              "current_state": string,
              "newly_unlocked": boolean,
            }
    """
    steps = int(request.form.get('steps', 1))

    return increment_achievement(achievement_id, request.oauth.user.id, steps)


@app.route('/jwt/achievements/<achievement_id>/increment', methods=['POST'])
@jwt_required()
def jwt_achievements_increment(achievement_id):
    steps = int(request.values.get('steps', 1))

    return increment_achievement(achievement_id, current_identity.id, steps)


@app.route('/achievements/<achievement_id>/setStepsAtLeast', methods=['POST'])
@oauth.require_oauth('write_achievements')
def achievements_set_steps_at_least(achievement_id):
    """Sets the steps of an achievement. If the steps parameter is less than the current number of steps
     that the player already gained for the achievement, the achievement is not modified.

    HTTP Parameters::

        steps string  The number of steps to increment

    :param achievement_id: ID of the achievement to increment

    :return
        If successful, this method returns a response body with the following structure::

            {
              "current_steps": integer,
              "current_state": string,
              "newly_unlocked": boolean,
            }
    """
    steps = int(request.form.get('steps', 1))

    return set_steps_at_least(achievement_id, request.oauth.user.id, steps)


@app.route('/jwt/achievements/<achievement_id>/setStepsAtLeast', methods=['POST'])
@jwt_required()
def jwt_achievements_set_steps_at_least(achievement_id):
    steps = int(request.values.get('steps', 1))

    return set_steps_at_least(achievement_id, current_identity.id, steps)


@app.route('/achievements/<achievement_id>/unlock', methods=['POST'])
@oauth.require_oauth('write_achievements')
def achievements_unlock(achievement_id):
    """Unlocks an achievement for the currently authenticated player.

    :param achievement_id: ID of the achievement to unlock

    :return:
        If successful, this method returns a response body with the following structure::

            {
              "newly_unlocked": boolean,
            }
    """
    return unlock_achievement(achievement_id, request.oauth.user.id)


@app.route('/jwt/achievements/<achievement_id>/unlock', methods=['POST'])
@jwt_required()
def jwt_achievements_unlock(achievement_id):
    return unlock_achievement(achievement_id, current_identity.id)


@app.route('/achievements/<achievement_id>/reveal', methods=['POST'])
@oauth.require_oauth('write_achievements')
def achievements_reveal(achievement_id):
    """Reveals an achievement for the currently authenticated player.

    :param achievement_id: ID of the achievement to reveal

    :return:
        If successful, this method returns a response body with the following structure::

            {
              "current_state": string,
            }
    """
    return reveal_achievement(achievement_id, request.oauth.user.id)


@app.route('/jwt/achievements/<achievement_id>/reveal', methods=['POST'])
@jwt_required()
def jwt_achievements_reveal(achievement_id):
    return reveal_achievement(achievement_id, current_identity.id)


@app.route('/achievements/updateMultiple', methods=['POST'])
@oauth.require_oauth('write_achievements')
def achievements_update_multiple():
    """Updates multiple achievements for the currently authenticated player.

    HTTP Body:
        In the request body, supply data with the following structure::

            {
              "updates": [
                {
                    "achievement_id": string,
                    "update_type": string,
                    "steps": integer
                }
              ]
            }

        ``updateType`` being one of "REVEAL", "INCREMENT", "UNLOCK" or "SET_STEPS_AT_LEAST"
        ``steps`` being mandatory only for update type `` INCREMENT`` and ``SET_STEPS_AT_LEAST``

    :return:
        If successful, this method returns a response body with the following structure::

            {
              "updated_achievements": [
                {
                  "achievement_id": string,
                  "current_state": string,
                  "current_steps": integer,
                  "newly_unlocked": boolean,
                }
              ],
            }
    """
    player_id = request.oauth.user.id

    updates = request.json['updates']
    return update_multiple(player_id, updates)


@app.route('/jwt/achievements/updateMultiple', methods=['POST'])
@jwt_required()
def jwt_achievements_update_multiple():
    updates = request.json['updates']
    return update_multiple(current_identity.id, updates)


@app.route('/players/<int:player_id>/achievements')
@oauth.require_oauth('read_achievements')
def achievements_list_player(player_id):
    """Lists the progress of achievements for a player.

    :param player_id: ID of the player.

    :return:
        If successful, this method returns a response body with the following structure::

            {
              "items": [
                {
                  "achievement_id": string,
                  "state": string,
                  "current_steps": integer,
                  "create_time": long,
                  "update_time": long
                }
              ]
            }
    """
    return fetch_data(PlayerAchievementSchema(), 'player_achievements', PLAYER_ACHIEVEMENT_SELECT_EXPRESSIONS,
                      MAX_PAGE_SIZE, request, where='WHERE player_id = %s', args=player_id)


def increment_achievement(achievement_id, player_id, steps):
    steps_function = lambda current_steps, new_steps: current_steps + new_steps
    return update_steps(achievement_id, player_id, steps, steps_function)


def set_steps_at_least(achievement_id, player_id, steps):
    steps_function = lambda current_steps, new_steps: max(current_steps, new_steps)
    return update_steps(achievement_id, player_id, steps, steps_function)


def update_steps(achievement_id, player_id, steps, steps_function):
    """Increments the steps of an achievement. This function is NOT an endpoint.

    :param achievement_id: ID of the achievement to increment
    :param player_id: ID of the player to increment the achievement for
    :param steps: The number of steps to increment
    :param steps_function: The function to use to calculate the new steps value. Two parameters are passed; the current
    step count and the parameter ``steps``

    :return:
        If successful, this method returns a dictionary with the following structure::

            {
              "current_steps": integer,
              "current_state": string,
              "newly_unlocked": boolean,
            }
    """
    achievement = achievements_get(achievement_id)['data']['attributes']
    if achievement['type'] != 'INCREMENTAL':
        raise InvalidUsage('Only incremental achievements can be incremented ({})'.format(achievement_id),
                           status_code=400)

    with db.connection:
        cursor = db.connection.cursor(db.pymysql.cursors.DictCursor)
        cursor.execute("""SELECT
                            current_steps,
                            state
                        FROM player_achievements
                        WHERE achievement_id = %s AND player_id = %s""",
                       (achievement_id, player_id))

        player_achievement = cursor.fetchone()

        new_state = 'REVEALED'
        newly_unlocked = False

        current_steps = player_achievement['current_steps'] if player_achievement else 0
        new_current_steps = steps_function(current_steps, steps)

        if new_current_steps >= achievement['total_steps']:
            new_state = 'UNLOCKED'
            new_current_steps = achievement['total_steps']
            newly_unlocked = player_achievement['state'] != 'UNLOCKED' if player_achievement else True

        cursor.execute("""INSERT INTO player_achievements (player_id, achievement_id, current_steps, state)
                        VALUES
                            (%(player_id)s, %(achievement_id)s, %(current_steps)s, %(state)s)
                        ON DUPLICATE KEY UPDATE
                            current_steps = VALUES(current_steps),
                            state = VALUES(state)""",
                       {
                           'player_id': player_id,
                           'achievement_id': achievement_id,
                           'current_steps': new_current_steps,
                           'state': new_state,
                       })

    return dict(current_steps=new_current_steps, current_state=new_state, newly_unlocked=newly_unlocked)


def unlock_achievement(achievement_id, player_id):
    """Unlocks a standard achievement. This function is NOT an endpoint.

    :param achievement_id: ID of the achievement to unlock
    :param player_id: ID of the player to unlock the achievement for

    :return:
        If successful, this method returns a dictionary with the following structure::

            {
              "newly_unlocked": boolean,
            }
    """
    newly_unlocked = False

    with db.connection:
        cursor = db.connection.cursor(db.pymysql.cursors.DictCursor)

        cursor.execute('SELECT type FROM achievement_definitions WHERE id = %s', achievement_id)
        achievement = cursor.fetchone()
        if achievement['type'] != 'STANDARD':
            raise InvalidUsage('Only standard achievements can be unlocked directly ({})'.format(achievement_id),
                               status_code=400)

        cursor.execute("""SELECT
                            state
                        FROM player_achievements
                        WHERE achievement_id = %s AND player_id = %s""",
                       (achievement_id, player_id))

        player_achievement = cursor.fetchone()

        new_state = 'UNLOCKED'
        newly_unlocked = not player_achievement or player_achievement['state'] != 'UNLOCKED'

        cursor.execute("""INSERT INTO player_achievements (player_id, achievement_id, state)
                        VALUES
                            (%(player_id)s, %(achievement_id)s, %(state)s)
                        ON DUPLICATE KEY UPDATE
                            state = VALUES(state)""",
                       {
                           'player_id': player_id,
                           'achievement_id': achievement_id,
                           'state': new_state,
                       })

    return dict(newly_unlocked=newly_unlocked)


def reveal_achievement(achievement_id, player_id):
    """Reveals an achievement.

    :param achievement_id: ID of the achievement to unlock
    :param player_id: ID of the player to reveal the achievement for

    :return:
        If successful, this method returns a response body with the following structure::

            {
              "current_state": string,
            }
    """
    with db.connection:
        cursor = db.connection.cursor(db.pymysql.cursors.DictCursor)
        cursor.execute("""SELECT
                            state
                        FROM player_achievements
                        WHERE achievement_id = %s AND player_id = %s""",
                       (achievement_id, player_id))

        player_achievement = cursor.fetchone()

        new_state = player_achievement['state'] if player_achievement else 'REVEALED'

        cursor.execute("""INSERT INTO player_achievements (player_id, achievement_id, state)
                        VALUES
                            (%(player_id)s, %(achievement_id)s, %(state)s)
                        ON DUPLICATE KEY UPDATE
                            state = VALUES(state)""",
                       {
                           'player_id': player_id,
                           'achievement_id': achievement_id,
                           'state': new_state,
                       })

    return dict(current_state=new_state)


def update_multiple(player_id, updates):
    result = dict(updated_achievements=[])

    for update in updates:
        achievement_id = update['achievement_id']
        update_type = update['update_type']

        update_result = dict(achievement_id=achievement_id)

        if update_type == 'REVEAL':
            reveal_result = reveal_achievement(achievement_id, player_id)
            update_result['current_state'] = reveal_result['current_state']
            update_result['current_state'] = 'REVEALED'
        elif update_type == 'UNLOCK':
            unlock_result = unlock_achievement(achievement_id, player_id)
            update_result['newly_unlocked'] = unlock_result['newly_unlocked']
            update_result['current_state'] = 'UNLOCKED'
        elif update_type == 'INCREMENT':
            increment_result = increment_achievement(achievement_id, player_id, update['steps'])
            update_result['current_steps'] = increment_result['current_steps']
            update_result['current_state'] = increment_result['current_state']
            update_result['newly_unlocked'] = increment_result['newly_unlocked']
        elif update_type == 'SET_STEPS_AT_LEAST':
            set_steps_at_least_result = set_steps_at_least(achievement_id, player_id, update['steps'])
            update_result['current_steps'] = set_steps_at_least_result['current_steps']
            update_result['current_state'] = set_steps_at_least_result['current_state']
            update_result['newly_unlocked'] = set_steps_at_least_result['newly_unlocked']

        result['updated_achievements'].append(update_result)

    return result