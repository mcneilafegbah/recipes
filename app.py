import os
from flask import Flask, flash, render_template, redirect, request, session, url_for
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

if os.path.exists("env.py"):
    import env

app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)

@app.route("/")
@app.route("/get_recipes")
def get_recipes():
    recipes = list(mongo.db.recipes.find())
    return render_template("recipes.html", recipes=recipes)

@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.form.get("query")
    recipes = list(mongo.db.recipes.find({"$text": {"$search": query}}))
    return render_template("recipes.html", recipes=recipes)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one({"username": request.form.get("username").lower()})
        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        register = {
            "username": request.form.get("username").lower(),
            "email": request.form.get("email").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }
        mongo.db.users.insert_one(register)
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one({"username": request.form.get("username").lower()})
        if existing_user and check_password_hash(existing_user["password"], request.form.get("password")):
            session["user"] = request.form.get("username").lower()
            flash(f"Welcome, {request.form.get('username')}")
            return redirect(url_for("profile", username=session["user"]))
        else:
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    if "user" in session:
        user_recipes = list(mongo.db.recipes.find({"created_by": session["user"]}))
        return render_template("profile.html", username=username, recipes=user_recipes)
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))

@app.route("/add_recipe", methods=["GET", "POST"])
def add_recipe():
    if request.method == "POST":
        ingredients = request.form.get("recipe_ingredient").split('\n')
        directions = request.form.get("recipe_direction").split('\n')
        recipe = {
            "category_name": request.form.get("category_name"),
            "recipe_name": request.form.get("recipe_name"),
            "recipe_about": request.form.get("recipe_about"),
           "recipe_ingredient": [ingredient.strip() for ingredient in ingredients if ingredient.strip()],
            "recipe_direction": [direction.strip() for direction in directions if direction.strip()],
            "cooktime": request.form.get("cooktime"),
            "servings": request.form.get("servings"),
            "created_by": session["user"]
        }
        mongo.db.recipes.insert_one(recipe)
        flash("Recipe Successfully Added")
        return redirect(url_for("get_recipes"))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_recipe.html", categories=categories)

@app.route("/edit_recipe/<recipe_id>", methods=["GET", "POST"])
def edit_recipe(recipe_id):
    if request.method == "POST":
        ingredients = request.form.get("recipe_ingredient").split('\n')
        directions = request.form.get("recipe_direction").split('\n')
        recipe = {
            "category_name": request.form.get("category_name"),
            "recipe_name": request.form.get("recipe_name"),
            "recipe_about": request.form.get("recipe_about"),
            "recipe_ingredient": [ingredient.strip() for ingredient in ingredients if ingredient.strip()],
            "recipe_direction": [direction.strip() for direction in directions if direction.strip()],
            "cooktime": request.form.get("cooktime"),
            "servings": request.form.get("servings"),
            "created_by": session["user"]
        }
        mongo.db.recipes.update_one({"_id": ObjectId(recipe_id)}, {"$set": recipe})
        flash("Recipe Successfully Updated")
        return redirect(url_for("get_recipes"))

    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_recipe.html", recipe=recipe, categories=categories)

@app.route("/delete_recipe/<recipe_id>")
def delete_recipe(recipe_id):
    recipe = mongo.db.recipes.find_one({"_id": ObjectId(recipe_id)})
    if recipe:
        recipe_name = recipe["recipe_name"]
        mongo.db.recipes.delete_one({"_id": ObjectId(recipe_id)})
        flash(f"Recipe '{recipe_name}' successfully deleted")
    else:
        flash("Recipe not found")
    return redirect(url_for("get_recipes"))

if __name__ == "__main__":
    app.run(host=os.environ.get("IP"), port=int(os.environ.get("PORT")), debug=True)