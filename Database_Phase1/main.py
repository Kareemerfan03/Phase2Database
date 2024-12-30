from flask import Flask, render_template, request
import psycopg2
app = Flask(__name__)

def connect_to_database():
    try:
        conn = psycopg2.connect(dbname='user_info' ,user='postgres',password='kareem',host='localhost' ,port=5432)
        print("Database connected successfully!")

        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            db_version = cursor.fetchone()
            print("Database version:", db_version)

    except Exception as e:
        print("Error connecting to the database:", e)

if __name__ == '__main__':
    connect_to_database()

@app.route('/')
def home():
    return render_template('index.html')

# Example route for a POST request
@app.route('/submit', methods=['POST'])
def submit():
    data = request.form.get('input_data')
    # Process the data
    result = f"Processed: {data}"
    return render_template('result.html', result=result)  # Pass data to another page

if __name__ == '__main__':
    app.run(debug=True)
if __name__ == '__main__':
    connect_to_database()
