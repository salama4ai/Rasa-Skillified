from typing import Any, Text, Dict, List, Union

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset, FollowupAction
from rasa_sdk.types import DomainDict
import json
# from actions.db_utils import *
from db_utils import *
 

# ============================= custom actions of stories =============================

class ActionExtractOrder(Action):
    """
    This custom action is responsible for extracting removals and extras from entities in tracker 
    and put them into the corresponding slot

    """
    def name(self) -> Text:
        return "action_extract_order"

    def removals_n_extras_extractor(self, entities):
        # entities has all the entities recognized by the rasa nlu components
        # so we parse and put them into the list
        removals = [] 
        extras = []
        for entity in entities:
            if entity["entity"] == "item" and entity["group"] == "extra":
                extras.append(entity["value"])
            elif entity["entity"] == "item" and entity["group"] == "removal":
                removals.append(entity["value"])

        # we make sure that the empty removals and extras are None type instead of []
        # so that rasa form with ask users to fill them out
        if not removals:
            removals = None
        if not extras:
            extras = None
        
        return removals, extras
    
    def run(self, dispatcher, tracker, domain):
        entities = tracker.latest_message["entities"]
        # parse removals and extras from entities in the tracker
        removals, extras = self.removals_n_extras_extractor(entities)
        
        # making sure that only the removals and/or extras that are filled are returned
        # return_slots = [SlotSet("meal_group", "meal")]
        return_slots = []
        if removals:
            return_slots.append(SlotSet("removals", removals))
        if extras:
            return_slots.append(SlotSet("extras", extras))

        return return_slots
    

class ActionShowOrder(Action):
    """
    this custom action is responsible for showing/dispatching the order details as a bot response
    """
    def name(self) -> Text:
        return "action_show_order"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # get the slot key value pair from the tracker object
        slots = tracker.current_slot_values()      

        # prepare the output message, basically converting the dict into a string
        msg = ""
        for slot_name, value in slots.items():
            msg += f"{slot_name} : {value} \n"

        # dispatching the order as a bot response
        dispatcher.utter_message(text = msg)
        return []

class ActionResetAllSlots(Action):
    """
    use this action to reset all the slot to None and perform ordering process as a fresh start 
    basically we don't have to load the model again if we use this action to reset the slot
    """
    def name(self) -> Text:
        return "action_reset_all_slots"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(
            text="Reset all slots; fresh start of the conversation"
            )
        return [AllSlotsReset()]


class ActionFaqHandle(Action):
    """
    use this action to reset all the slot to None and perform ordering process as a fresh start 
    basically we don't have to load the model again if we use this action to reset the slot
    """
    def name(self) -> Text:
        return "action_faq_handle"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(
            text="Return response text using GPT"
            )
        return []
    

# ============================ custom ask responses for order form =============================

class ActionAskMeal(Action):
    """
    rasa internally call this action as a response to fill out meal slot, 
    we can dispatch the suggestion and instruction as a bot response 
    """
    def name(self) -> Text:
        return "action_ask_meal"

    def generate_suggestions(self, tracker):
        # for now suggestions are the available relevant items of the db
        # prepare suggestion of available meal besed on meal group
        # In the future we can we recommendation model to generate suggestions
        meal_group = tracker.current_slot_values()["meal_group"]
        available_items = get_available_dish(meal_group)
        suggestions ="suggestions: " + " ,".join([" ".join(item) for item in available_items])
        return suggestions
    
    def run(self, dispatcher, tracker, domain):
        # generate suggestions
        suggestions = self.generate_suggestions(tracker)

        # display question and suggestions as a bot response
        dispatcher.utter_message(text="What do you want for meal 🍔?")
        dispatcher.utter_message(text=suggestions)
        return []

class ActionAskMealType(Action):
    """
    similar to the ActionAskMeal but for the meal type
    """
    def name(self) -> Text:
        return "action_ask_meal_type"

    def generate_suggestions(self, tracker):
        # here we are generating suggestions based on meal's name selected by the user
        slots = tracker.current_slot_values()
        meal_name = slots.get("meal")
        available_types = get_available_meal_types(meal_name)
        suggestions = "suggestions: "+" ,".join(available_types)
        return suggestions

    def run(self, dispatcher, tracker, domain):
        suggestions = self.generate_suggestions(tracker)
        dispatcher.utter_message(text="please specify the meal type")
        dispatcher.utter_message(text=suggestions)
        return [] 


