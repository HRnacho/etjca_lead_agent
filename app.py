from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import pymysql
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

# Configurazione database MySQL
def get_db_connection():
    if os.getenv('MYSQL_DATABASE'):
        # Produzione PythonAnywhere
        connection = pymysql.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DATABASE'),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    else:
        # Sviluppo locale (se serve)
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            database='etjca_agent',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    return connection

# Database inizializzazione
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabella prospects
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prospects (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            cognome VARCHAR(100) NOT NULL,
            azienda VARCHAR(255) NOT NULL,
            email VARCHAR(255),
            telefono VARCHAR(50),
            linkedin_url TEXT,
            posizione VARCHAR(255),
            citta VARCHAR(100),
            provincia VARCHAR(10),
            settore VARCHAR(100),
            dimensioni_azienda VARCHAR(50),
            fonte VARCHAR(50),
            stato VARCHAR(20) DEFAULT 'nuovo',
            data_creazione TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            note TEXT
        )
    ''')
    
    # Tabella email campaigns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_campaigns (
            id INT AUTO_INCREMENT PRIMARY KEY,
            prospect_id INT,
            oggetto VARCHAR(255),
            contenuto TEXT,
            data_invio TIMESTAMP,
            stato VARCHAR(20) DEFAULT 'inviata',
            risposta TEXT,
            data_risposta TIMESTAMP,
            FOREIGN KEY (prospect_id) REFERENCES prospects (id)
        )
    ''')
    
    # Tabella appuntamenti
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appuntamenti (
            id INT AUTO_INCREMENT PRIMARY KEY,
            prospect_id INT,
            data_appuntamento TIMESTAMP,
            tipo VARCHAR(100) DEFAULT 'Colloquio in azienda',
            note TEXT,
            stato VARCHAR(20) DEFAULT 'confermato',
            engage_id VARCHAR(50),
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
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Statistiche
    cursor.execute("SELECT COUNT(*) as count FROM prospects")
    total_prospects = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM email_campaigns WHERE data_invio >= DATE_SUB(NOW(), INTERVAL 30 DAY)")
    emails_sent = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM appuntamenti WHERE data_appuntamento >= NOW()")
    appointments_scheduled = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM email_campaigns WHERE risposta IS NOT NULL")
    responses_received = cursor.fetchone()['count']
    
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
    
    conn = get_db_connection()
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
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Dati per report
    cursor.execute("""
        SELECT DATE(data_creazione) as data, COUNT(*) as prospects_trovati
        FROM prospects 
        WHERE data_creazione >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY DATE(data_creazione)
        ORDER BY data
    """)
    prospects_data = cursor.fetchall()
    
    cursor.execute("""
        SELECT DATE(data_invio) as data, COUNT(*) as email_inviate
        FROM email_campaigns 
        WHERE data_invio >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY DATE(data_invio)
        ORDER BY data
    """)
    emails_data = cursor.fetchall()
    
    cursor.execute("""
        SELECT DATE(data_appuntamento) as data, COUNT(*) as appuntamenti
        FROM appuntamenti 
        WHERE data_appuntamento >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY DATE(data_appuntamento)
        ORDER BY data
    """)
    appointments_data = cursor.fetchall()
    
    conn.close()
    
    return render_template('reports.html', 
                         prospects_data=prospects_data,
                         emails_data=emails_data,
                         appointments_data=appointments_data)

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
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO prospects (nome, cognome, azienda, email, telefono, linkedin_url, 
                             posizione, citta, provincia, settore, fonte, note)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM prospects")
    total_prospects = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM email_campaigns")
    emails_sent = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM appuntamenti")
    appointments_scheduled = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM email_campaigns WHERE risposta IS NOT NULL")
    responses_received = cursor.fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'total_prospects': total_prospects,
        'emails_sent': emails_sent,
        'appointments_scheduled': appointments_scheduled,
        'responses_received': responses_received
    })

@app.route('/api/get_prospects')
def api_get_prospects():
    """API per ottenere lista prospects"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM prospects ORDER BY data_creazione DESC LIMIT 100")
    prospects = cursor.fetchall()
    
    conn.close()
    
    return jsonify({'prospects': prospects})

@app.route('/api/search_prospects', methods=['POST'])
def api_search_prospects():
    """API per ricerca prospect"""
    data = request.get_json()
    source = data.get('source', 'linkedin')
    keywords = data.get('keywords', '')
    location = data.get('location', 'Friuli Venezia Giulia')
    
    # Simulazione ricerca (da implementare con scraping reale)
    mock_prospects = [
        {
            'nome': 'Mario',
            'cognome': 'Rossi',
            'azienda': 'Tech Solutions SRL',
            'posizione': 'HR Manager',
            'citta': 'Udine',
            'fonte': source
        },
        {
            'nome': 'Laura',
            'cognome': 'Bianchi',
            'azienda': 'Innovazione SpA',
            'posizione': 'Responsabile Risorse Umane',
            'citta': 'Trieste',
            'fonte': source
        }
    ]
    
    return jsonify({'prospects': mock_prospects})

@app.route('/api/save_settings', methods=['POST'])
def api_save_settings():
    """API per salvare impostazioni"""
    data = request.get_json()
    
    # Qui implementeresti il salvataggio delle impostazioni
    # Per ora restituiamo solo success
    
    return jsonify({'success': True})

if __name__ == '__main__':
    init_db()
    port = int(os.getenv('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
