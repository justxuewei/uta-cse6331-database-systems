import re
from datetime import datetime, timedelta

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.config['DEBUG'] = True

###### Variables ######

# game1 status: "Closed", "Waiting", "Started"
game1_status = "Closed"
game1_closed_time = datetime.now()
game1_player1 = None
game1_player2 = None
game1_current_player = None
game1_min = None
game1_max = None
game1_remaining = None

game2_status = "Closed"
game2_closed_time = datetime.now()
game2_player1_paragraph = None
game2_player2_paragraph = None
game2_words = None
game2_result = None


###### Utils ######


def message_page(msg):
    return render_template("message.html", msg=msg)


def results_page(data, msg, **kwargs):
    return render_template("results.html", data=data, msg=msg, attachment=kwargs)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/queries")
def queries():
    return render_template("queries.html")


def game2_update_result():
    global game2_result, game2_words, game2_player1_paragraph, game2_player2_paragraph
    if game2_result:
        return
    player1_result = []
    player2_result = []
    player1_hit_times = 0
    player2_hit_times = 0
    if game2_player1_paragraph:
        for word in game2_words:
            times = len(re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE).findall(game2_player1_paragraph))
            player1_result.append("\"{}\" {} times".format(word, times))
            player1_hit_times += times

    if game2_player2_paragraph:
        for word in game2_words:
            times = len(re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE).findall(game2_player2_paragraph))
            player2_result.append("\"{}\" {} times".format(word, times))
            player2_hit_times += times

    if player1_hit_times > player2_hit_times:
        game2_result = "Player 1 wins; "
    elif player1_hit_times < player2_hit_times:
        game2_result = "Player 2 wins; "
    else:
        game2_result = "No winner; "
    
    game2_result += "player1: {}; player2: {}".format(", ".join(player1_result), ", ".join(player2_result))


###### Pages ######


@app.route("/game1/admin")
def page_game1_admin():
    return render_template("game1_admin.html")


@app.route("/game1/player1")
def page_game1_player1():
    return render_template("game1_player1.html")


@app.route("/game1/player2")
def page_game1_player2():
    return render_template("game1_player2.html")


@app.route("/game2/admin")
def page_game2_admin():
    return render_template("game2_admin.html")


@app.route("/game2/player1")
def page_game2_player1():
    return render_template("game2_player1.html")


@app.route("/game2/player2")
def page_game2_player2():
    return render_template("game2_player2.html")

###### APIs ######


# role: public
@app.route("/game1/status")
def api_game1_status():
    global game1_status
    global game1_closed_time
    global game1_min, game1_max, game1_remaining
    remaining_time = datetime.timestamp(
        game1_closed_time) - datetime.timestamp(datetime.now())
    if remaining_time <= 0:
        if game1_status == "Started":
            game1_status = "Closed"
        remaining_time = 0
    if game1_status != "Started":
        remaining_time = 0
    return jsonify({
        "status": game1_status,
        "remaining_time": remaining_time,
        "min": game1_min,
        "max": game1_max,
        "remaining": game1_remaining,
    })


# role: public
@app.route("/game1/players")
def api_game1_players():
    global game1_player1, game1_player2
    return jsonify({
        "player1": game1_player1,
        "player2": game1_player2,
    })


# role: public
@app.route("/game1/current_player")
def api_game1_current_player():
    global game1_status, game1_current_player, game1_player1, game1_player2
    ret = None
    if game1_status != "Closed":
        ret = game1_current_player
    if ret == "player1":
        ret = game1_player1
    elif ret == "player2":
        ret = game1_player2
    return jsonify({
        "current_player": ret
    })

# role: admin


@app.route("/game1/prestarted")
def api_game1_prestarted():
    role = request.args.get("role")
    if not role or role != "admin":
        return jsonify({
            "msg": "you don't have permission to prestart the game",
        }), 500
    global game1_player1, game1_player2, game1_status, game1_current_player, game1_min, game1_max, game1_remaining
    game1_player1 = None
    game1_player2 = None
    game1_current_player = None
    game1_min = None
    game1_max = None
    game1_remaining = None
    game1_status = "Waiting"
    return jsonify({
        "msg": "success",
    })