class ActionAskDrink(Action):
    """
    similar to the ActionAskMeal but for the drink
    """
    def name(self) -> Text:
        return "action_ask_drink"

    def generate_suggestions(self, tracker):
        # generate suggestions of drink based on meal's name and type selected by the user
        slots = tracker.current_slot_values()
        meal_type = slots.get("meal_type")
        meal_name = slots.get("meal")
        available_drinks = get_available_drinks(meal_type, meal_name)
        suggestions ="suggestions: " + " ,".join(available_drinks)
        return suggestions

    def run(self, dispatcher, tracker, domain):
        suggestions = self.generate_suggestions(tracker)
        dispatcher.utter_message(text="Do you want a drink 🥤? ")
        dispatcher.utter_message(text=suggestions)

        return []

class ActionAskDrinkType(Action):
    """
    similar to the ActionAskMeal but for the drink's type
    """
    def name(self) -> Text:
        return "action_ask_drink_type"

    def generate_suggestions(self, tracker):
        # generate suggestions based on meal's name, type and a drink selected my the user
        slots = tracker.current_slot_values()        
        meal_name = slots.get("meal")
        meal_type = slots.get("meal_type")
        drink = slots.get("drink")
        available_fries_size = get_available_drink_type(meal_type, meal_name, drink)
        suggestions ="suggestions: " + " ,".join(available_fries_size)
        return suggestions

    def run(self, dispatcher, tracker, domain):
        suggestions = self.generate_suggestions(tracker)
        dispatcher.utter_message(text="please specify the drink type")
        dispatcher.utter_message(text=suggestions)
        return []   

class ActionAskFriesSize(Action):
    """
    similar to the ActionAskMeal but for the fries size
    """
    def name(self) -> Text:
        return "action_ask_fries_size"

    def generate_suggestions(self, tracker):
        # generate suggestions based on meal's name and type
        slots = tracker.current_slot_values()        
        meal_name = slots.get("meal")
        meal_type = slots.get("meal_type")
        available_fries_size = get_available_fries_size(meal_type, meal_name)
        suggestions ="suggestions: " + " ,".join(available_fries_size)
        return suggestions

    def run(self, dispatcher, tracker, domain):
        suggestions = self.generate_suggestions(tracker)
        dispatcher.utter_message(text="please specify the fries size 🍟")
        dispatcher.utter_message(text=suggestions)
        return []    


class ActionAskExtras(Action):
    """
    similar to the ActionAskMeal but for the extras
    """
    def name(self) -> Text:
        return "action_ask_extras"

    def run(self, dispatcher, tracker, domain):
        slot = tracker.current_slot_values()        
        available_extras = get_available_extras(slot["meal_type"], slot["meal"])

        if available_extras:
            suggestions = "suggestions: "+" ,".join(available_extras)
            dispatcher.utter_message(text="Do you want any extras?")
            dispatcher.utter_message(text=suggestions)
            return []
        else: # it will only be executed when a meal in the db has extras field but no items are available
            dispatcher.utter_message(text="sorry ! no extras available right now")
            return [SlotSet("extras", "NO")]


class ActionAskAdditions(Action):
    """
    similar to the ActionAskMeal but for the additions
    """
    def name(self) -> Text:
        return "action_ask_additions"

    def generate_suggestions(self, tracker):
        # generate suggestions based on meal's name and type specified by the customer
        slots = tracker.current_slot_values()
        meal_type = slots.get("meal_type")
        meal_name = slots.get("meal")
        available_additions = get_available_additions(meal_type, meal_name)
        suggestions ="suggestions: " + " ,".join(available_additions)
        return suggestions

    def run(self, dispatcher, tracker, domain):
        suggestions = self.generate_suggestions(tracker)
        dispatcher.utter_message(text="what do you like for additions?")
        dispatcher.utter_message(text=suggestions)
        return []


# ============================= order_form validation ===============================

