import random

def generate_smart_diet_plan(goal, preference):
    """
    Generates a dynamic 24-hour meal plan based on user goal and diet type.
    """
    
    # 1. Calorie & Macro Logic
    if goal == 'weight_loss':
        calories = "1500-1800 kcal"
        focus = "High Protein, Low Carb, Calorie Deficit"
    elif goal == 'muscle_gain':
        calories = "2500-2800 kcal"
        focus = "High Protein, Moderate Carb, Calorie Surplus"
    else: # stamina, flexibility, etc.
        calories = "2000-2200 kcal"
        focus = "Balanced Macros, High Hydration"

    # 2. Food Database (Vegetarian vs Non-Veg)
    if preference == 'vegetarian':
        proteins = ["Paneer Tikka", "Lentil Soup (Dal)", "Chickpea Salad", "Greek Yogurt", "Tofu Stir-fry", "Soy Chunks", "Quinoa"]
    else:
        proteins = ["Grilled Chicken Breast", "Salmon/Fish", "Boiled Eggs", "Lean Turkey", "Chicken Curry (Light oil)", "Tuna Salad"]

    carbs = ["Brown Rice", "Oatmeal", "Sweet Potato", "Whole Wheat Roti", "Multigrain Bread"]
    fats = ["Almonds & Walnuts", "Olive Oil dressing", "Avocado", "Peanut Butter", "Chia Seeds"]
    fruits = ["Apple", "Banana", "Berries", "Orange", "Papaya"]
    veggies = ["Spinach", "Broccoli", "Mixed Veggies", "Cucumber Salad", "Steamed Beans"]

    # 3. Randomize Meals
    plan = {
        'goal_title': goal.replace('_', ' ').title(),
        'preference': preference.title(),
        'calories': calories,
        'focus': focus,
        'breakfast': f"Bowl of {random.choice(carbs)} with {random.choice(fats)} and a side of {proteins[0]}.",
        'snack_1': f"A fresh {random.choice(fruits)} and a handful of {random.choice(fats)}.",
        'lunch': f"1 cup {random.choice(carbs)}, a large portion of {proteins[1]}, and {random.choice(veggies)}.",
        'snack_2': "Protein Shake or Greek Yogurt with seeds.",
        'dinner': f"Light salad with {proteins[2]} and {random.choice(veggies)} (Avoid heavy carbs at night).",
        'tip': "Drink 3-4 liters of water. Consistency is key!"
    }
    
    return plan