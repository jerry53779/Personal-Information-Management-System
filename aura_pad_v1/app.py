from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from extensions import db
from models import Contact, HealthRecord, PersonalDetail, Note, Event
from datetime import datetime
import os, csv
from sqlalchemy import or_
import os

app = Flask(__name__)
app.secret_key = os.environ.get('AURAPAD_SECRET', 'dev-secret-key')

# Default DB path (absolute) — editable in code/config to use relative path
default_db_path = r'C:/Users/Jerry/Desktop/DBMS PROJECT/personal_info.db'
# If you want a relative DB, change below to 'sqlite:///personal_info.db'
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'aura_pad.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create DB on first run
with app.app_context():
    db.create_all()

# Dashboard
@app.route('/')
def index():
    contacts_count = Contact.query.count()
    health_count = HealthRecord.query.count()
    notes_count = Note.query.count()
    events = Event.query.order_by(Event.date).limit(6).all()
    upcoming = [{'title': e.title, 'date': e.date.strftime('%Y-%m-%d'), 'id': e.id} for e in events]
    return render_template('index.html', contacts_count=contacts_count, health_count=health_count, notes_count=notes_count, upcoming=upcoming)

# Contacts
@app.route('/contacts')
def contacts_view():
    q = request.args.get('q','').strip()
    if q:
        contacts = Contact.query.filter(Contact.name.ilike(f'%{q}%')).order_by(Contact.name).all()
    else:
        contacts = Contact.query.order_by(Contact.name).all()
    return render_template('contacts/view.html', contacts=contacts, q=q)

@app.route('/contacts/add', methods=['GET','POST'])
def contacts_add():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        phone = request.form.get('phone','').strip()
        email = request.form.get('email','').strip()
        note = request.form.get('note','').strip()
        # basic validation
        if not name:
            flash('Name is required','danger'); return redirect(url_for('contacts_add'))
        if phone and (not phone.isdigit() or len(phone) < 7 or len(phone) > 15):
            flash('Phone must be digits (7-15 chars)','danger'); return redirect(url_for('contacts_add'))
        c = Contact(name=name, phone=phone or None, email=email or None, note=note or None)
        db.session.add(c); db.session.commit()
        flash('Contact added','success'); return redirect(url_for('contacts_view'))
    return render_template('contacts/add.html')

@app.route('/contacts/<int:id>/edit', methods=['GET','POST'])
def contacts_edit(id):
    c = Contact.query.get_or_404(id)
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        phone = request.form.get('phone','').strip()
        email = request.form.get('email','').strip()
        note = request.form.get('note','').strip()
        if not name:
            flash('Name is required','danger'); return redirect(url_for('contacts_edit', id=id))
        if phone and (not phone.isdigit() or len(phone) < 7 or len(phone) > 15):
            flash('Phone must be digits (7-15 chars)','danger'); return redirect(url_for('contacts_edit', id=id))
        c.name, c.phone, c.email, c.note = name, (phone or None), (email or None), (note or None)
        db.session.commit()
        flash('Contact updated','success'); return redirect(url_for('contacts_view'))
    return render_template('contacts/edit.html', contact=c)

@app.route('/contacts/<int:id>/delete', methods=['POST'])
def contacts_delete(id):
    c = Contact.query.get_or_404(id)
    db.session.delete(c); db.session.commit()
    flash('Contact deleted','success'); return redirect(url_for('contacts_view'))

@app.route('/export/contacts')
def export_contacts():
    contacts = Contact.query.order_by(Contact.name).all()
    si = []
    for c in contacts:
        si.append({'id':c.id,'name':c.name,'phone':c.phone or '','email':c.email or '','note':c.note or ''})
    csv_path = '/tmp/contacts_export.csv'
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id','name','phone','email','note'])
        writer.writeheader(); writer.writerows(si)
    return send_file(csv_path, as_attachment=True, download_name='contacts.csv')

# Health
@app.route('/health')
def health_view():
    records = HealthRecord.query.order_by(HealthRecord.created_at.desc()).all()
    return render_template('health/view.html', records=records)

@app.route('/health/add', methods=['GET','POST'])
def health_add():
    if request.method == 'POST':
        try:
            weight = float(request.form.get('weight_kg') or 0)
        except:
            weight = None
        try:
            height = float(request.form.get('height_cm') or 0)
        except:
            height = None
        try:
            bp_s = int(request.form.get('bp_systolic') or 0)
        except:
            bp_s = None
        try:
            bp_d = int(request.form.get('bp_diastolic') or 0)
        except:
            bp_d = None
        notes = request.form.get('notes','').strip()
        hr = HealthRecord(weight_kg=weight or None, height_cm=height or None, bp_systolic=bp_s or None, bp_diastolic=bp_d or None, notes=notes or None)
        db.session.add(hr); db.session.commit()
        flash('Health record added','success'); return redirect(url_for('health_view'))
    return render_template('health/add.html')