class ValidateRestaurantForm(FormValidationAction):
    """
    this class will be exectued internally by the rasa when a form slot has been filled.
    we can add logics to verify if the item specified by the customer is available or not in the db,
    if it is not available then we simplay reset the correponsind slot with value None and rasa will 
    trigger the custom ask action again until the corresponding slot is filled.

    """
    def name(self) -> Text:
        return "validate_order_form"
    
    
    async def required_slots(self, domain_slots,
                             dispatcher, tracker, domain):
        """
        this an crutial method if you want to create dynamic form,
        we can dynamically add slots in the form so that form will ask different questions for different responses,
        we have also used it for the confirmation of the meal getting changed.
        """        

        print(tracker.current_slot_values())

        slot = tracker.current_slot_values()
        # additional slots are the items name such as "drinks, drink_type, fries, extras, additions" 
        # that are available in the db for corresponding meal and meal type
        # we use these names for dynamically changing the slots of the form

        # for instance, if a meal A has drinks then we will create a slot for drinks, 
        # on the other hand, if it doesn't than we won't create a slot for drinks for this form
        additional_slots = get_to_be_slots(slot["meal_type"], slot["meal"])

        # need confirmation is slot using as a flag to trigger confirmation action
        # we will set confirmation true when we have to confirm the change in meal from the customer
        # note that we are putting confirmation at the beginnning of the domain_slots, 
        # so that conformation slot will have the highest priority meaning rasa will ask the user for the confirmation
        # in the nutshell, the order of the slots name in the domain_slots list is the order in which rasa asks questions to fill out the slot 
        if slot["need_confirmation"] == True:
            domain_slots = ["confirmation"] + domain_slots
        
        # this is for dynamic slots based on meals
        # we are moving the slot for comments at the end of the list; domain_slots[-1] is the comment slot
        # note that domain slots are the slots which we specified in the corresponding form in the domain file
        if additional_slots:
            return domain_slots[:-1] + additional_slots + [domain_slots[-1]]
        return domain_slots
        
    # async def extract_extras(self, dispatcher,
    #                          tracker, domain):
        
    #     intent_of_last_user_message = tracker.latest_message['intent'].get('name')
    #     extras = None
        
    #     if intent_of_last_user_message == "chose_extras":
    #        extras = ["lattuce"]

    #     return {"extras": extras}
    

    def validate_confirmation(self, slot_value, 
                              dispatcher, tracker, domain,):
        """
        this method will fill out the slots based on the confirmation, if the user doesn't want to change the meal than the meal will remain previous meal
        alternatively, if the user wants to change that meal then the prev_meal will become new meal

        """
        slots = tracker.current_slot_values()
        intent = tracker.latest_message['intent'].get('name')
        prev_meal = slots.get("prev_meal")
        current_meal = slots.get("meal")

        #  once the confirmation is successfully recognized either affirm (yes) or deny(no), then we set need_confirmation to None
        # so that confirmation doesn't get triggered 
        if intent == "affirm":
            return {"confirmation": None, "prev_meal": current_meal, "need_confirmation": None}
        elif intent == "deny":
            return {"confirmation": None,"meal": prev_meal, "need_confirmation": None}
            
        dispatcher.utter_message(text="sorry I didn't understand you")
        return {"confirmation": None}


    def validate_meal(self, slot_value, 
                      dispatcher, tracker, domain):
        """
        this method will compare the meal specified by the rasa is available in the db or not, 
        and if it is not available than it will change meal slot value back to None, 
        so that customer get asked again to specified the meal
        """
        
        slots = tracker.current_slot_values()
        intent = tracker.latest_message['intent'].get('name')

        # if mistake validation
        if slots["meal"] is None or intent not in ["make_order"]:
            return {"meal": None}

        available_dishes = get_available_dish(slots.get("meal_group", None))
        available_meal_names = [meal_name for _, meal_name in available_dishes]
        
        current_meal = slots.get("meal")
        prev_meal = slots.get("prev_meal")
        
        print("Current meal: ", current_meal)
        print("prev meal: ", prev_meal)

        if current_meal not in available_meal_names:
            # dispatcher.utter_message(text="suggestions: " + " ,".join(available_meal_names))
            dispatcher.utter_message(
                text=f"sorry '{current_meal}' is not available, please choose another meal"
                )
            return {"meal": None}
        
        # we use prev_meal to track the previous added meal and detect the change the meal
        if not prev_meal:
            return {"meal": current_meal, "prev_meal": current_meal}
        
        if prev_meal == current_meal:
            return {"meal": current_meal}

        # if prev_meal and current_meal didn't matched that we fill the  need_confirmation slot with True value, 
        # so that rasa ask for the confirmation
        if prev_meal != current_meal:
            return {"need_confirmation": True, "meal": current_meal}
        
    
    def validate_meal_type(self, slot_value, 
                           dispatcher, tracker, domain):
        """
        it is similar to validate meal except we don't ask for confirmation 
        and verify the meal type with the available meal in the db
        """
        # get available meal type
        slots = tracker.current_slot_values()
        meal_type = slots.get("meal_type")
        meal_name = slots.get("meal")
        available_types = get_available_meal_types(meal_name)

        # validate meal type
        if meal_type in available_types:
            dispatcher.utter_message(
                text=f"great, you have chose {meal_type}"
            )
            return {"meal_type": meal_type}
        else:
            dispatcher.utter_message(
                text="sorry that meal type is not available"
                )
            
            return {"meal_type": None}

    
    def validate_fries_size(
                        self,
                        slot_value: Any,
                        dispatcher: CollectingDispatcher,
                        tracker: Tracker,
                        domain: DomainDict,
                    ) -> Dict[Text, Any]:
        """
        similar to the validate meal type except for fries size
        """
        # get available fries size
        slots = tracker.current_slot_values()
        meal_name = slots.get("meal")
        meal_type = slots.get("meal_type")
        fries_size = slots.get("fries_size")
        available_fries_size = get_available_fries_size(meal_type, meal_name)

        # validate fries size
        if fries_size in available_fries_size:
            dispatcher.utter_message(text=f"you have selected {fries_size} fries size")
            return {"fries_size": fries_size}
        else:
            dispatcher.utter_message(
                text="sorry that fries size is not available, please choose another size"
                )
            dispatcher.utter_message(text="suggestions: "+" ,".join(available_fries_size))
            return {"fries_size": None}


    def validate_drink(
                        self,
                        slot_value: Any,
                        dispatcher: CollectingDispatcher,
                        tracker: Tracker,
                        domain: DomainDict,
                    ) -> Dict[Text, Any]:
        """
        simiar to the validate meal type except for the drink
        """
        
        # get available drinks
        slots = tracker.current_slot_values()
        meal_type = slots.get("meal_type")
        meal_name = slots.get("meal")
        drink = slots.get("drink")
        available_drinks = get_available_drinks(meal_type, meal_name)

        # validate available drinks
        if drink in available_drinks:
            dispatcher.utter_message(text=f"you have selected {drink} for a drink")
            return {"drink": drink}
        else:
            dispatcher.utter_message(text=f"sorry that {drink} is not available")
            return {"drink": None, "drink_type": None}


    def validate_drink_type(
                        self,
                        slot_value: Any,
                        dispatcher: CollectingDispatcher,
                        tracker: Tracker,
                        domain: DomainDict,
                    ) -> Dict[Text, Any]:
        """
        similar to the validate meal type except for the drink type
        """
        # get available drink types
        slots = tracker.current_slot_values()
        meal_type = slots.get("meal_type")
        meal_name = slots.get("meal")
        drink = slots.get("drink")
        drink_type = slots.get("drink_type")
        available_drink_types = get_available_drink_type(meal_type, meal_name, drink)

        # validate drink types
        if drink_type in available_drink_types:
            dispatcher.utter_message(text=f"you have selected {drink_type} {drink}")
            return {"drink_type": drink_type}
        else:
            dispatcher.utter_message(text=f"sorry {drink_type} {drink}, is not available")
            return {"drink_type": None}
        

    def validate_extras(
                        self,
                        slot_value: Any,
                        dispatcher: CollectingDispatcher,
                        tracker: Tracker,
                        domain: DomainDict,
                    ) -> Dict[Text, Any]:
        """
        similar to the validate meal except for the extras
        !!! under construction !!!
        """

        # if the intention is deny then set extras slot with "NO"
        intent = tracker.latest_message['intent'].get("name")
        if intent == "deny":
            return {"extras": ["NO"]}

        # get available extras
        slot = tracker.current_slot_values()
        available_extras = get_available_extras(slot["meal_type"], slot["meal"])
        # print("available extras", available_extras)

        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! VALIDATION HASN"T BEEN IMPLEMENTED YET !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        # get extras from entity
        entities = tracker.latest_message["entities"]
        extras = []
        for entity in entities:
            if entity["entity"] == "item" and entity["group"] == "extra":
                extras.append(entity["value"])
        
        # print("Extras :", extras)
        
        if not extras:
            dispatcher.utter_message(text="unable to extract extras")
            dispatcher.utter_message(
                text="please write all the extras by including 'extra' keyword at the beginning"
                )
            return {"extras": None}
        return {"extras": extras}

