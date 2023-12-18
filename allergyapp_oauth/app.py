from flask import Flask, render_template, url_for, redirect, session
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
import os
from db_functions import update_or_create_user
from flask import Flask, render_template, request
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import sentry_sdk

load_dotenv()

sentry_sdk.init(
    dsn="https://127e735d2fff5cdf04c65db1d3bb20cd@o4506300835758080.ingest.sentry.io/4506408500199424",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

# Database connection settings from environment variables
DB_HOST = os.getenv("DB_HOST")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")

# Creating a connection string
connect_args = {'ssl': {'fake_flag_to_enable_tls': True}}
connection_string = f'mysql+pymysql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}/{DB_DATABASE}'

# Create the SQLAlchemy engine
engine = create_engine(
    connection_string,
    connect_args=connect_args
)


GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

app = Flask(__name__)
app.secret_key = os.urandom(12)
oauth = OAuth(app)

@app.route('/')
def index():
    return render_template('tabs/index.html')

@app.route('/google/')
def google():
    CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url=CONF_URL,
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

    # Redirect to google_auth function
    ###note, if running locally on a non-google shell, do not need to override redirect_uri
    ### and can just use url_for as below
    redirect_uri = url_for('google_auth', _external=True)
    print('REDIRECT URL: ', redirect_uri)
    session['nonce'] = generate_token()
    ##, note: if running in google shell, need to override redirect_uri 
    ## to the external web address of the shell, e.g.,
    redirect_uri = 'https://5000-cs-813183857211-default.cs-us-east1-rtep.cloudshell.dev/google/auth/'
    return oauth.google.authorize_redirect(redirect_uri, nonce=session['nonce'])

@app.route('/google/auth/')
def google_auth():
    token = oauth.google.authorize_access_token()
    user = oauth.google.parse_id_token(token, nonce=session['nonce'])
    session['user'] = user
    update_or_create_user(user)
    print(" Google User ", user)
    return redirect('/dashboard')

@app.route('/dashboard/')
def dashboard():
    user = session.get('user')
    if user:
        return render_template('dashboard.html', user=user)
    else:
        return redirect('/')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

@app.route('/about')
def aboutpage():
    return render_template('about.html')

@app.route('/allergy_testing')
def allergy_testing():
    with engine.connect() as connection:
        query1 = text('SELECT * FROM allergy_tests')
        result1 = connection.execute(query1)
        db_data1 = result1.fetchall()
    return render_template('allergy_testing.html', data1=db_data1)

@app.route('/patients')
def patients():
    with engine.connect() as connection:
        query2 = text('SELECT * FROM patients')
        result2 = connection.execute(query2)
        db_data2 = result2.fetchall()
    return render_template('patients.html', data2=db_data2)

## create a route that throws an error
@app.route('/error')
def error():
    raise Exception('This is a test error for Sentry Testing')

if __name__ == '__main__':
    app.run(
        debug=True, 
        port=5000
    )

#if __name__ == "__main__":
#    app.run(host="0.0.0.0", port=5000)