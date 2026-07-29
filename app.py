import markdown, os
import config
from flask import Flask, render_template, request, redirect, render_template_string, session
from flask_wtf.csrf import CSRFProtect
from database import db
from services.story_service import *
from services.thumbnail_generator.thumbnail_generator import *
from werkzeug.security import generate_password_hash, check_password_hash
from flask import send_file, abort
from services.exporter.exporter import export_to_txt, export_to_docx, export_to_pdf


app = Flask(__name__)
app.config.from_object(config)
app.config['SECRET_KEY'] = '0f9a2e6b7c8d4e5f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d'
csrf = CSRFProtect(app)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)


#Initializing the database
db.init_db()

#Initialize global variables
@app.context_processor
def inject_user_status():
    connection = db.get_db_connection()
    logged_in = session.get('logged_in', False)
    logged_in_user = session.get('logged_in_user')
    avatar_name = "user.png"

    if logged_in and logged_in_user != "Anonymous Guest":
        raw_avatar_name = connection.execute(
            "SELECT avatar_file FROM users WHERE user_name = ?",
            (logged_in_user,)
        ).fetchone()
        
        if raw_avatar_name:
            try:
                avatar_name = raw_avatar_name['avatar_file']
            except (TypeError, IndexError):
                avatar_name = raw_avatar_name[0]

    connection.close()

    if not logged_in or not logged_in_user:
        display_name = "Anonymous Guest"
    else:
        display_name = logged_in_user

    return {
        'logged_in': logged_in,
        'logged_in_user': display_name,
        'avatar_name': avatar_name
    }


@app.route('/')
def index():
    logged_in = session.get('logged_in')
    connection = db.get_db_connection()
    logged_in_user = session.get('logged_in_user')
    genre_filter = request.args.get('genre-filter')
    search_input = request.args.get('search')
    search_btn = request.args.get('search-btn')
    query=""
    

    #fetch all stories and users according to genre and search
    if search_input:
        query = '''
            SELECT
            stories.story_id,
            stories.title,
            stories.thumbnail_url,
            users.user_id AS author_id,
            users.user_name AS author_name,
            users.avatar_file AS author_avatar
            FROM stories
            LEFT JOIN users ON stories.owner_id = users.user_id
            WHERE stories.title LIKE ? OR users.user_name LIKE ?
            ORDER BY RANDOM();
        '''

        stories = connection.execute(query, (f"%{search_input.lower()}%", f"%{search_input.lower()}%")).fetchall()

    elif genre_filter == 'all' or not genre_filter:
        stories = connection.execute('''
            SELECT
            stories.story_id,
            stories.title,
            stories.thumbnail_url,
            users.user_id AS author_id,
            users.user_name AS author_name,
            users.avatar_file AS author_avatar
            FROM stories
            LEFT JOIN users ON stories.owner_id = users.user_id ORDER BY RANDOM();
        ''').fetchall()
        
    else:
        query = '''
            SELECT
            stories.story_id,
            stories.title,
            stories.thumbnail_url,
            users.user_id AS author_id,
            users.user_name AS author_name,
            users.avatar_file AS author_avatar
            FROM stories
            LEFT JOIN users ON stories.owner_id = users.user_id WHERE genre LIKE ? ORDER BY RANDOM();
        '''

        stories = connection.execute(query, (f"%{genre_filter}%",)).fetchall()

    connection.close()
    return render_template("index.html", title = "StoryForge | Home", stories = stories, logged_in = logged_in, genre_filter = genre_filter, search_input = search_input)

