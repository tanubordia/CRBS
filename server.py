from flask import Flask, render_template,request,g,flash,redirect,url_for,jsonify,json,session
from datetime import datetime,timedelta
import sqlite3


#initialising app
app = Flask(__name__)
app.secret_key = 'some_secret'


@app.route('/')
def index():
	li = g.db.execute("SELECT city,e_name,b_date from Bookings,Rooms where Bookings.r_id = Rooms.r_id and b_date>=date('now') order by b_date asc;").fetchall();
	return render_template('index.html',data=li)

#connecting to DB before every request
@app.before_request
def before_request():
    g.db = sqlite3.connect('usersDB.db')

#closing connection after every request
@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()


@app.route('/signup', methods=['GET', 'POST'])
def test():
	if(request.method=='POST'):
		uid = request.form['sp_uid']
		passw = request.form['sp_pass']
		name = request.form['uname']
		email = request.form['email']
		phone = request.form['cell']
		city = request.form['city']

		if(len(uid)==0 or len(passw)==0 or len(name)==0 or len(email)==0 or len(phone)==0 or city=='City'):
			return jsonify(result = 'Please fill up all the fields')
		else:
			li = g.db.execute("SELECT * from Users WHERE uid = ?;",[uid]).fetchall();

			if(len(li)>0):
				return jsonify(result='User-id already exists! Please choose a different User-id.')
			else:
				g.db.execute("INSERT INTO Users VALUES (?,?,?,?,?,?);", (uid,passw,name,email,phone,city))
				g.db.commit()
				return jsonify(result='Signup successful! Now login with your new User-id.')
				
			
#clicking on Login
@app.route('/login',methods=['GET', 'POST'])
def login():
	if(request.method=='POST'):
		uid = request.form['uid']
		passw = request.form['pass']

		li = g.db.execute("SELECT pass from Users WHERE uid = ?;",[uid]).fetchall();
		nm = g.db.execute("SELECT uname from Users WHERE uid = ?;",[uid]).fetchall();

		if(len(li)==0):
			flash("Invalid User-id")
			return redirect(url_for('index'))
			
		else:
			if(str(passw)==str(li[0][0])):
				session['uname'] = str(nm[0][0])
				return render_template('choice.html',data = str(nm[0][0]))
			else:
				flash("Incorrect password")
				return redirect(url_for('index'))
			
@app.route('/choice')
def manageHall():
	if(session.get('uname',None)):
		return render_template('choice.html',data = session.get('uname',None))
	else:
		return render_template('choice.html')


@app.route('/calendar',methods=["POST"])
def calendar():
	if(request.method=="POST"):
		uid = session.get('uid',None)
		rid = request.form['click_rid']
		r_name = request.form['rname']
		session['rname'] = r_name
		session['rid'] = rid
		li = g.db.execute('SELECT e_name,b_date,days from Bookings where r_id = ?',[rid])
		days=[]
		for day in li:
			dt = datetime.strptime(day[1],'%Y-%m-%d')
			ndays = day[2]
			dt_next = dt + timedelta(days = ndays)
			days.append([day[0],dt,dt_next])

		session['days'] = days
		# days = ['TEST','2017-09-25','2017-09-27']
		return render_template('calendar.html',data=days,hallname=r_name)


@app.route('/searchHalls',methods=['POST'])
def searchHalls():
	if(request.method=='POST'):
		city = request.form['hallcity']
		no_of_seats = request.form['seats']
		session['uid'] = request.form['uid']
		ac = request.form['ac']
		sb = request.form['sb']
		pr = request.form['pr']
		a=1
		s=1
		p=1
		li=[]

		if(no_of_seats==''):
			no_of_seats=0
		else:
			try:
				no_of_seats=int(no_of_seats)
			except exception as e:
				flash("Invalid no. of seats")
		if(ac==""):
			a=0
		if(sb==""):
			s=0
		if(pr==""):
			p=0
		
		if(city=='City'):
			li = g.db.execute("SELECT r_id,r_name,loc,seats,city from Rooms WHERE seats >= ? and ac = ? and sb = ? and prj = ?;",(no_of_seats,a,s,p)).fetchall()
		else:
			li = g.db.execute("SELECT r_id,r_name,loc,seats,city from Rooms WHERE city = ? and seats >= ? and ac = ? and sb = ? and prj = ?;",(city,no_of_seats,a,s,p)).fetchall()
		
		return jsonify(list=li)


@app.route('/bookHall',methods=['POST'])
def bookHall():
	if(request.method=='POST'):
		d = datetime.today()

		nofdays = (int)(request.form['nofdays'])
		e_name = request.form['eventName']
		date = request.form['book-date']	#2017-09-24
		bk_day = (int)(date[8:])
		bk_mon = (int)(date[5:7])
		bk_year = (int)(date[:4])

		req_date = datetime.strptime(date, '%Y-%m-%d')

		uid = session.get('uid',None)
		rid = session.get('rid',None)
		r_name =session.get('rname',None)
		days = session.get('days',None)

		if((d.year,d.month,d.day)<=(bk_year,bk_mon,bk_day)):
			if(nofdays<=0):
				flash('Number of days cannot be negative or 0')
				return render_template('calendar.html',data=days,hallname=r_name)
			elif(nofdays>15):
				flash('Number of days limit exceeded! Maximum allowed is 15 days')
				return render_template('calendar.html',data=days,hallname=r_name)
			else:
				li = g.db.execute('SELECT b_date,days from Bookings where r_id = ?;',[rid]).fetchall()
				if(len(li)==0):
					try:
						g.db.execute('INSERT into Bookings VALUES (?,?,?,?,?)',(rid,uid,e_name,date,nofdays))
						g.db.commit()
						flash('Booking successful!')
						dt = datetime.strptime(date,'%Y-%m-%d')
						ndays = nofdays
						dt_next = dt + timedelta(days = ndays)
						days.append([e_name,dt,dt_next])
						session['days'] = days

					except sqlite3.Error as e:
						flash('Something went wrong..{0}'.format(e))
						return render_template('calendar.html',data=days,hallname=r_name)
				else:
					flag=0
					for x in li:
						dt = x[0]
						dt = datetime.strptime(dt,'%Y-%m-%d')
						ndays = x[1]
						dt_next = dt + timedelta(days = ndays-1)
						d1 = (dt.year,dt.month,dt.day)
						
						d3 = (dt_next.year,dt_next.month,dt_next.day)
						print(x)
						for k in range(nofdays):
							req_date_nxt = req_date + timedelta(days = k)
							print(req_date_nxt)
							d2 = (req_date_nxt.year,req_date_nxt.month,req_date_nxt.day)
							if(d1<=d2<=d3):
								flash('Sorry, requested dates are not available.')
								flag=1
								break
						if(flag==1):
							break
					else:
						g.db.execute('INSERT into Bookings VALUES (?,?,?,?,?)',(rid,uid,e_name,date,nofdays))
						g.db.commit()
						flash('Booking successful!')

						dt = datetime.strptime(date,'%Y-%m-%d')
						ndays = nofdays
						dt_next = dt + timedelta(days = ndays)
						days.append([e_name,dt,dt_next])
						session['days'] = days

				return render_template('calendar.html',data=days,hallname=r_name)
		else:
			flash('Invalid booking date: Cannot book a past date.')
			return render_template('calendar.html',data=days,hallname=r_name)


if __name__ == '__main__':
  app.run(host= '0.0.0.0', port=5000, debug=True)
#host= '0.0.0.0', port=5000,
