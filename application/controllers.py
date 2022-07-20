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
        user_entry = User.query.filter(User.UserName == request.form.get('name'))\
                .filter(User.Password==request.form.get('pass')).all()
        if user_entry == []:
            return render_template('login.html',fail = True)
        else:
            return redirect('/'+UserName+'/logs')

# Signup page
@app.route('/signup', methods=['GET','POST'])
def signup():  
    if request.method == 'GET':
        return render_template('signup.html')
    if request.method == 'POST':
        new_entry = User(UserName =  request.form.get('cname'), Password = request.form.get('cpass'))
        db.session.add(new_entry)
        db.session.commit()
        return redirect('/'+request.form.get('cname') + '/logs')

# Shows logs associated with a given user.
@app.route('/<string:UserName>/logs', methods=['GET', 'POST'])
def logs_page(UserName):
    if request.method == 'GET':

        logs_queried = Logs.query.filter(Logs.UserName == UserName).all()
        logs_list = []
        for i in logs_queried:
            log_dic = i.__dict__
            log_dic['Last_modified'] = log_dic['Last_modified'][:16]
            log_dic['Date_created'] = log_dic['Date_created'][:16]
            logs_list.append([log_dic['Date_created'], log_dic['Value'], log_dic['Description'], log_dic['Last_modified'], log_dic['LogID']])
        return render_template('logs.html', logs_list= logs_list, name = UserName)
    
    
    if request.method == 'POST':
        
        selected_period = int(request.form.get('period'))

        present_time = datetime.datetime.now()
        logs_thisyear = Logs.query.filter(extract('year',Logs.Date_created) == present_time.year)
        logs_thismonth = logs_thisyear.filter(extract('month',Logs.Date_created) == present_time.month)
        logs_thisweek = logs_thismonth.filter(extract('week',func.date(Logs.Date_created))== present_time.isocalendar().week)
        logs_today = logs_thisweek.filter(extract('day',Logs.Date_created) == present_time.day)

        logs_periodwise = [logs_today,logs_thisweek,logs_thismonth]
        logs_list = []
        logs_intime = logs_periodwise[selected_period].filter(Logs.UserName == UserName).all()
        
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

        def saveplot(y):
            fig = plt.figure()
            _ = plt.plot(range(1,len(y)+1),y)
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
                x = np.apply_along_axis(lambda z:z[0].seconds//60,axis=1,arr=(x-midnight).reshape(-1,1))
                y = new(x,y,60*24)
                saveplot(y)
            else:
                saveplot([0 for i in range(60*24)])
        
        if selected_period == 1:
            if x.shape[0]:
                weekstart = present_time-datetime.timedelta(days=present_time.weekday())
                x = np.apply_along_axis(lambda z :z[0].days,axis=1, arr = (x-weekstart).reshape(-1,1))
                y = new(x,y,7)
                saveplot(y)
            else:
                saveplot([0 for i in range(7)])
        
        if selected_period ==2:
            if x.shape[0]:
                x = np.apply_along_axis(lambda z:z[0].day-1,axis=1,arr=(x).reshape(-1,1))
                y = new(x,y,calendar.monthrange(present_time.year, present_time.month)[1])
                saveplot(y)
            else:
                saveplot([0 for i in range(calendar.monthrange(present_time.year, present_time.month)[1])])
        
        return render_template('logs.html', logs_list=logs_list, name = UserName)

@app.route('/<string:UserName>/logs/add', methods=['GET', 'POST'])
def add_log(UserName):

    if request.method == 'GET':
        
        present_time = datetime.datetime.now()
        present_datetime = present_time.strftime ("%Y-%m-%dT%H:%M")
     
        return render_template('log_add.html', name = UserName, present_datetime = present_datetime)

    if request.method == 'POST':

        new_time = request.form.get('date_created').replace('T',' ')
        new_datetime = datetime.datetime.strptime(new_time, "%Y-%m-%d %H:%M")

        new_log = Logs( UserName = UserName, \
                        Date_created = new_datetime.replace(second = 0),\
                        Last_modified = datetime.datetime.now().replace(second = 0), \
                      Value = request.form.get('value'),\
                      Description =request.form.get('desc'))
        
        db.session.add(new_log)
        db.session.commit()
        
        return redirect('/'+ UserName+ '/logs')

@app.route('/<string:UserName>/logs/<string:LogID>/delete', methods=['DELETE'])
def log_delete(UserName, LogID):
    if request.method == 'DELETE' :
        Log_entry = Logs.query.filter(Logs.LogID == LogID)
        if Log_entry.all():
            deleted = Log_entry.delete()
            db.commit()
        return redirect('/', UserName, '/logs')

@app.route('/<string:UserName>/logs/<string:LogID>/edit', methods=['GET', 'POST'])
def log_edit(UserName, LogID):
    if request.method == 'GET':
        log_entry = Logs.query.filter(Logs.LogID == LogID).first()
        return render_template('log_edit.html',log = log_entry, name = UserName, lid = LogID)
    
    if request.method == 'POST':
        log_entry = Logs.query.filter(Logs.LogID == LogID).first()
        log_entry.Date_created = request.form.get('date_created')
        log_entry.Value = request.form.get('value')
        log_entry.Description  = request.form.get('desc')
        log_entry.Last_modified = datetime.datetime.now().replace(second = 0)
        db.add(log_entry)
        db.commit()
        return redirect('/', UserName, '/logs')