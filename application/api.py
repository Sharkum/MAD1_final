from os import stat
from turtle import st
from xmlrpc.client import Marshaller
from flask import make_response, request
from flask_restful import Resource, Api, marshal_with, fields
from sqlalchemy import desc
from .database import db 
from .models import *
from werkzeug.exceptions import HTTPException
import json

class DefaultError(HTTPException):
    def __init__(self, status_code, desc):
        self.response = make_response('', status_code)
        self.description = "<p>"+desc+"</p>"

class Success(HTTPException):
    def __init__(self, status_code, msg):
        self.response = make_response(msg, status_code)

class BError(HTTPException):
    def __init__(self, status_code, errorcode, errormsg):
        message = {
  "error_code": errorcode,
  "error_message": errormsg
}
        self.response = make_response(json.dumps(message), status_code)

loginfo = {
    "datetime" : fields.String,
    "value" : fields.Integer,
    "notes" : fields.String
}
trackerinfo = {
    "tracker_name": fields.String,
    "tracker_type": fields.String,
    "tracker_settings": fields.String,
}
types = set(['numeric','multiple choice','other'])

class Users(Resource):
    def get(self, name):
        try:
            tracker_list = []
            current_user = user.query.filter(user.user_name == name).first()
        except:
            raise DefaultError(status_code=500, description='Internal Server Error ')
        if current_user:
            assignment_list = assignment.query.filter(assignment.user_id == current_user.user_id).all()
            if assignment_list:
                for i in assignment_list:
                    current_tracker = tracker.query.filter(tracker.tracker_id == i.tracker_id).first()
                    tracker_list.append(current_tracker.tracker_name)
                return {"trackers": tracker_list} 
            else:
                raise DefaultError(status_code=404, desc="No trackers found for the given user\n")

        else:
            raise DefaultError(status_code=404, desc="User doesn't exist.\n")

class Trackers(Resource):
    @marshal_with(trackerinfo)
    def post(self):
        details = request.get_json()
        for i in trackerinfo.keys():
            if i not in details.keys():
                raise BError(status_code=400,errorcode="FLDSABSNT", errormsg="All the relevant details needed for a tracker must be provided.")
            if i == "tracker_settings":
                if type(details[i]) is list or not details[i]:
                    for j in details[i]:
                        if type(j) is not str:
                            raise BError(status_code=400, errorcode="BADINP", errormsg="All the settings must be strings")
                else:
                    raise BError(status_code=400, errorcode="BADINP", errormsg="The settings must be an array of strings")
            elif type(details[i]) is not str or details[i] == "":
                raise BError(status_code=400, errorcode="BADINP", errormsg=i + " must be a string and should not be empty")
            if i == "tracker_type" and details[i] not in types:
                raise BError(status_code=400, errorcode="BADTYPE", errormsg="The following is not a valid type of tracker")

        present = tracker.query.filter(tracker.tracker_name == details["tracker_name"]).all()
        if not present:
            new_tracker = tracker(tracker_name = details["tracker_name"], \
                              tracker_type = details["tracker_type"], \
                              tracker_settings = "tracker_settings")
            db.session.add(new_tracker)
            db.session.commit()
            return new_tracker
        else:
            raise BError(status_code=400,errorcode="DUP", errormsg="There already exists a tracker with the given name")

class Logs(Resource):
    @marshal_with(loginfo)
    def get(self, name, tracker_name):
        try:
            logs_list = []
            current_user = user.query.filter(user.user_name == name).first()
            current_tracker = tracker.query.filter(tracker.tracker_name == tracker_name).first()
        except:
            raise DefaultError(status_code=500, description='Internal Server Error ')
        if current_user and current_tracker:
            assignment_list = assignment.query.filter(assignment.tracker_id == current_tracker.tracker_id, \
                                                assignment.user_id == current_user.user_id).all()
            for i in assignment_list:
                logs_list.append(logs.query.filter(logs.log_id == i.log_id).first())

            return logs_list
        else:
            d ="" 
            if not current_user:
                d = d+ "User doesn't exist.\n"
            elif not current_tracker:
                d = d+ "Tracker doesn't exist.\n"
            raise DefaultError(status_code=404, desc=d)
    
    @marshal_with(loginfo)
    def post(self,tracker_name, name):
        try:
            current_tracker = tracker.query.filter(tracker.tracker_name == tracker_name).first()
            current_user = user.query.filter(user.user_name == name).first()
            details = request.get_json()
        except:
            raise DefaultError(status_code=500)
        for i in loginfo.keys():
            if i not in details.keys():
                raise BError(status_code=400,errorcode="FLDSABSNT", errormsg="All the relevant details needed for a tracker must be provided.")
            if i == 'notes':
                pass
            elif type(details[i]) is not str or details[i] == "":
                raise BError(status_code=400, errorcode="BADINP", errormsg=i + " must be a string and should not be empty")
        if current_user and current_tracker:
            new_log = logs(datetime = details['datetime'],\
                        value = details['value'],\
                        notes = details['notes'])
            db.session.add(new_log)
            db.session.commit()
            new_assignment = assignment(tracker_id = current_tracker.tracker_id,\
                                user_id = current_user.user_id,\
                                log_id = new_log.log_id)
            db.session.add(new_assignment)
            db.session.commit()
            return new_log
        else:
            d ="" 
            if not current_user:
                d = d+ "User doesn't exist.\n"
            elif not current_tracker:
                d = d+ "Tracker doesn't exist.\n"
            raise DefaultError(status_code=404, desc=d)
