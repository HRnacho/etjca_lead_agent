from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import requests
import json
import time
import os
from datetime import datetime, timedelta
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database inizializzazione
def init_db():
    conn = sqlite3.connect('etjca_agent.db')
    cursor = conn.cursor()
    
    # Tabella prospects
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prospects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cognome TEXT NOT NULL,
            azienda TEXT NOT NULL,
            email TEXT,
            telefono TEXT,
            linkedin_url TEXT,
            posizione TEXT,
            citta TEXT,
            provincia TEXT,
            settore TEXT,
            dimensioni_azienda TEXT,
            fonte TEXT,
            stato TEXT DEFAULT 'nuovo',
            data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            note TEXT
        )
    ''')
    
    # Tabella email campaigns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER,
            oggetto TEXT,
            contenuto TEXT,
            data_invio TIMESTAMP,
            stato TEXT DEFAULT 'inviata',
            risposta TEXT,
            data_risposta TIMESTAMP,
            FOREIGN KEY (prospect_id) REFERENCES prospects (id)
        )
    ''')
    
    # Tabella appuntamenti
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appuntamenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prospect_id INTEGER,
            data_appuntamento TIMESTAMP,
            tipo TEXT DEFAULT 'Colloquio in azienda',
            note TEXT,
            stato TEXT DEFAULT 'confermato',
            engage_id TEXT,
            FOREIGN KEY (prospect_id) REFERENCES prospects (id)
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/')
def dashboard():
    """Dashboard principale"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('etjca_agent.db')
    cursor = conn.cursor()
    
    # Statistiche
    cursor.execute("SELECT COUNT(*) FROM prospects")
    total_prospects = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM email_campaigns WHERE data_invio >= date('now', '-30 days')")
    emails_sent = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM appuntamenti WHERE data_appuntamento >= date('now')")
    appointments_scheduled = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM email_campaigns WHERE risposta IS NOT NULL")
    responses_received = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('dashboard.html', 
                         total_prospects=total_prospects,
                         emails_sent=emails_sent,
                         appointments_scheduled=appointments_scheduled,
                         responses_received=responses_received)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login utente"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Verifica credenziali (semplificato)
        if username == 'admin' and password == 'password':
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Credenziali non valide')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout utente"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/search_prospects')
def search_prospects():
    """Pagina ricerca prospect"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template('search_prospects.html')

@app.route('/select_prospects')
def select_prospects():
    """Pagina selezione prospect"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('etjca_agent.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM prospects WHERE stato = 'nuovo' ORDER BY data_creazione DESC")
    prospects = cursor.fetchall()
    
    conn.close()
    
    return render_template('select_prospects.html', prospects=prospects)

@app.route('/reports')
def reports():
    """Pagina report"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template('reports.html')

@app.route('/settings')
def settings():
    """Pagina impostazioni"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template('settings.html')

@app.route('/api/add_prospect_manual', methods=['POST'])
def api_add_prospect_manual():
    """API per aggiungere prospect manualmente"""
    data = request.get_json()
    
    conn = sqlite3.connect('etjca_agent.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO prospects (nome, cognome, azienda, email, telefono, linkedin_url, 
                             posizione, citta, provincia, settore, fonte, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['nome'], data['cognome'], data['azienda'], data.get('email'),
        data.get('telefono'), data.get('linkedin_url'), data.get('posizione'),
        data.get('citta'), data.get('provincia'), data.get('settore'),
        'Manuale', data.get('note')
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/dashboard_stats')
def api_dashboard_stats():
    """API per statistiche dashboard"""
    conn = sqlite3.connect('etjca_agent.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM prospects")
    total_prospects = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM email_campaigns")
    emails_sent = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM appuntamenti")
    appointments_scheduled = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM email_campaigns WHERE risposta IS NOT NULL")
    responses_received = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'total_prospects': total_prospects,
        'emails_sent': emails_sent,
        'appointments_scheduled': appointments_scheduled,
        'responses_received': responses_received
    })

if __name__ == '__main__':
    init_db()
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
