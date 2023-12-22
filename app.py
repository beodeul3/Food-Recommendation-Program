from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)

api_key_spoonacular = "your_spoonacular_api"

app.config['SPOONACULAR_URL'] = "https://api.spoonacular.com/recipes/findByNutrients"

recipe_detail_url = "https://api.spoonacular.com/recipes/{recipe_id}/nutritionWidget.json"

allergies = ["milk", "eggs", "fish", "crustacean shellfish", "tree nuts", "peanuts", "wheat", "soybeans"]

def get_calorie_range(bmi):
    if bmi < 18.5:
        return 600, 1000
    elif 18.5 <= bmi < 25:
        return 500, 900
    elif 25 <= bmi < 30:
        return 400, 800    
    elif 30 <= bmi < 35:
        return 300, 700
    elif 35 <= bmi < 40:
        return 200, 600
    else:
        return 100, 500

def get_user_allergies():
    user_allergies = []
    for allergen in allergies:
        if request.form.get(allergen):
            user_allergies.append(allergen)
    return user_allergies

def call_spoonacular_api(min_calories, max_calories):
    params = {
        "minCalories": min_calories,
        "maxCalories": max_calories,
        "number": 5,
        "random": True,
        "limitLicense": True,
        "apiKey": api_key_spoonacular
    }
    response = requests.get(app.config['SPOONACULAR_URL'], params=params)
    return response.json()

def get_recipe_detail(recipe_id):
    url = recipe_detail_url.format(recipe_id=recipe_id)
    params = {"apiKey": api_key_spoonacular}
    response = requests.get(url, params=params)
    
    if response.status_code == 404:
        return {}
    
    recipe_detail = response.json()
    return recipe_detail

def filter_allergies(recipe_detail, user_allergies):
    for allergen in user_allergies:
        if any(allergen.lower() in nutrient["name"].lower() for nutrient in recipe_detail.get("nutrients", [])):
            return False
    return True

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        height = float(request.form["height"])
        weight = float(request.form["weight"])

        bmi = weight / ((height / 100) ** 2)

        min_calories, max_calories = get_calorie_range(bmi)

        user_allergies = get_user_allergies()

        recipe_list = call_spoonacular_api(min_calories, max_calories)

        filtered_recipe_list = [recipe for recipe in recipe_list if filter_allergies(get_recipe_detail(recipe["id"]), user_allergies)]

        return render_template("index.html", recipe_list=filtered_recipe_list, allergies=allergies)

    return render_template("index.html", allergies=allergies)


@app.route("/recommendations", methods=["POST"])
def show_recommendations():
    if request.method == "POST":

        height = float(request.form["height"])
        weight = float(request.form["weight"])

        user_allergies = request.form.getlist("allergies")

        bmi = weight / ((height / 100) ** 2)

        min_calories, max_calories = get_calorie_range(bmi)

        recipe_list = call_spoonacular_api(min_calories, max_calories)

        filtered_recipe_list = [recipe for recipe in recipe_list if filter_allergies(get_recipe_detail(recipe["id"]), user_allergies)]

        return render_template("recommendations.html", recipe_list=filtered_recipe_list)

    return redirect(url_for("index"))


@app.route("/recipe_detail", methods=["POST"])
def recipe_detail():
    if request.method == "POST":

        selected_recipe_id = request.form.get("selected_recipe")

        recipe_detail = get_recipe_detail(selected_recipe_id)

        return render_template("recipe.html", recipe_detail=recipe_detail)

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