# role: admin
@app.route("/game1/start")
def api_game1_start():
    role = request.args.get("role")
    if not role or role != "admin":
        return jsonify({
            "msg": "you don't have permission to prestart the game",
        }), 500
    try:
        min_value = int(request.args.get("min"))
        max_value = int(request.args.get("max"))
        start_value = int(request.args.get("start"))
        duration_value = int(request.args.get("duration"))
        player_value = request.args.get("player")
    except Exception as e:
        return jsonify({
            "msg": "invalid parameters, err = {}".format(e),
        }), 500
    print("min_value = {}, max_value = {}, start_value = {}, duration_value = {}".format(
        min_value, max_value, start_value, duration_value))
    global game1_player1, game1_player2, game1_status, game1_closed_time, game1_current_player, game1_min, game1_max, game1_remaining
    if min_value <= 0 or max_value <= 0 or start_value <= 0 or duration_value <= 0:
        return jsonify({
            "msg": "parameters should greater than zero",
        }), 500
    if min_value > max_value:
        return jsonify({
            "msg": "min should less than max",
        }), 500
    if not game1_player1 or not game1_player2:
        return jsonify({
            "msg": "players are not ready",
        }), 500
    if game1_status != "Waiting":
        return jsonify({
            "msg": "game can't be started due to current status",
        }), 500
    game1_status = "Started"
    game1_closed_time = datetime.now() + timedelta(seconds=duration_value)
    if not player_value:
        return jsonify({
            'msg': 'the player is required'
        }), 500
    if player_value != "player1" and player_value != "player2":
        return jsonify({
            'msg': 'the player is invalid, the possible values are "player1" or "player2"'
        }), 500
    game1_current_player = player_value
    game1_min = min_value
    game1_max = max_value
    game1_remaining = start_value
    return jsonify({
        "msg": "success",
    })


# role: admin
@app.route("/game1/close")
def api_game1_close():
    role = request.args.get("role")
    if not role or role != "admin":
        return jsonify({
            "msg": "you don't have permission to prestart the game",
        }), 500
    global game1_player1, game1_player2, game1_status, game1_current_player, game1_min, game1_max, game1_remaining
    game1_player1 = None
    game1_player2 = None
    game1_current_player = None
    game1_min = None
    game1_max = None
    game1_remaining = None
    game1_status = "Closed"
    return jsonify({
        "msg": "success",
    })


# role: player
@app.route("/game1/join")
def api_game1_join():
    role = request.args.get("role")
    if not role or (role != "player1" and role != "player2"):
        return jsonify({
            "msg": "you don't have permission to join a game",
        }), 500
    name = request.args.get("name")
    if not name:
        return jsonify({
            "msg": "name is required"
        }), 500
    global game1_status, game1_player1, game1_player2
    if game1_status != "Waiting":
        return jsonify({
            "msg": "game is not in waiting status"
        }), 500
    if role == "player1":
        game1_player1 = name
    if role == "player2":
        game1_player2 = name
    return jsonify({
        "msg": "joined successfully"
    })


@app.route("/game1/player_submit")
def api_game1_player_submit():
    global game1_player1, game1_player2, game1_status, game1_current_player, game1_min, game1_max, game1_remaining
    role = request.args.get("role")
    if not role or (role != "player1" and role != "player2"):
        return jsonify({
            "msg": "you don't have permission to join a game",
        }), 500
    if role != game1_current_player:
        return jsonify({
            "msg": "it's not your turn"
        }), 500
    value = request.args.get("value")
    try:
        value = int(value)
    except:
        return jsonify({
            'msg': 'the value should be a integer'
        }), 500

    if value < game1_min or value > game1_max:
        return jsonify({
            'msg': 'the value should be between {} and {}'.format(game1_min, game1_max)
        }), 500
    result = game1_remaining - value
    if result < 0:
        return jsonify({
            'msg': 'the value should be less than {}'.format(game1_remaining)
        }), 500
    elif result == 0:
        if game1_current_player == 'player1':
            player_name = game1_player1
        else:
            player_name = game1_player2
        game1_player1 = None
        game1_player2 = None
        game1_current_player = None
        game1_min = None
        game1_max = None
        game1_remaining = None
        game1_status = "Closed"
        return jsonify({
            'msg': '{} loss the game'.format(player_name),
            'remaining': result,
        })
    else:
        if game1_current_player == 'player1':
            game1_current_player = 'player2'
        else:
            game1_current_player = 'player1'
        game1_remaining = result
        return jsonify({
            'remaining': result,
            'msg': 'continue',
        })