@app.route('/profile', methods=['POST', 'GET'])
def profile():
    connection = db.get_db_connection()
    text = None
    user_stories = []
    logged_in = session.get('logged_in')
    logged_in_user = session.get('logged_in_user')

    if request.method == 'POST':
        #Handle user logout form submission action
        if request.form.get('logout') == 'logout':
            session.pop('logged_in', None)
            session.pop('logged_in_user', None)
            connection.close()
            return redirect('/')
            
        if request.form.get('change-avatar-btn') == 'true':
            avatar = request.form.get('chosen_avatar')
            if avatar and logged_in_user:
                connection.execute(
                    "UPDATE users SET avatar_file = ? WHERE user_name = ?",
                    (avatar, logged_in_user)
                )
                connection.commit()
            connection.close()
            return redirect('/profile')

    #Handle dashboard template view generation
    if logged_in:
        text = session.get('login_text')

        query = "SELECT story_id, title, thumbnail_url FROM stories WHERE owner_id = ?"
        user_id = connection.execute("SELECT user_id FROM users WHERE user_name = ?", (logged_in_user,)).fetchone()
        
        if user_id:
            user_stories = connection.execute(query, (user_id[0],)).fetchall()
            
        return render_template("dashboard/profile.html", title="StoryForge | Profile", login_text=text, logged_in=logged_in, user_stories=user_stories)
    else:
        text = 'No Active User'
        
    connection.close()
    return render_template("dashboard/profile.html", title="StoryForge | Profile", login_text=text, logged_in=logged_in, user_stories=user_stories)


