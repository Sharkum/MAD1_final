import datetime , calendar , os
from distutils.log import Log
from sqlalchemy import extract,func
import numpy as np
import matplotlib.pyplot as plt
from flask import Flask,request,render_template,redirect, url_for
from flask import current_app as app
from .models import *
    
# code to prevent the app from loading cached images/data and always load only the supplied data.
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)
def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)    

# Login page
@app.route('/', methods= ['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', fail=False)
    if request.method == 'POST':
        UserName = request.form.get('name')
        password = request.form.get('pass')
        user_entry = User.query.filter(User.UserName == UserName).first()
        if not user_entry:
            return render_template('login.html',user_not_found = True, fail=False)
        else:
            if(user_entry.Password == password):
                return redirect('/'+UserName+'/trackers')
            else:
                return render_template('login.html', user_not_found=False, fail=True)

# Signup page
@app.route('/signup', methods=['GET','POST'])
def signup():  
    if request.method == 'GET':
        return render_template('signup.html')
    if request.method == 'POST':
        new_entry = User(UserName =  request.form.get('cname'), Password = request.form.get('cpass'))
        db.session.add(new_entry)
        db.session.commit()
        return redirect('/'+request.form.get('cname') + '/trackers')

@app.route('/<string:UserName>/trackers', methods = ['GET'])
def userpage(UserName):
    if request.method == 'GET' :
        all_trackers =  Trackers.query.filter(Trackers.UserName == UserName).all()

        return render_template('userpage.html',name= UserName, tracker_list = all_trackers)

@app.route('/<string:Username>/add', methods=['GET', 'POST'])
def tracker_add(Username):
    if request.method == 'GET':
        return render_template('tracker_add.html', name = Username)
    if request.method == 'POST':
        tracker_name = request.form.get('tracker_name')
        tracker_desc = request.form.get('tracker_desc')
        new_tracker = Trackers(UserName = Username, Tracker_name = tracker_name,\
                                Description = tracker_desc, Active = 0)
        db.session.add(new_tracker)
        db.session.commit()
        return redirect('/'+ Username +'/'+tracker_name+'/logs')

@app.route('/<string:UserName>/<string:Tracker_name>/edit', methods=['GET', 'POST'])
def tracker_edit(UserName, Tracker_name):
    if request.method == 'GET':
        tracker_info = Trackers.query.filter(Trackers.Tracker_name == Tracker_name).filter(Trackers.UserName == UserName).first()
        return render_template('tracker_edit.html', name = UserName, tracker_name = Tracker_name, desc = tracker_info.Description)
    
    if request.method == 'POST':

        tracker_info = Trackers.query.filter(Trackers.Tracker_name == Tracker_name).filter(Trackers.UserName == UserName).first()
        new_tname = request.form.get('tracker_name')
        new_desc = request.form.get('tracker_desc')
        tracker_info.Tracker_name = new_tname
        tracker_info.Description = new_desc
        db.session.commit()

        logs_info = Logs.query.filter(Logs.Tracker_name == Tracker_name).filter(Logs.UserName == UserName).update({"Tracker_name":new_tname})
        db.session.commit()

        return redirect('/'+ UserName+ '/trackers')

@app.route('/<string:UserName>/<string:Tracker_name>/delete', methods = ['GET'])
def tracker_delete(UserName, Tracker_name):
    if request.method == 'GET':
        tracker_info = Trackers.query.filter(Trackers.Tracker_name == Tracker_name).filter(Trackers.UserName == UserName).delete()
        log_info = Logs.query.filter(Logs.Tracker_name == Tracker_name).filter(Logs.UserName == UserName).delete()
        db.session.commit()

        return redirect('/'+ UserName+ '/trackers')

# Shows logs associated with a given user and tracker.
@app.route('/<string:UserName>/<string:Tracker_name>/logs', methods=['GET', 'POST'])
def logs_page(UserName, Tracker_name):
    if request.method == 'GET':

        logs_queried = Logs.query.filter(Logs.UserName == UserName).filter(Logs.Tracker_name == Tracker_name).all()
        logs_list = []
        for i in logs_queried:
            log_dic = i.__dict__
            log_dic['Last_modified'] = log_dic['Last_modified'][:16]
            log_dic['Date_created'] = log_dic['Date_created'][:16]
            logs_list.append([log_dic['Date_created'], log_dic['Value'], log_dic['Description'], log_dic['Last_modified'], log_dic['LogID']])
        
        return render_template('logs.html', logs_list= logs_list, name = UserName, tracker_name = Tracker_name)
    
    
    if request.method == 'POST':
        
        logs_queried = Logs.query.filter(Logs.UserName == UserName).filter(Logs.Tracker_name == Tracker_name)
        selected_period = int(request.form.get('period'))

        present_time = datetime.datetime.now()
        logs_thisyear = logs_queried.filter(extract('year',Logs.Date_created) == present_time.year)
        logs_thismonth = logs_thisyear.filter(extract('month',Logs.Date_created) == present_time.month)
        logs_thisweek = logs_thismonth.filter(extract('week',func.date(Logs.Date_created))== present_time.isocalendar().week)
        logs_today = logs_thisweek.filter(extract('day',Logs.Date_created) == present_time.day)

        logs_periodwise = [logs_today,logs_thisweek,logs_thismonth]
        logs_list = []
        logs_intime = logs_periodwise[selected_period].all()
        
        def new(x,y,days):
            newy = [[] for i in range(days)]
            for i in range(x.shape[0]):
                newy[x[i]].append(int(y[i])) 
            for i in range(len(newy)):
                if newy[i]:
                    newy[i] = sum(newy[i])/len(newy[i])
                else:
                    newy[i]=0
            y = np.array(newy)
            return y

        def saveplot(y,original_ticks, new_ticks, xlabel):
            fig = plt.figure()
            _ = plt.plot(range(1,len(y)+1),y)
            plt.xticks(original_ticks, new_ticks)
            plt.ylabel('Average of values by '+ xlabel)
            plt.xlabel(xlabel)
            plt.savefig('static/trendline.jpg')
            return 
        
        x,y = [],[]
        for i in logs_intime:
            log_dic = i.__dict__
            x.append(datetime.datetime.strptime(i.Date_created[:16],"%Y-%m-%d %H:%M"))
            y.append(i.Value)
            log_dic['Last_modified'] = log_dic['Last_modified'][:16]
            log_dic['Date_created'] = log_dic['Date_created'][:16]
            logs_list.append([log_dic['Date_created'], log_dic['Value'], log_dic['Description'], log_dic['Last_modified'], log_dic['LogID']])

        x = np.array(x)
        y = np.array(y)
        
        if selected_period == 0:
            midnight = present_time.replace(hour=0, minute=0, second=0, microsecond=0)
            if x.shape[0]:
                x = np.apply_along_axis(lambda z:z[0].seconds//3600-1,axis=1,arr=(x-midnight).reshape(-1,1))
                y = new(x,y,24)
                saveplot(y,range(1,25,2),range(1,25,2), "Hours")
            else:
                saveplot([0 for i in range(1,25)],range(0,24,2),range(1,25,2),"Hours")
        
        if selected_period == 1:
            if x.shape[0]:
                weekstart = present_time - datetime.timedelta(days=present_time.weekday())
                x = np.apply_along_axis(lambda z :z[0].days+1,axis=1, arr = (x-weekstart).reshape(-1,1))
                y = new(x,y,7)
                saveplot(y, range(1,8), ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],"Weekday")
            else:
                saveplot([0 for i in range(1,8)], range(1,8), [ 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],"Weekday")
        
        if selected_period ==2:
            if x.shape[0]:
                x = np.apply_along_axis(lambda z:z[0].day-1,axis=1,arr=(x).reshape(-1,1))
                days_in_month = calendar.monthrange(present_time.year, present_time.month)[1]
                y = new(x,y,days_in_month)
                saveplot(y, range(1,days_in_month,2), range(1,days_in_month,2),"Day of this month")
            else:
                saveplot([0 for i in range(days_in_month)], range(1,days_in_month,2), range(1,days_in_month,2),"Day of this month")
        
        return render_template('logs.html', logs_list=logs_list, name = UserName, tracker_name = Tracker_name)

@app.route('/<string:UserName>/<string:Tracker_name>/logs/add', methods=['GET', 'POST'])
def add_log(UserName, Tracker_name):

    if request.method == 'GET':
        
        present_time = datetime.datetime.now()
        present_datetime = present_time.strftime ("%Y-%m-%dT%H:%M")
        return render_template('log_add.html', name = UserName, present_datetime = present_datetime, tracker_name = Tracker_name)

    if request.method == 'POST':
        
        new_time = request.form.get('date_created').replace('T',' ')
        new_datetime = datetime.datetime.strptime(new_time, "%Y-%m-%d %H:%M")

        new_log = Logs( UserName = UserName, \
                        Tracker_name = Tracker_name, \
                        Date_created = new_datetime.replace(second = 0),\
                        Last_modified = datetime.datetime.now().replace(second = 0), \
                      Value = request.form.get('value'),\
                      Description =request.form.get('desc'))
        
        db.session.add(new_log)
        db.session.commit()
        
        tracker_info = Trackers.query.filter(Trackers.UserName == UserName).filter(Trackers.Tracker_name == Tracker_name).first()
        tracker_info.Active += 1
        db.session.add(tracker_info)
        db.session.commit()

        return redirect('/'+ UserName+ '/' + Tracker_name + '/logs')

@app.route('/<string:UserName>/<string:Tracker_name>/logs/<int:LogID>/delete', methods=['GET'])
def log_delete(UserName,Tracker_name, LogID):
    if request.method == 'GET' :
        Log_entry = Logs.query.filter(Logs.LogID == LogID)
        if Log_entry.first() != []:
            deleted = Log_entry.delete()
            db.session.commit()
            tracker_info = Trackers.query.filter(Trackers.Tracker_name == Tracker_name).filter(Trackers.UserName == UserName).first()
            tracker_info.Active -= 1
            db.session.add(tracker_info)
            db.session.commit()
        return redirect('/'+ UserName+'/'+ Tracker_name+'/logs')

@app.route('/<string:UserName>/<string:Tracker_name>/logs/<int:LogID>/edit', methods=['GET', 'POST'])
def log_edit(UserName,Tracker_name, LogID):
    if request.method == 'GET':
        
        log_entry = Logs.query.filter(Logs.LogID == LogID).first()
        date_created = log_entry.Date_created.replace(' ', 'T')[:-3]
        
        return render_template('log_edit.html',log = log_entry, name = UserName,\
             lid = LogID, date_created = date_created, tracker_name = Tracker_name)
    
    if request.method == 'POST':
        
        log_entry = Logs.query.filter(Logs.LogID == LogID).first()
        new_date = request.form.get('date_created').replace('T',' ')
        
        log_entry.Date_created = datetime.datetime.strptime(new_date, "%Y-%m-%d %H:%M")
        log_entry.Value = request.form.get('value')
        log_entry.Description  = request.form.get('desc')
        log_entry.Last_modified = datetime.datetime.now().replace(second = 0)

        db.session.commit()

        return redirect('/'+ UserName+'/'+Tracker_name+'/logs')