# role: public


@app.route("/game2/dashboard")
def api_game2_dashboard():
    global game2_closed_time, game2_status, game2_player1_paragraph, game2_player2_paragraph, game2_result, game2_words
    remaining_time = datetime.timestamp(
        game2_closed_time) - datetime.timestamp(datetime.now())
    if remaining_time <= 0:
        if game2_status == "Started":
            game2_status = "Closed"
            game2_update_result()
        remaining_time = 0
    if game2_status != "Started":
        remaining_time = 0
    words = game2_words
    if words:
        words = ",".join(words)
    return jsonify({
        "status": game2_status,
        "remaining_time": remaining_time,
        "player1_paragraph": game2_player1_paragraph,
        "player2_paragraph": game2_player2_paragraph,
        "result": game2_result,
        "words": words,
    })


# role: admin
@app.route("/game2/start")
def api_game2_start():
    role = request.args.get("role")
    if not role or role != "admin":
        return jsonify({
            "msg": "you don't have permission to prestart the game",
        }), 500
    global game2_status, game2_closed_time, game2_words, game2_player1_paragraph, game2_player2_paragraph, game2_result
    if game2_status != "Closed":
        return jsonify({
            'msg': 'the game is not in closed status'
        }), 500
    words_str = request.args.get("words")
    print(words_str)
    words = words_str.split(",")
    if len(words) < 1 or len(words) > 6:
        return jsonify({
            'msg': 'The length of words should be between 1 and 6',
        }), 500
    duration = request.args.get('duration')
    try:
        duration = int(duration)
    except Exception as e:
        return jsonify({
            'msg': 'The duration should be an integer',
        }), 500
    game2_status = "Started"
    game2_closed_time = datetime.now() + timedelta(seconds=duration)
    game2_words = words
    print(game2_words)
    game2_player1_paragraph = None
    game2_player2_paragraph = None
    game2_result = None
    return jsonify({
        'msg': 'success',
    })


# role: admin
@app.route("/game2/close")
def api_game2_stop():
    role = request.args.get("role")
    if not role or role != "admin":
        return jsonify({
            "msg": "you don't have permission to prestart the game",
        }), 500
    global game2_status, game2_closed_time, game2_words, game2_player1_paragraph, game2_player2_paragraph, game2_result
    game2_status = "Closed"
    game2_update_result()
    return jsonify({
        'msg': 'success',
    })


# role: player
@app.route("/game2/submit")
def api_game2_submit():
    role = request.args.get("role")
    if not role or (role != "player1" and role != "player2"):
        return jsonify({
            "msg": "you don't have permission to submit a result",
        }), 500
    global game2_status, game2_player1_paragraph, game2_player2_paragraph, game2_result, game2_words
    if game2_status != 'Started':
        return jsonify({
            'msg': 'The game is not started',
        }), 500
    paragraph = request.args.get("value")
    if not paragraph:
        return jsonify({
            'msg': 'paragraph is required'
        }), 500
    for word in game2_words:
        print('Started to check "{}"'.format(word))
        if not re.compile(r'\b({0})\b'.format(word), flags=re.IGNORECASE).search(paragraph):
            return jsonify({
                'msg': 'The word "{}" is not in the paragraph'.format(word),
            }), 500
    if role == 'player1':
        if game2_player1_paragraph:
            return jsonify({
                'msg': 'you have submitted a result',
            }), 500
        game2_player1_paragraph = paragraph
    else:
        if game2_player2_paragraph:
            return jsonify({
                'msg': 'you have submitted a result',
            }), 500
        game2_player2_paragraph = paragraph

    # update result
    if game2_player1_paragraph and game2_player2_paragraph:
        game2_update_result()
        if game2_result:
            game2_status = "Closed"

    return jsonify({
        'msg': 'success',
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