@app.route('/view-user', methods=['POST', 'GET'])
def view_user():
    user_stories = []
    user_id = None
    user_name = "Anonymous Guest"
    connection = db.get_db_connection()
    user_avatar = "user.png"
    
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        user_name = data.get('text_content')

        raw_user_id = connection.execute(
            "SELECT user_id FROM users WHERE LOWER(user_name) = LOWER(?)", (user_name,)
        ).fetchone()
        
        if raw_user_id is not None:
            user_id = raw_user_id[0]
            user_stories = connection.execute("SELECT story_id, title FROM stories WHERE owner_id = ?", (user_id,)).fetchall()
            raw_user_avatar = connection.execute("SELECT avatar_file FROM users WHERE user_id = ?", (user_id,)).fetchone()
            user_avatar = raw_user_avatar[0]
        else:
            user_id = None
            user_name = "User Not Found"

    else:
        # Read view-user
        user_id = request.args.get('user-id')
        if user_id:
            raw_user = connection.execute("SELECT user_name FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if raw_user:
                user_name = raw_user[0]
                user_stories = connection.execute("SELECT story_id, title FROM stories WHERE owner_id = ?", (user_id,)).fetchall()

    connection.close()
    
    return render_template('view_user.html', user_stories=user_stories, user_id=user_id, user_name=user_name, user_avatar = user_avatar)


@app.route('/login', methods=['POST', 'GET'])
def login():
    feedback_msg=None
    connection=db.get_db_connection()
    if request.method=='POST':
        user_name=request.form.get('username')
        password=request.form.get('password')
        
        user_exists = connection.execute("SELECT user_name FROM users WHERE user_name = ?", (user_name,)).fetchone()
        if user_exists != None:
            saved_hash_pwd = connection.execute("SELECT user_password FROM users WHERE user_name = ?", (user_name,)).fetchone()

            if ":" in saved_hash_pwd[0]:
                is_valid=check_password_hash(saved_hash_pwd[0], password)
            else:
                is_valid=(saved_hash_pwd[0] == password)
                if is_valid:
                    new_hash = generate_password_hash(password)
                    connection.execute("UPDATE users SET user_password = ? WHERE user_name = ?", (new_hash, user_name))
                    connection.commit()

            if is_valid:
                session['logged_in'] = True
                session['logged_in_user'] = user_name
                session['login_text'] = f"User active: @{user_name}"
                connection.close()
                return redirect("/profile")
            else:
                feedback_msg="Incorrect password.Try again!"
                connection.close()
                return render_template("auth/login.html", feedback_msg=feedback_msg, password="")
        else:
            feedback_msg="Username not Found. Try another!"
            connection.close()
            return render_template("auth/login.html", feedback_msg=feedback_msg, user_name="", password="")
    connection.close()
    return render_template("auth/login.html")


@app.route('/register', methods=['POST','GET'])
def register():
    connection = db.get_db_connection()
    users=connection.execute("SELECT * FROM users")
    feedback_msg=None
    feedback_msg_status=None

    if request.method=='POST':
        username = request.form.get('username')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        submit_btn = request.form.get('create_user')

        existing_user = connection.execute("SELECT * FROM users WHERE user_name = ?", (username,)).fetchone()
        query = "INSERT INTO users(user_name, user_password) VALUES (?, ?)"
        if submit_btn:
            if password1!=password2:
                feedback_msg = "Passwords don't match Try again"
                feedback_msg_status="error"
                return render_template("auth/register.html", feedback_msg=feedback_msg, feedback_msg_status=feedback_msg_status)

            if existing_user:
                feedback_msg = "Username already used!"
                feedback_msg_status="error"
                return render_template("auth/register.html", feedback_msg=feedback_msg, feedback_msg_status=feedback_msg_status)

            else:
                password = generate_password_hash(password1)
                connection.execute(query, (username, password))
                connection.commit()

                feedback_msg = f"User {username} has successfully been created!"
                feedback_msg_status="success"
                connection.close()
                return render_template("auth/register.html", feedback_msg=feedback_msg, registration_success=True, feedback_msg_status=feedback_msg_status)
    connection.close()
    return render_template("auth/register.html", users=users)


@app.route('/about', methods=['POST', 'GET'])
def about_contact():
    receiver_email = os.getenv('EMAIL')
    phone_number = os.getenv('PHONE_NUMBER')

    return render_template('about_us.html', phone_number=phone_number, receiver_email = receiver_email)


@app.route('/create-story', methods=['POST','GET'])
def create_story():
    connection = db.get_db_connection()
    title_text = ""
    content = ""
    owner_id = 0
    thumbnail_url = ""
    art_description = ""
    feedback_message = ""
    genres = ""
    story_id = None

    if request.method == 'POST':
        instructions = request.form.get('instructions')
        genre = request.form.get('genre')
        topic = request.form.get('topic')
        submit_btn = request.form.get('create')

        logged_in_user = session.get('logged_in_user', 'Anonymous Guest')

        save_btn = request.form.get('yes')
        no_save_btn = request.form.get('no')

        if submit_btn == 'publish':
            raw_content = create_new_story(instructions, genre, topic)
            title_text = "Untitled Story"
            content_text = raw_content
            
            if "[TITLE]" in raw_content and "[CONTENT]" in raw_content and "[THUMBNAIL_PROMPT]" in raw_content:
                try:
                    title_part = raw_content.split("[TITLE]")[1]
                    title_text = title_part.split("[CONTENT]")[0].strip()
                    
                    content_part = raw_content.split("[CONTENT]")[1]
                    raw_story_body = content_part.split("[THUMBNAIL_PROMPT]")[0].strip()
                    
                    if "has been provided above" in raw_story_body:
                        content_text = raw_story_body.split("[CONTENT] has been provided above")[0].strip()
                    else:
                        content_text = raw_story_body
                    
                    art_description = raw_content.split("[THUMBNAIL_PROMPT]")[1].strip()

                except IndexError:
                    title_text = "Untitled Story"
                    content_text = raw_content
                    art_description = f"Cinematic cover art for a {genre} story about {topic}"

            content = markdown.markdown(content_text)
            thumbnail_url = generate_story_thumbnail(art_description)

        elif save_btn:
            saved_title = request.form.get('hidden_title')
            saved_content = request.form.get('hidden_content')
            thumbnail_url = request.form.get('hidden_thumbnail')
            
            #FIXED PARAMETER TUPLE LOOKUP GUARD
            raw_owner_id = connection.execute("SELECT user_id FROM users WHERE user_name = ?", (logged_in_user,)).fetchone()
            
            if raw_owner_id:
                try:
                    owner_id = raw_owner_id['user_id']
                except (TypeError, IndexError):
                    owner_id = raw_owner_id[0]
            else:
                #ANONYMOUS GUEST PLACEHOLDER
                guest_user_id = connection.execute("SELECT user_id FROM users WHERE user_name LIKE ?", ('%Guest%',)).fetchone()
                if guest_user_id:
                    try:
                        owner_id = guest_user_id['user_id']
                    except (TypeError, IndexError):
                        owner_id = guest_user_id[0]
                else:
                    owner_id = 0

            connection.execute("INSERT INTO stories(owner_id, title, content, thumbnail_url, genre) VALUES(?, ?, ?, ?, ?)", (owner_id, saved_title, saved_content, thumbnail_url, genre,))
            connection.commit()
            
            feedback_message = f"Story saved successfully! | Creator: {logged_in_user}"
            raw_story_id = connection.execute("SELECT story_id FROM stories WHERE owner_id = ? AND title = ? ORDER BY story_id DESC LIMIT 1;", (owner_id, saved_title,)).fetchone()
            story_id = raw_story_id[0]

            connection.close()
            return render_template("stories/create_story.html", owner_id=owner_id, content=content, title=saved_title, feedback_message=feedback_message, thumbnail_url=thumbnail_url, genre = genre, story_id = story_id)

        elif no_save_btn:
            feedback_message = "Story discarded"
            connection.close()
            return render_template("stories/create_story.html", owner_id=owner_id, content="", title="", feedback_message=feedback_message, genre="")
    try:
        connection.close()
    except:
        pass
        
    return render_template("stories/create_story.html", owner_id=owner_id, content=content, title=title_text, thumbnail_url=thumbnail_url, feedback_message=feedback_message, genre = genres)


@app.route("/view-story", methods=['GET', 'POST'])
def view_story():
    connection = db.get_db_connection()
    logged_in_user = session.get("logged_in_user")
    logged_in = session.get("logged_in")
    check_creator = ""

    if logged_in:
        check_creator = connection.execute("SELECT user_id FROM users WHERE user_name = ?", (logged_in_user,)).fetchone()



    #HANDLE THE DELETE ACTION FIRST (POST)
    if request.method == 'POST':
        story_id = int(request.form.get('story_id'))
        delete_btn = request.form.get('delete-story')

        if delete_btn:
            if logged_in and check_creator[0]:
                alert = f"The story With Id: {story_id} has been successfully deleted!"
                delete_query = "DELETE FROM stories WHERE story_id = ?"
                connection.execute(delete_query, (story_id,))
                connection.commit()
                connection.close()
                return f"""
                    <script>
                        alert("{alert}");
                        window.location.href="/";
                    </script>
                """
            else:
                alert = f"Only the Creator can delete the story"
                return f"""<script>
                        alert("{alert}");
                        window.location.href="/";
                    </script>
                """

    #HANDLE THE INITIAL PAGE VIEW DEFAULT (GET)
    raw_owner_id=[]
    story_id_str = request.args.get('story_id')
    if not story_id_str:
        connection.close()
        return "Missing story_id parameter", 400
        
    story_id = int(story_id_str)

    query = """
        SELECT stories.*, users.user_name
        FROM stories
        LEFT JOIN users ON stories.owner_id = users.user_id
        WHERE stories.story_id = ?
    """
    story = connection.execute(query, (story_id,)).fetchone()
    raw_owner_id = connection.execute("SELECT owner_id FROM stories WHERE story_id = ?", (story_id,)).fetchone()
    owner_id = raw_owner_id[0]
    connection.close()

    if story is None:
        return "Story not found", 404
    return render_template("/stories/view_story.html", story = story, owner_id = owner_id, story_id = story['story_id'])


@app.route('/story/<int:story_id>/export/<string:format_type>')
def download_story(story_id, format_type):
    connection = db.get_db_connection()
    story = connection.execute("SELECT title, content, thumbnail_url FROM stories WHERE story_id = ?", (story_id,)).fetchone()
    connection.close()
    
    if not story:
        abort(404)
        
    title = story['title']
    html_content = story['content']
    thumbnail_url = story['thumbnail_url']
    
    import re
    clean_text_regex = re.compile('<.*?>')
    plain_content = re.sub(clean_text_regex, '', html_content).strip()
    

    safe_filename = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    safe_filename = safe_filename.replace(' ', '_').lower()

    if format_type == 'txt':
        file_stream = export_to_txt(title, plain_content)
        return send_file(file_stream, as_attachment=True, download_name=f"{safe_filename}.txt", mimetype="text/plain")
        
    elif format_type == 'docx':
        file_stream = export_to_docx(title, plain_content, thumbnail_url)
        return send_file(file_stream, as_attachment=True, download_name=f"{safe_filename}.docx", mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        
    elif format_type == 'pdf':
        file_stream = export_to_pdf(title, plain_content, thumbnail_url)
        return send_file(file_stream, as_attachment=True, download_name=f"{safe_filename}.pdf", mimetype="application/pdf")
        
    else:
        abort(400) # Bad Request format handler


if __name__ == "__main__":
    app.debug=True
    app.config['SESSION_COOKIE_SECURE'] = not app.debug

    app.run(host='0.0.0.0', port=8080)