# Personal details (single record)
@app.route('/personal', methods=['GET','POST'])
def personal():
    pd = PersonalDetail.query.first()
    if request.method == 'POST':
        full_name = request.form.get('full_name','').strip()
        aadhar = request.form.get('aadhar','').strip()
        passport = request.form.get('passport','').strip()
        pancard = request.form.get('pancard','').strip().upper()
        address = request.form.get('address','').strip()
        # validations
        if aadhar and (not aadhar.isdigit() or len(aadhar) != 12):
            flash('Aadhar must be 12 digits','danger'); return redirect(url_for('personal'))
        if pancard and (not re_fullmatch(r'^[A-Z]{5}\\d{4}[A-Z]$', pancard)):
            flash('PAN must be in format: 5 letters,4 digits,1 letter','danger'); return redirect(url_for('personal'))
        if not pd:
            pd = PersonalDetail(full_name=full_name or None, aadhar=aadhar or None, passport=passport or None, pancard=pancard or None, address=address or None)
            db.session.add(pd)
        else:
            pd.full_name, pd.aadhar, pd.passport, pd.pancard, pd.address = full_name or None, aadhar or None, passport or None, pancard or None, address or None
        db.session.commit(); flash('Personal details saved','success'); return redirect(url_for('personal'))
    return render_template('personal/personal.html', pd=pd)

import re
def re_fullmatch(pattern, string):
    return True if re.fullmatch(pattern, string or '') else False

# Notes
@app.route('/notes')
def notes_list():
    notes = Note.query.order_by(Note.updated_at.desc()).all()
    return render_template('notes/list.html', notes=notes)

@app.route('/notes/add', methods=['GET','POST'])
def notes_add():
    if request.method == 'POST':
        title = request.form.get('title','').strip()
        body = request.form.get('body','').strip()
        if not title:
            flash('Title required','danger'); return redirect(url_for('notes_add'))
        n = Note(title=title, body=body or None)
        db.session.add(n); db.session.commit(); flash('Note created','success'); return redirect(url_for('notes_list'))
    return render_template('notes/add.html')

@app.route('/notes/<int:id>/edit', methods=['GET','POST'])
def notes_edit(id):
    n = Note.query.get_or_404(id)
    if request.method == 'POST':
        title = request.form.get('title','').strip()
        body = request.form.get('body','').strip()
        if not title:
            flash('Title required','danger'); return redirect(url_for('notes_edit', id=id))
        n.title, n.body = title, body or None
        db.session.commit(); flash('Note updated','success'); return redirect(url_for('notes_list'))
    return render_template('notes/edit.html', note=n)

@app.route('/notes/<int:id>/delete', methods=['POST'])
def notes_delete(id):
    n = Note.query.get_or_404(id)
    db.session.delete(n); db.session.commit(); flash('Note deleted','success'); return redirect(url_for('notes_list'))

# Events & Calendar
@app.route('/events')
def events_view():
    return render_template('events/list.html')

@app.route('/events/add', methods=['GET','POST'])
def events_add():
    if request.method == 'POST':
        title = request.form.get('title','').strip()
        date_raw = request.form.get('date','').strip()
        description = request.form.get('description','').strip()
        if not title or not date_raw:
            flash('Title and date required','danger'); return redirect(url_for('events_add'))
        try:
            date = datetime.strptime(date_raw, '%Y-%m-%d')
        except ValueError:
            flash('Date must be YYYY-MM-DD','danger'); return redirect(url_for('events_add'))
        e = Event(title=title, date=date, description=description or None)
        db.session.add(e); db.session.commit(); flash('Event added','success'); return redirect(url_for('events_view'))
    return render_template('events/add.html')

@app.route('/events/<int:id>/delete', methods=['POST'])
def events_delete(id):
    e = Event.query.get_or_404(id)
    db.session.delete(e); db.session.commit(); flash('Event removed','success'); return redirect(url_for('events_view'))

@app.route('/api/events')
def api_events():
    events = Event.query.order_by(Event.date).all()
    out = []
    for e in events:
        out.append({'id':e.id,'title':e.title,'date':e.date.strftime('%Y-%m-%d'),'description':e.description or ''})
    return jsonify(out)

if __name__ == '__main__':
    app.run(debug=True)
