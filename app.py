from flask import Flask, jsonify, request, abort
from functools import wraps
from uuid import uuid4
import requests
import json
import subprocess

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from generator import *
from doprogram import compile_and_run

app = Flask(__name__)

URL = 'Slack Incoming Webhook URL'
LINE_ACCESS_TOKEN = 'LINE ACCESS TOKEN'

g = dict()

def sendToLine(program, to):
    s = emit(program)
    line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
    line_bot_api.push_message(to, TextSendMessage(s))

def sendToSlack(program):
    s = emit(program)
    requests.post(URL, data = json.dumps({
        'text': "```{}```".format(s),
        'username': 'TAKOYAKITABETAI',
        'icon_emoji': ':pencil:',
        'link_names': 1,
    }))

def session(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        body = request.get_json()
        if body is None:
            return abort(400, {"reason": "request has no body"})
        
        session_id = body.get("session_id", None)
        if session_id is None:
            return abort(400, {
                "result": "failed",
                "reason": "field session_id is required"
            })

        program = g.get(session_id)
        if program is None:
            return abort(400, {
                "result": "failed",
                "reason": "invalid session_id"
            })

        return f(body, program)
    return decorated_function

# Create new Program Seession
@app.route("/new", methods=['POST'])
def newSession():
    global g
    body = request.get_json()
    if body is None:
        return abort(400, {"reason": "request has no body"})
    
    session_id = body.get("session_id", None)
    if session_id is None:
        return abort(400, {
            "result": "failed",
            "reason": "field session_id is required"
        })
    g[session_id] = Program()

    return jsonify({
        "result": "ok",
        "session_id": session_id
    })

@app.route("/switch", methods=["POST"])
@session
def switch(req, program):
    expr = req.get("expr")
    if expr is None:
        return abort(400, {
            "result": "failed",
            "reason": "field expr is required"
        })

    program.switch(Id(expr))
    sendToLine(program, req['session_id'])
    sendToSlack(program)
    return jsonify({"result": "ok"})

@app.route("/case", methods=["POST"])
@session
def case(req, program):
    expr = req.get("expr")
    if expr is None:
        return abort(400, {
            "result": "failed",
            "reason": "field expr is required"
        })

    program.case(Id(expr))
    sendToLine(program, req['session_id'])
    sendToSlack(program)
    return jsonify({"result": "ok"})

@app.route("/default", methods=["POST"])
@session
def default(req, program):
    program.default()
    sendToLine(program, req['session_id'])
    sendToSlack(program)
    return jsonify({"result": "ok"})

@app.route("/assign", methods=["POST"])
@session
def assign(req, program):
    lhs = req.get("lhs")
    if lhs is None:
        return abort(400, {
            "result": "failed",
            "reason": "field lhs is required"
        })

    rhs = req.get("rhs")
    if rhs is None:
        return abort(400, {
            "result": "failed",
            "reason": "field rhs is required"
        })

    program.statement(Assign(Id(lhs), Id(rhs)))
    sendToSlack(program)
    sendToLine(program, req['session_id'])
    return jsonify({"result": "ok"})


@app.route("/break", methods=["POST"])
@session
def break_(req, program):
    return jsonify({"result": "ok"})

@app.route("/close", methods=["POST"])
@session
def close(req, program):
    program.doclose()
    sendToSlack(program)
    sendToLine(program, req['session_id'])
    return jsonify({"result": "ok"})

@app.route("/if", methods=["POST"])
@session
def if_(req, program):
    expr = req.get("expr")
    if expr is None:
        return abort(400, {
            "result": "failed",
            "reason": "field expr is required"
        })

    program.if_(Id(expr))
    sendToSlack(program)
    sendToLine(program, req['session_id'])
    return jsonify({"result": "ok"})

@app.route("/elseif", methods=["POST"])
@session
def elseif(req, program):
    expr = req.get("expr")
    if expr is None:
        return abort(400, {
            "result": "failed",
            "reason": "field expr is required"
        })

    program.elseif(Id(expr))
    sendToSlack(program)
    sendToLine(program, req['session_id'])
    return jsonify({"result": "ok"})

@app.route("/else", methods=["POST"])
@session
def else_(req, program):
    program.else_()
    sendToSlack(program)
    sendToLine(program, req['session_id'])
    return jsonify({"result": "ok"})

@app.route("/for", methods=["POST"])
@session
def for_(req, program):
    var = req.get("id")
    if var is None:
        return abort(400, {
            "result": "failed",
            "reason": "field id is required"
        })
    start = req.get("start")
    if start is None:
        return abort(400, {
            "result": "failed",
            "reason": "field start is required"
        })
    end = req.get("end")
    if end is None:
        return abort(400, {
            "result": "failed",
            "reason": "field end is required"
        })

    program.for_(Id(var), Id(start), Id(end))
    sendToSlack(program)
    sendToLine(program, req['session_id'])
    return jsonify({"result": "ok"})

@app.route("/print", methods=["POST"])
@session
def print_(req, program):
    expr = req.get("expr")
    if expr is None:
        return abort(400, {
            "result": "failed",
            "reason": "field expr is required"
        })

    program.statement(Print(Id(expr)))
    sendToLine(program, req['session_id'])
    sendToSlack(program)
    return jsonify({"result": "ok"})

@app.route("/printi", methods=["POST"])
@session
def printi(req, program):
    expr = req.get("expr")
    if expr is None:
        return abort(400, {
            "result": "failed",
            "reason": "field expr is required"
        })

    program.statement(Printi(Id(expr)))
    sendToLine(program, req['session_id'])
    sendToSlack(program)
    return jsonify({"result": "ok"})


@app.route("/done", methods=["POST"])
@session
def done(req, program):
    sendToSlack(program)
    sendToLine(program, req['session_id'])
    g.pop(req['session_id'])
    return jsonify({"result": "ok"})

@app.route("/exec", methods=["POST"])
@session
def ex(req, program):
    s = emit(program)
    output, ok = compile_and_run(s)
    if ok:
        return jsonify({
            "result": "ok",
            "lines": output
        })
    else:
        return jsonify({
            "result": "failed",
            "reason": output
        })

if __name__ == '__main__':
    app.run(host="localhost", port=5000, debug=True)
