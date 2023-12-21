from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)

# Spoonacular API 키
api_key_spoonacular = "9747cbf38a3b4fa497c9cf9976d17156"

# Spoonacular API 요청 URL
app.config['SPOONACULAR_URL'] = "https://api.spoonacular.com/recipes/findByNutrients"

# Spoonacular API 상세 정보 요청 URL
recipe_detail_url = "https://api.spoonacular.com/recipes/{recipe_id}/nutritionWidget.json"

# 알러지 목록
allergies = ["milk", "eggs", "fish", "crustacean shellfish", "tree nuts", "peanuts", "wheat", "soybeans"]

# BMI에 따른 칼로리 구간 설정
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

# 사용자로부터 알러지 정보를 입력받는 함수
def get_user_allergies():
    user_allergies = []
    for allergen in allergies:
        if request.form.get(allergen):
            user_allergies.append(allergen)
    return user_allergies

# Spoonacular API 호출 함수
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

# Spoonacular 상세 정보 호출 함수
def get_recipe_detail(recipe_id):
    url = recipe_detail_url.format(recipe_id=recipe_id)
    params = {"apiKey": api_key_spoonacular}
    response = requests.get(url, params=params)
    
    # 음식 세부 정보가 없을 경우 빈 딕셔너리 반환
    if response.status_code == 404:
        return {}
    
    recipe_detail = response.json()
    return recipe_detail

# 알러지 성분을 확인하여 필터링하는 함수
def filter_allergies(recipe_detail, user_allergies):
    for allergen in user_allergies:
        if any(allergen.lower() in nutrient["name"].lower() for nutrient in recipe_detail.get("nutrients", [])):
            return False
    return True

# index 뷰 함수 수정
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # 사용자에게 키와 몸무게 입력 받기
        height = float(request.form["height"])
        weight = float(request.form["weight"])

        # BMI 계산
        bmi = weight / ((height / 100) ** 2)

        # BMI에 따른 칼로리 구간 설정
        min_calories, max_calories = get_calorie_range(bmi)

        # 사용자로부터 알러지 정보 입력 받기
        user_allergies = get_user_allergies()

        # Spoonacular API 호출하여 음식 추천 목록 받아오기
        recipe_list = call_spoonacular_api(min_calories, max_calories)

        # 알러지 성분을 고려하여 필터링된 음식 목록
        filtered_recipe_list = [recipe for recipe in recipe_list if filter_allergies(get_recipe_detail(recipe["id"]), user_allergies)]

        # 음식 추천 목록 출력
        return render_template("index.html", recipe_list=filtered_recipe_list, allergies=allergies)

    return render_template("index.html", allergies=allergies)


@app.route("/recommendations", methods=["POST"])
def show_recommendations():
    if request.method == "POST":
        # 사용자에게 키와 몸무게 입력 받기
        height = float(request.form["height"])
        weight = float(request.form["weight"])

        # 사용자의 알러지 정보
        user_allergies = request.form.getlist("allergies")

        # BMI 계산
        bmi = weight / ((height / 100) ** 2)

        # BMI에 따른 칼로리 구간 설정
        min_calories, max_calories = get_calorie_range(bmi)

        # Spoonacular API 호출하여 음식 추천 목록 받아오기
        recipe_list = call_spoonacular_api(min_calories, max_calories)

        # 알러지 성분을 고려하여 필터링된 음식 목록
        filtered_recipe_list = [recipe for recipe in recipe_list if filter_allergies(get_recipe_detail(recipe["id"]), user_allergies)]

        # 추천된 음식 목록을 새로운 페이지에 전달
        return render_template("recommendations.html", recipe_list=filtered_recipe_list)

    # 기본적으로는 홈페이지로 리다이렉트
    return redirect(url_for("index"))


@app.route("/recipe_detail", methods=["POST"])
def recipe_detail():
    if request.method == "POST":
        # 선택한 레시피 ID 가져오기
        selected_recipe_id = request.form.get("selected_recipe")

        # Spoonacular API를 통해 음식의 상세 정보 받아오기
        recipe_detail = get_recipe_detail(selected_recipe_id)

        # 음식의 상세 정보 출력
        return render_template("recipe.html", recipe_detail=recipe_detail)

    # 기본적으로는 홈페이지로 리다이렉트
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
