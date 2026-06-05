# TODO: Add graph traversal for routes
# TODO: Refactor everything (never gonna happen)
# Database is SQLite

# For teammates 
# Running this: python app.py
# Then open http://127.0.0.1:5000
# 


```python

import sqlite3
import random
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
app.secret_key = "super-secret-key-put-yours-here-12345"  #make it secure

# ==============================================
# DATABASE STUFF - I should use an ORM but SQL is FINE
# ==============================================

def init_db():
    """Creates tables if they don't exist. Why is this function so long?"""
    conn = sqlite3.connect('railway.db')
    c = conn.cursor()
    
    # Trains table - main data
    c.execute('''CREATE TABLE IF NOT EXISTS trains (
        train_no TEXT PRIMARY KEY,
        train_name TEXT NOT NULL,
        source TEXT NOT NULL,
        destination TEXT NOT NULL,
        available_seats INTEGER DEFAULT 0,
        waiting_list_count INTEGER DEFAULT 0,
        base_fare INTEGER DEFAULT 200,
        tatkal_quota INTEGER DEFAULT 10,
        popularity_score REAL DEFAULT 0.5
    )''')
    
    # Bookings table - passengers and their chaos
    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
        booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
        train_no TEXT,
        passenger_name TEXT,
        passenger_age INTEGER,
        booking_date TEXT,
        status TEXT,  -- confirmed, waiting, cancelled
        waiting_number INTEGER DEFAULT 0,
        wallet_txn_id TEXT,
        FOREIGN KEY (train_no) REFERENCES trains(train_no)
    )''')
    
    # Wallet transactions - because fake money is fun
    c.execute('''CREATE TABLE IF NOT EXISTS wallet_transactions (
        txn_id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        amount INTEGER,
        txn_type TEXT,
        timestamp TEXT
    )''')
    
    # Insert dummy train data if table is empty
    c.execute("SELECT COUNT(*) FROM trains")
    if c.fetchone()[0] == 0:
        # Adding 15 trains with various routes just copy them I assure you
        dummy_trains = [
            ("12015", "Shatabdi Express", "Delhi", "Jaipur", 45, 0, 450, 8, 0.85),
            ("12985", "Double Decker Express", "Jaipur", "Delhi", 23, 0, 400, 5, 0.75),
            ("12414", "Rajdhani Express", "Delhi", "Mumbai", 12, 0, 1250, 6, 0.95),
            ("12627", "Karnataka Express", "Delhi", "Bengaluru", 8, 0, 980, 4, 0.90),
            ("12301", "Howrah Express", "Kolkata", "Delhi", 32, 0, 750, 7, 0.80),
            ("11057", "Amritsar Express", "Mumbai", "Amritsar", 15, 0, 1100, 5, 0.70),
            ("12138", "Punjab Mail", "Mumbai", "Amritsar", 5, 0, 1050, 3, 0.65),
            ("12615", "Grand Trunk Express", "Delhi", "Chennai", 18, 0, 1350, 6, 0.88),
            ("17030", "Hyderabad Express", "Mumbai", "Hyderabad", 27, 0, 580, 7, 0.72),
            ("19019", "Dehradun Express", "Mumbai", "Dehradun", 9, 0, 890, 4, 0.68),
            ("15658", "Brahmaputra Mail", "Delhi", "Guwahati", 3, 0, 1450, 2, 0.60),
            ("12295", "Sanghamitra Express", "Bengaluru", "Patna", 11, 0, 720, 5, 0.77),
            ("12951", "Mumbai Rajdhani", "Mumbai", "Delhi", 21, 0, 1300, 6, 0.92),
            ("12315", "Ananya Express", "Kolkata", "Jaipur", 14, 0, 820, 4, 0.69),
            ("12723", "Telangana Express", "Hyderabad", "Delhi", 6, 0, 1050, 3, 0.82),
        ]
        for train in dummy_trains:
            c.execute("INSERT INTO trains VALUES (?,?,?,?,?,?,?,?,?)", train)
    
    conn.commit()
    conn.close()
    print("Database ready!")

# Run database initialization
init_db()

# ==============================================
# HELPER FUNCTIONS (some are useful, some are just for fun)
# ==============================================

def get_db_connection():
    """Returns database connection. I could use connection pooling but too long."""
    return sqlite3.connect('railway.db')

def get_wallet_balance():
    """Get wallet balance from session. Blockchain? No, just session dictionary."""
    if 'wallet_balance' not in session:
        session['wallet_balance'] = 2500  # Free money! Because I want free money
    return session['wallet_balance']

def update_wallet(amount, txn_type):
    """Update wallet balance and record transaction. Why am I storing session_id? I don't know."""
    current = get_wallet_balance()
    session['wallet_balance'] = current + amount
    
    # Store transaction in database - for audit? maybe bit too much
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO wallet_transactions (session_id, amount, txn_type, timestamp) VALUES (?,?,?,?)",
              (session.sid if hasattr(session, 'sid') else 'unknown', amount, txn_type, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return session['wallet_balance']

# ==============================================
# "AI" PREDICTION FUNCTION - Very sophisticated (not really)
# ==============================================

def calculate_confirmation_probability(train_no, waiting_number):
    """
    My super advanced AI model using LightGBM and neural networks...
    Just kidding, it's random + train popularity + waiting number.
    ADHD note: started implementing real ML but got distracted by YouTube.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT popularity_score, available_seats, waiting_list_count FROM trains WHERE train_no = ?", (train_no,))
    train = c.fetchone()
    conn.close()
    
    if not train:
        return 0
    
    popularity, available_seats, waiting_list = train
    
    # Base probability decreases with waiting number
    base = 100 - (waiting_number * 3.5)
    
    # Popularity bonus: popular trains have lower chance actually (more demand)
    popularity_penalty = (popularity * 20)
    
    # If waiting number is within available seats range? Actually no, waiting means no seats
    # But if seats become available soon?
    seat_factor = min(20, available_seats * 2)
    
    # Random chaos factor (just cause)
    chaos = random.randint(-15, 15)
    
    probability = base - popularity_penalty + seat_factor + chaos
    
    # Keep between 5% and 98% (never 100% because life is uncertain)
    probability = max(5, min(98, probability))
    
    # Print debug info (I like seeing what the AI is thinking because it looks cool)
    print(f"AI DEBUG - Train: {train_no}, Wait#: {waiting_number}, Prob: {probability}% (pop:{popularity}, seats:{available_seats})")
    
    return int(probability)

# ==============================================
# FLASK ROUTES - Here we go! Hold onto your seats
# ==============================================

@app.route('/')
def home():
    """Home page - looks decent I guess"""
    balance = get_wallet_balance()
    return render_template('index.html', balance=balance)

@app.route('/search', methods=['POST'])
def search():
    """Search trains between source and destination"""
    source = request.form.get('source', '').strip()
    destination = request.form.get('destination', '').strip()
    
    if not source or not destination:
        return render_template('error.html', message="Please enter both source and destination! 🤦")
    
    conn = get_db_connection()
    c = conn.cursor()
    # Using LIKE for fuzzy matching? I'm too tired for case sensitivity
    c.execute("""
        SELECT train_no, train_name, source, destination, available_seats, base_fare, waiting_list_count 
        FROM trains 
        WHERE LOWER(source) LIKE ? AND LOWER(destination) LIKE ?
    """, (f'%{source.lower()}%', f'%{destination.lower()}%'))
    trains = c.fetchall()
    conn.close()
    
    balance = get_wallet_balance()
    return render_template('search_results.html', trains=trains, source=source, destination=destination, balance=balance)

@app.route('/train/<train_no>')
def train_details(train_no):
    """Show detailed info about a specific train"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM trains WHERE train_no = ?", (train_no,))
    train = c.fetchone()
    conn.close()
    
    if not train:
        return render_template('error.html', message="Train not found! Maybe it derailed?")
    
    balance = get_wallet_balance()
    return render_template('train_details.html', train=train, balance=balance)

@app.route('/book/<train_no>', methods=['GET', 'POST'])
def book(train_no):
    """Booking page - GET shows form, POST processes booking"""
    if request.method == 'GET':
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM trains WHERE train_no = ?", (train_no,))
        train = c.fetchone()
        conn.close()
        
        if not train:
            return render_template('error.html', message="Train not found!")
        
        balance = get_wallet_balance()
        return render_template('booking_form.html', train=train, balance=balance)
    
    # POST - process booking
    passenger_name = request.form.get('passenger_name', '').strip()
    passenger_age = request.form.get('passenger_age', 25)
    use_wallet = request.form.get('use_wallet') == 'on'
    
    if not passenger_name:
        return render_template('error.html', message="Please enter passenger name! 📝")
    
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get train details with row lock? Nah, we live dangerously
    c.execute("SELECT available_seats, waiting_list_count, base_fare, train_name FROM trains WHERE train_no = ?", (train_no,))
    train_data = c.fetchone()
    
    if not train_data:
        conn.close()
        return render_template('error.html', message="Train vanished into thin air!")
    
    available_seats, waiting_list_count, fare, train_name = train_data
    
    # Check wallet balance if using wallet
    balance = get_wallet_balance()
    if use_wallet and balance < fare:
        conn.close()
        return render_template('error.html', message=f"Insufficient wallet balance! Need ₹{fare}, have ₹{balance}. Add money! 💰")
    
    # Determine booking status
    if available_seats > 0:
        status = "confirmed"
        waiting_number = 0
        # Reduce available seats
        c.execute("UPDATE trains SET available_seats = available_seats - 1 WHERE train_no = ?", (train_no,))
        message_text = f"🎉 Booking CONFIRMED! Seat allocated. Train: {train_name}"
    else:
        status = "waiting"
        waiting_number = waiting_list_count + 1
        # Increment waiting list count
        c.execute("UPDATE trains SET waiting_list_count = waiting_list_count + 1 WHERE train_no = ?", (train_no,))
        message_text = f"⏳ Booking added to WAITING LIST. Position: {waiting_number}"
    
    # Create booking record
    booking_date = datetime.now().isoformat()
    txn_id = None
    if use_wallet:
        update_wallet(-fare, "booking")
        txn_id = f"TXN_{random.randint(10000,99999)}"
    
    c.execute("""
        INSERT INTO bookings (train_no, passenger_name, passenger_age, booking_date, status, waiting_number, wallet_txn_id)
        VALUES (?,?,?,?,?,?,?)
    """, (train_no, passenger_name, passenger_age, booking_date, status, waiting_number, txn_id))
    
    booking_id = c.lastrowid
    conn.commit()
    conn.close()
    
    new_balance = get_wallet_balance()
    return render_template('booking_success.html', 
                          booking_id=booking_id, 
                          train_no=train_no, 
                          train_name=train_name,
                          status=status, 
                          waiting_number=waiting_number,
                          message=message_text,
                          fare=fare,
                          used_wallet=use_wallet,
                          balance=new_balance)

@app.route('/predict', methods=['POST'])
def predict():
    """
    AI seat prediction endpoint - returns probability of confirmation
    This is the "ML" part of the project. Very fancy.
    """
    train_no = request.form.get('train_no')
    waiting_number = request.form.get('waiting_number')
    
    if not train_no or not waiting_number:
        return jsonify({"error": "Missing train_no or waiting_number"}), 400
    
    try:
        waiting_number = int(waiting_number)
    except ValueError:
        return jsonify({"error": "waiting_number must be integer"}), 400
    
    probability = calculate_confirmation_probability(train_no, waiting_number)
    
    # Generate a random advice message because they do that in loading screens
    advice_messages = [
        "Looks promising!", 
        "Maybe book Tatkal instead?", 
        "Fingers crossed!",
        "My AI says: uncertain, try alternate train",
        "The stars are aligned!",
        "Low probability but miracles happen!"
    ]
    
    if probability > 70:
        advice = "High chance! Go for it!"
    elif probability > 40:
        advice = random.choice(advice_messages)
    else:
        advice = "Sorry, probability is low. Consider other options."
    
    return jsonify({
        "probability": probability,
        "advice": advice,
        "model_used": "ADHD-Net v1.0 (patent pending)"
    })

@app.route('/cancel/<int:booking_id>')
def cancel_booking(booking_id):
    """Cancel a booking - this might have bugs but whatever"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Get booking details
    c.execute("SELECT train_no, status, waiting_number FROM bookings WHERE booking_id = ?", (booking_id,))
    booking = c.fetchone()
    
    if not booking:
        conn.close()
        return render_template('error.html', message="Booking not found! Are you sure it exists?")
    
    train_no, status, _ = booking
    
    if status == "cancelled":
        conn.close()
        return render_template('error.html', message="Booking already cancelled! No double cancellation 😤")
    
    # Update booking status
    c.execute("UPDATE bookings SET status = 'cancelled' WHERE booking_id = ?", (booking_id,))
    
    # If confirmed booking, add seat back to train
    if status == "confirmed":
        c.execute("UPDATE trains SET available_seats = available_seats + 1 WHERE train_no = ?", (train_no,))
        message = "Booking cancelled! Seat added back to inventory."
    else:
        # For waiting list cancellation, just reduce waiting count
        c.execute("UPDATE trains SET waiting_list_count = waiting_list_count - 1 WHERE train_no = ?", (train_no,))
        message = "Waiting list booking cancelled. Your position removed."
    
    conn.commit()
    conn.close()
    
    balance = get_wallet_balance()
    return render_template('cancel_success.html', booking_id=booking_id, message=message, balance=balance)

@app.route('/my-bookings')
def my_bookings():
    """Show all bookings - I need to add user system but session is fine"""
    # This is a hack - since no login, just show last 10 bookings from the session
    # TODO: Actually link to session user ID (one day)
    conn = get_db_connection()
    c = conn.cursor()
    # For demo, show recent bookings (last 20)
    c.execute("""
        SELECT b.booking_id, b.train_no, t.train_name, b.passenger_name, b.status, b.waiting_number, b.booking_date
        FROM bookings b
        JOIN trains t ON b.train_no = t.train_no
        ORDER BY b.booking_id DESC LIMIT 20
    """)
    bookings = c.fetchall()
    conn.close()
    
    balance = get_wallet_balance()
    return render_template('my_bookings.html', bookings=bookings, balance=balance)

@app.route('/wallet')
def wallet():
    """Wallet page - show balance and add money"""
    balance = get_wallet_balance()
    
    # Get transaction history
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT amount, txn_type, timestamp FROM wallet_transactions WHERE session_id = ? ORDER BY timestamp DESC LIMIT 10",
              (session.sid if hasattr(session, 'sid') else 'unknown',))
    transactions = c.fetchall()
    conn.close()
    
    return render_template('wallet.html', balance=balance, transactions=transactions)

@app.route('/add-money', methods=['POST'])
def add_money():
    """Add money to wallet - totally secure (not really)"""
    amount = request.form.get('amount', 0, type=int)
    
    if amount <= 0:
        return render_template('error.html', message="Enter a positive amount!")
    
    if amount > 10000:
        return render_template('error.html', message="Max ₹10,000 per transaction (too much money is suspicious)")
    
    new_balance = update_wallet(amount, "recharge")
    
    # ADHD style: random success message
    messages = ["Money added!", "Cha-ching!", "Wallet funded!", "Transaction successful!"]
    
    return render_template('wallet_success.html', amount=amount, new_balance=new_balance, message=random.choice(messages))

@app.route('/tatkal/<train_no>')
def tatkal_booking(train_no):
    """Special Tatkal booking - extra cost, limited quota, chaotic"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT tatkal_quota, base_fare, train_name, available_seats FROM trains WHERE train_no = ?", (train_no,))
    train = c.fetchone()
    
    if not train:
        conn.close()
        return render_template('error.html', message="Train not found!")
    
    tatkal_quota, base_fare, train_name, available_seats = train
    
    # Tatkal fare is 1.5x + random handling charge (because why not)
    tatkal_fare = int(base_fare * 1.5) + random.randint(10, 50)
    
    if tatkal_quota <= 0:
        conn.close()
        return render_template('error.html', message="Tatkal quota exhausted! Just as usual. No corruption at all.")
    
    balance = get_wallet_balance()
    if balance < tatkal_fare:
        conn.close()
        return render_template('error.html', message=f"Tatkal requires ₹{tatkal_fare}. Your balance: ₹{balance}. Add money first!")
    
    # Process Tatkal booking
    update_wallet(-tatkal_fare, "tatkal_booking")
    c.execute("UPDATE trains SET tatkal_quota = tatkal_quota - 1, available_seats = available_seats - 1 WHERE train_no = ?", (train_no,))
    
    # Create booking record
    booking_date = datetime.now().isoformat()
    c.execute("""
        INSERT INTO bookings (train_no, passenger_name, passenger_age, booking_date, status, waiting_number, wallet_txn_id)
        VALUES (?,?,?,?,?,?,?)
    """, (train_no, "TATKAL_USER", 30, booking_date, "confirmed", 0, f"TATKAL_{random.randint(1000,9999)}"))
    
    booking_id = c.lastrowid
    conn.commit()
    conn.close()
    
    new_balance = get_wallet_balance()
    return render_template('tatkal_success.html', 
                          train_name=train_name, 
                          train_no=train_no, 
                          fare=tatkal_fare,
                          booking_id=booking_id,
                          balance=new_balance)

@app.route('/alternate-routes')
def alternate_routes():
    """Find alternate routes - because graph traversal sounded cool but I got bored"""
    # This is a stub for the "graph algorithm engine" I promised
    # It just returns some hardcoded suggestions (ADHD at its finest)
    source = request.args.get('source', 'Delhi')
    destination = request.args.get('destination', 'Mumbai')
    
    # Hardcoded alternate routes (I'll implement real BFS later...)
    alternates = [
        {"route": f"{source} → Jaipur → {destination}", "stops": 2, "duration_hrs": 14, "change_at": "Jaipur"},
        {"route": f"{source} → Ahmedabad → {destination}", "stops": 2, "duration_hrs": 16, "change_at": "Ahmedabad"},
        {"route": f"{source} → Bhopal → {destination}", "stops": 2, "duration_hrs": 12, "change_at": "Bhopal"},
    ]
    
    balance = get_wallet_balance()
    return render_template('alternate_routes.html', alternates=alternates, source=source, destination=destination, balance=balance)

# ==============================================
# RUN THE APP - Please don't break
# ==============================================

if __name__ == '__main__':
    print("\n" + "="*50)
    print("RAILWAY RESERVATION SYSTEM")
    print("="*50)
    print("Server starting at: http://127.0.0.1:5000")
    print("Wallet balance default: ₹2500 (free real estate)")
    print("Admin tip: Check console for AI debug messages!")
    print("="*50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)



```
