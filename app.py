# app.py
from flask import Flask, render_template, jsonify, request
from datetime import datetime
from db_utils import DatabaseManager
from cigarette_tracker import CigaretteTracker

app = Flask(__name__)
db = DatabaseManager()
tracker = CigaretteTracker(db)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cigarette', methods=['POST'])
def add_cigarette():
    data = request.json
    cigarette_id = tracker.add_cigarette(
        notes=data.get('notes'),
        trigger_category=data.get('trigger_category'),
        location=data.get('location')
    )
    return jsonify({'id': cigarette_id})

@app.route('/api/stats/today', methods=['GET'])
def get_today_stats():
    # Add debug logging
    print("Getting today's stats...")
    
    stats = tracker.get_stats_for_day()
    print(f"Stats from tracker: {stats}")
    
    cigarettes = tracker.get_daily_cigarettes()
    print(f"Cigarettes from tracker: {cigarettes}")
    
    last_cigarette_time = None
    time_since_last = "No cigarettes today"
    
    if cigarettes:
        # Get the most recent cigarette
        most_recent = cigarettes[0]  # They're ordered by timestamp DESC
        print(f"Most recent cigarette: {most_recent}")
        
        try:
            # Ensure we're handling timezone consistently
            last_cigarette_time = datetime.strptime(
                most_recent['timestamp'], 
                '%Y-%m-%d %H:%M:%S'
            )
            now = datetime.now()
            
            print(f"Last cigarette time: {last_cigarette_time}")
            print(f"Current time: {now}")
            
            # Calculate time difference
            diff = now - last_cigarette_time
            total_minutes = int(diff.total_seconds() / 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            
            time_since_last = f"{hours}h {minutes}m"
            print(f"Calculated time since: {time_since_last}")
            
        except Exception as e:
            print(f"Error processing timestamp: {str(e)}")
            print(f"Problematic timestamp: {most_recent['timestamp']}")
            time_since_last = "Error calculating time"

    response_data = {
        'total_count': stats.get('total_count', 0),
        'time_since_last': time_since_last,
        'hourly_breakdown': stats.get('hourly_breakdown', {}),
        'triggers': stats.get('triggers', {})
    }
    
    print(f"Sending response: {response_data}")
    return jsonify(response_data)
    
if __name__ == '__main__':
    app.run(debug=True)
