# Python program to translate
# speech to text and text to speech


import speech_recognition as sr
import pyttsx3 
from main import *

# Initialize the recognizer 
r = sr.Recognizer() 

# Function to convert text to
# speech
def speak_text(command):
    
    # Initialize the engine
    engine = pyttsx3.init()
    engine.say(command) 
    engine.runAndWait()
    
def main_speech_to_text():
    # Loop infinitely for user to
    # speak
    idx = 1
    combined = re.compile(
        r"\b("
            r"next|forward|advance|"
            r"previous|prev|last|back|before|"
            r"repeat|again|say (?:that|it) again|"
            r"first step|start|begin"
        r")\b"
    )

    while(1):    
        
        # Exception handling to handle
        # exceptions at the runtime
        try:
            
            # use the microphone as source for input.
            with sr.Microphone() as source2:
                handled = False
                # wait for a second to let the recognizer
                # adjust the energy threshold based on
                # the surrounding noise level 
                r.adjust_for_ambient_noise(source2, duration=0.2)
                
                #listens for the user's input 
                audio2 = r.listen(source2)
                
                # Using google to recognize audio
                query = r.recognize_google(audio2)
                query = query.lower()

                if (query == "stop" or query == "quit" or query == "exit"):
                    break

                # print(query)
                if combined.search(query):
                    handled, idx, output = handle_step_query(query, recipe_data, idx, True)
                    if handled:
                        speak_text(output)
                        continue
                else:
                    if not handled:
                        if (contains_vague_term(query)):
                            handled, output = handle_vague_query(query, idx, True)
                            # print("vague: " + output + ":")

                    if not handled:
                        handled, output = handle_temp_query(query)
                        # print(output)
                    
                    if not handled:
                        handled, output = handle_substitution_query(query, idx, True)
                        # print("sub: " + output + ":")

                    if not handled:
                        handled, idx, output = handle_step_query(query, recipe_data, idx, True)
                        # print("step: " + output + ":")

                    if not handled:
                        handled, output = handle_info_query(query, True, idx)
                        # print("info: " + output + ":")
                    
                    if not handled:
                        output = "Sorry, I didn't understand that. Please try again."
                        handled = True
                        # slow_print("Sorry, I didn't understand that. Please try again.")

                    if handled:
                        print(output)
                        speak_text(output)
                        continue
                        
        except sr.RequestError as e:
            print("Could not request results {0}".format(e))
            
        except sr.UnknownValueError:
            print("unknown error occurred")

if __name__ == "__main__":
    startup_base()
    slow_print("Would you like to interact with this recipe?")
    yes_or_no = input(" y/n : ")
    yes_or_no = yes_or_no.strip()
    if yes_or_no.lower() in ['y', 'yes', 'sure', 'yeah']:
        slow_print("Would you like to use speech to text (microphone required)?")
        yes_or_no = input(" y/n : ")
        yes_or_no = yes_or_no.strip()
        if yes_or_no.lower() in ['y', 'yes', 'sure', 'yeah']:
            main_speech_to_text()
        elif yes_or_no.lower() in ['n', 'no', 'nah', 'nope']:
            query_handler()
        else:
            print("Invalid input. Please enter 'y' or 'n'.")
    elif yes_or_no.lower() in ['n', 'no', 'nah', 'nope']:
        slow_print("Alright! Enjoy your cooking!")
    else:
        print("Invalid input. Please enter 'y' or 'n'.")

    print("Thanks for using our recipe helper!")