import json

# all those functions are used to retrieve the corresponding items from the db in our case the json file 
# for instance get_available_dish retrives the list of (meal_type, meal_name) that belongs to the given meal_group 
# if meal group is not define that retrieve all the available (meal_type, meal_name)

def get_available_dish(meal_group):
    # load data
    with open("db/database.json") as f:
        data = json.load(f)
    # extraction
    meal_names = []
    for meal_type, meals in data.items():
        for meal in meals:
            if not meal_group:
                meal_names.append((meal_type, meal["item"]))
            elif meal["meal_group"] == meal_group:
                meal_names.append((meal_type, meal["item"]))
    return meal_names


def get_to_be_slots(meal_type, meal_name):
    """
    this will retrieve all the items that needs to be filled out by the user based on meal type and name, 
    and use this information to create a dynamic form
    """
    # load data
    with open("db/database.json") as f:
        data = json.load(f)
    # extraction
    to_be_slots = []
    remove_key = ["meal_group", "item", "price", "removals", "extras"]
    for meal in data.get(meal_type, []):
        if meal["item"] == meal_name:
            for key, value in meal.items():
                if key not in remove_key:
                    to_be_slots.append(key)
                    if isinstance(value, str):
                        continue
                    elif isinstance(value.get("items", []), dict):
                        to_be_slots.append(f"{key}_type")
    return to_be_slots


def get_available_extras(meal_type, meal_name):
    # load data
    with open("db/database.json") as f:
        data = json.load(f)
    # extraction
    for meal in data[meal_type]:
        if meal["item"] == meal_name:
            return meal["extras"]["items"]
    return []


def get_available_additions(meal_type, meal_name):
    with open("db/database.json") as f:
        data = json.load(f)
    # extraction
    for meal in data[meal_type]:
        if meal["item"] == meal_name:
            return meal["additions"]["items"].keys()
    return []    


def get_available_meal_types(meal_name):
    # assuming that different meal groups doesnot have same meal_name
    # load data
    with open("db/database.json") as f:
        data = json.load(f)
    # extract meals
    meal_types = []
    for meal_type, meals in data.items():
        for meal in meals:
            if meal["item"] == meal_name:
                meal_types.append(meal_type)

    return meal_types


def get_available_fries_size(meal_type, meal_name):
    # load data
    with open("db/database.json") as f:
        data = json.load(f)
    for meal in data[meal_type]:
        if meal["item"] == meal_name:
            return meal.get("fries_size", {}).get("items", [])
    return []


def get_available_drinks(meal_type, meal_name):
    with open("db/database.json") as f:
        data = json.load(f)
    for meal in data[meal_type]:
        if meal["item"] == meal_name:
            return meal["drink"]["items"].keys()
    return []


def get_available_drink_type(meal_type, meal_name, drink):
    with open("db/database.json") as f:
        data = json.load(f)
    for meal in data[meal_type]:
        if meal["item"] == meal_name:
            return meal["drink"]["items"].get(drink, [])
    return []
