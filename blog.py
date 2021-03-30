from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

# Kullanıcı Giriş Decorator'ı

def login_required(dashboard):
    @wraps(dashboard)
    def decorated_function(*args, **kwargs):
       if "logged_in" in session: 
        return dashboard(*args, **kwargs)
       else:
        flash("Please login to view this page","danger")
        return redirect(url_for("login"))
    return decorated_function

# wt formları kullanarak bir tane register form ile diğer formları türetebiliriz.
# wt formsuz html template larda birçok form oluşturmak zorunda kalabiliriz.

# Kullanıcı Kayıt Formu
class RegisterForm(Form):
    name = StringField("Name-Last name", validators=[validators.length(min = 4, max = 25)]) #validators input sınırlandırma validators.required zorunlu alan
    username = StringField("User Name", validators=[validators.length(min = 5, max = 20)])
    email = StringField("E-mail", validators=[validators.Email(message="please enter a valid email address")])
    password = PasswordField("Password",validators=[
        validators.DataRequired(message="Please set a password"),
        validators.EqualTo(fieldname = "confirm", message="the passwords you entered do not match")])

    confirm = PasswordField("Verify Password")
class LoginForm(Form):
    username = StringField("User Name")
    password = PasswordField("Password")

# Bootstrap hazır modüller bulunduran css kütüphanesi
app = Flask(__name__) 
app.secret_key ="aiblog"

app.config["MYSQL_HOST"] = "localhost" #mysql host bilgisi
app.config["MYSQL_USER"] = "root" #kullanıcı ismi parola boş şekilde geliyor
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "aiblog" 
app.config["MYSQL_CURSORCLASS"] = "DictCursor" #flask ve mysql ilişkisi

mysql = MySQL(app) #flask ile ilişki tamamlama

@app.route("/")
def index():
    articles = [

    #     {"id":1, "title":"Deneme1","content":"Deneme1 icerik"},
    #     {"id":2, "title":"Deneme2","content":"Deneme2 icerik"},
    #     {"id":3, "title":"Deneme3","content":"Deneme3 icerik"}
    ]
    return render_template("index.html",articles = articles)

@app.route("/aboutus")
def about():
    return render_template("about.html")

#Makale Sayfası
@app.route("/articles")
def articles():

    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles"

    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")

@app.route("/articles/<string:id>")
def detail(id):
    return "Article ID:" + id

@app.route("/dashboard")
@login_required #****
def dashboard():
    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where author = %s"

    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles=articles)
    else:
        return render_template("dashboard.html")


    return render_template("dashboard.html")
#register
@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():

        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)
       
        #veri tabanı üzerinde işlem cursor
        cursor = mysql.connection.cursor()

        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"

        cursor.execute(sorgu,(name,email,username,password)) # %s lerin yerine geçmesi için demet oalrak verdik
        #sql sorgusu çalıştırmak tek sorgu varsa demet (name,(virgül))

        mysql.connection.commit() #sadece bilgi çekiyorsak commit yapmak zorunda değiliz

        cursor.close()

        flash("The record has been successfully created","success")

        return redirect(url_for("login"))   #belli bir sayfaya git
    else:
        return render_template("register.html",form = form)

#Login işlemi
@app.route("/login",methods = ["POST","GET"])
def login():
    form =LoginForm(request.form)
    if request.method =="POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "Select * from users where username = %s"

        result = cursor.execute(sorgu,(username,)) # 0 1

        if result > 0:
            data = cursor.fetchone() #kullanıcı bilgileri çekme
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Login successfully","success")

                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("index"))
            else:
                flash("Password Incorrect","danger")
                return redirect(url_for("login"))
        else:
            flash("User not found","danger")

        return redirect(url_for("login"))

    return render_template("login.html",form = form)

# Log out
@app.route("/logout")
def logout():
    session.clear() # sessionu kapatma
    flash("Exit Successful","success")
    return redirect(url_for("index"))

#Makale Ekleme
@app.route("/addarticle",methods = ["POST","GET"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))

        mysql.connection.commit()

        cursor.close()

        flash("The article has been successfully added","success")

        return redirect(url_for("dashboard"))

    return render_template("addarticle.html",form = form)

# Detay Sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select *from articles where id =%s"

    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article=article)
    else:
        return render_template("article.html")

#Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor  = mysql.connection.cursor()

    sorgu = "select * from articles where author = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0:
        sorgu2 = "Delete from articles where id = %s"

        cursor.execute(sorgu2,(id,))

        mysql.connection.commit()

        return redirect(url_for("dashboard"))

    else:
        flash("This article does not exist or you are not authorized for this action","danger")
        return redirect(url_for("index"))

#Makale Güncelleme
@app.route("/edit/<string:id>",methods =["GET","POST"])
@login_required
def update(id):

    if request.method == "GET":
        cursor = mysql.connection.cursor()

        sorgu = "select * from articles where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))

        if result == 0:
            flash("This article does not exist or you are not authorized for this action ","danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]

            return render_template("update.html",form=form)
    else:
        #post request
        form = ArticleForm(request.form)

        newTitle = form.title.data
        newContent = form.content.data

        sorgu2 = "Update articles Set title = %s, content = %s where id = %s"

        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))

        mysql.connection.commit()

        flash("The article has been updated successfully","success")

        return redirect(url_for("dashboard"))
#Makale Form
class ArticleForm(Form):
    title = StringField("Article Title",validators=[validators.length(min = 5,max = 100)])
    content = TextAreaField("Article Content",validators = [validators.length(min = 10)])


#Arama URL
@app.route("/search",methods=["GET","POST"])
def search():
        if request.method == "GET":
            return redirect(url_for("index"))
        else:
            keyword = request.form.get("keyword")

            cursor = mysql.connection.cursor()

            sorgu = "Select * from articles where title like '%" + keyword +"%'"

            result = cursor.execute(sorgu)

            if result == 0:
                flash("No articles matching the search term were found.","warning")
                return redirect(url_for("articles"))
            else:
                articles = cursor.fetchall()
                return render_template("articles.html",articles=articles)

if __name__ == "__main__":
    app.run(debug=True) 
