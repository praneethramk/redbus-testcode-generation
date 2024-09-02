from flask import Flask, request, render_template
from PIL import Image
import io
import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Get the API key from environment variables
api_key = os.getenv("API_KEY")

# Initialize the Flask application
app = Flask(__name__)

# Configure the Google AI API using the environment variable
genai.configure(api_key=api_key)

# Set up the model with the updated model name
generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 2048,
}

safety_settings = [
    {
        "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
        "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    },
    {
        "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    },
    {
        "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    },
    {
        "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    },
]

model = genai.GenerativeModel(model_name="gemini-1.5-flash",
                              generation_config=generation_config,
                              safety_settings=safety_settings)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/describe', methods=['POST'])
def describe_testing_instructions():
    context = request.form.get('context', '')
    images = request.files.getlist('screenshots')
    
    image_parts = []
    for img in images:
        image = Image.open(img)
        # Convert the image to bytes
        with io.BytesIO() as output:
            image.save(output, format="PNG")
            image_bytes = output.getvalue()
        image_parts.append({
            "mime_type": "image/png",
            "data": image_bytes
        })

    prompt = create_prompt(context, len(images))
    
    response = model.generate_content([prompt] + image_parts)
    
    formatted_test_cases = format_test_cases(response.text)
    return render_template('output.html', test_cases=formatted_test_cases)

def create_prompt(context, num_images):
    # Example Test Case 1: Source, Destination, and Date Selection
    example_test_case_1 = (
        "Test Case ID: TC001\n"
        "Test Scenario: Source, Destination, and Date Selection\n"
        "Test Case Description: Verify that the user can select the source, destination, and date on the Red Bus app.\n"
        "Pre-conditions: User must be logged into the app, and the app should be installed and opened. GPS location services should be enabled.\n"
        "Test Steps:\n"
        "1. Launch the Red Bus app.\n"
        "2. Navigate to the 'Search Buses' section.\n"
        "3. Enter 'Mumbai' in the source location field.\n"
        "4. Enter 'Pune' in the destination location field.\n"
        "5. Select the date '15th December 2024' for travel.\n"
        "6. Click on 'Search'.\n"
        "Expected Result: The app should display available buses for the selected route and date.\n"
        "Post-conditions: The selected route and date should be saved for later reference in the app's history or recent searches.\n"
        "Actual Result: The app successfully displays available buses for the selected route and date as expected.\n"
        "Status: Pass\n"
        "Priority: High\n"
        "Comments: Verify if the search results are sorted by default or allow the user to sort. Also, check if the app displays any error messages if no buses are available."
    )

    # Example Test Case 2: Bus Selection
    example_test_case_2 = (
        "Test Case ID: TC002\n"
        "Test Scenario: Bus Selection\n"
        "Test Case Description: Verify that the user can select a bus from the list of available buses for the chosen route and date.\n"
        "Pre-conditions: The user should have completed the source, destination, and date selection.\n"
        "Test Steps:\n"
        "1. After performing the search, review the list of available buses.\n"
        "2. Select a bus based on the time of departure.\n"
        "3. Review the details of the selected bus including amenities, photos, and user reviews.\n"
        "4. Confirm the bus selection.\n"
        "Expected Result: The selected bus details should be displayed correctly, and the user should be able to proceed to the seat selection.\n"
        "Post-conditions: The selected bus should be highlighted or marked as selected.\n"
        "Actual Result: The bus details were correctly displayed, and the user was able to proceed to the seat selection.\n"
        "Status: Pass\n"
        "Priority: High\n"
        "Comments: Ensure that the bus list is scrollable and that filters, if applied, work correctly."
    )

    # Example Test Case 3: Seat Selection
    example_test_case_3 = (
        "Test Case ID: TC003\n"
        "Test Scenario: Seat Selection\n"
        "Test Case Description: Verify that the user can select a seat on the selected bus.\n"
        "Pre-conditions: The user should have selected a bus.\n"
        "Test Steps:\n"
        "1. After selecting the bus, navigate to the seat selection screen.\n"
        "2. Choose an available seat.\n"
        "3. Confirm the seat selection.\n"
        "Expected Result: The selected seat should be marked as booked, and the user should be able to proceed to the payment.\n"
        "Post-conditions: The seat should no longer be available for others to book.\n"
        "Actual Result: The seat was successfully selected and marked as booked.\n"
        "Status: Pass\n"
        "Priority: High\n"
        "Comments: Verify that the seat map is correctly displayed and that the UI is responsive."
    )

    prompt = (
        "You are an expert software tester tasked with generating detailed manual test cases "
        "for the Red Bus mobile app based on a sequence of screenshots. Each test case should include the following elements and always start with TC001:\n\n"
        "1. Test Case ID: A unique identifier for each test case.\n"
        "2. Test Scenario: A high-level overview of the functionality being tested.\n"
        "3. Test Case Description: A detailed description of what the test case will validate.\n"
        "4. Pre-conditions: Steps or conditions that must be met before executing the test case.\n"
        "5. Test Steps: A numbered list of clear, step-by-step instructions for performing the test.\n"
        "6. Test Data: Specific data inputs required to execute the test.\n"
        "7. Expected Result: The expected outcome if the system behaves as expected.\n"
        "8. Post-conditions: The expected state of the system after the test is executed.\n"
        "9. Actual Result: The actual outcome observed after executing the test observed on the screenshot comparing with expected result.\n"
        "10. Status: The result of the test (e.g., Pass/Fail).\n"
        "11. Priority: The importance of the test case (High, Medium, Low).\n"
        "12. Comments: Include additional insights, potential edge cases, or UI/UX observations.\n\n"
        "The screenshots provided represent different stages of user interaction with the app. "
        "Analyze the sequence of screenshots to understand the flow of the application and generate test cases accordingly. "
        f"The number of screenshots provided is {num_images}. "
        "Break down complex features into multiple, specific test cases to cover all possible functionality visible in the screenshots.\n"
        "Focus on the following core features:\n"
        "- Source, Destination, and Date Selection: The user chooses where they're going, where they’re starting, and when.\n"
        "- Bus Selection: Display and choose from available buses.\n"
        "- Seat Selection: Let the user pick their seat on the selected bus.\n"
        "- Pick-up and Drop-off Point Selection: Choose where the journey starts and ends.\n"
        
        "- Offers: Highlight any discounts or promotions available.\n"
        "- Filters: Options for sorting buses by time, price, or other criteria.\n"
        "- Bus Information: Details about the bus, such as amenities, photos, and user reviews.\n"
        "Here are some example test cases:\n\n"
        f"{example_test_case_1}\n\n"
        f"{example_test_case_2}\n\n"
        f"{example_test_case_3}\n\n"
        "Now, generate additional test cases based on the provided screenshots and context. "
        "Ensure each test case includes a detailed, step-by-step guide on how to test each functionality, focusing on both core and bonus features."
    )
    if context:
        prompt += f"\nAdditional Context: {context}\n"
    return prompt


def format_test_cases(test_cases):
    # Remove any unwanted characters like '*' and '#' if present
    cleaned_cases = test_cases.replace("*", "").replace("#", "")
    
    # Replace newlines and add HTML tags for formatting
    formatted_cases = cleaned_cases.replace("\n", "<br>").replace("Test Case ID:", "<strong>Test Case ID:</strong>")
    formatted_cases = formatted_cases.replace("Test Scenario:", "<strong>Test Scenario:</strong>")
    formatted_cases = formatted_cases.replace("Test Case Description:", "<strong>Test Case Description:</strong>")
    formatted_cases = formatted_cases.replace("Pre-conditions:", "<strong>Pre-conditions:</strong>")
    formatted_cases = formatted_cases.replace("Test Steps:", "<strong>Test Steps:</strong>")
    formatted_cases = formatted_cases.replace("Test Data:", "<strong>Test Data:</strong>")
    formatted_cases = formatted_cases.replace("Expected Result:", "<strong>Expected Result:</strong>")
    formatted_cases = formatted_cases.replace("Post-conditions:", "<strong>Post-conditions:</strong>")
    formatted_cases = formatted_cases.replace("Actual Result:", "<strong>Actual Result:</strong>")
    
    # Adding input fields for Status and Comments
    formatted_cases = formatted_cases.replace("Status:", "</p><p><strong>Status:</strong><br><select name='status'><option value=''>Select Status</option><option value='Pass'>Pass</option><option value='Fail'>Fail</option></select>")
    formatted_cases = formatted_cases.replace("Comments:", "</p><p><strong>Comments:</strong><br><textarea name='comments'></textarea>")
    
    formatted_cases = formatted_cases.replace("Priority:", "<strong>Priority:</strong>")
    
    return formatted_cases


@app.route('/submit_results', methods=['POST'])
def submit_results():
    # Capture the submitted statuses and comments from the form
    statuses = request.form.getlist('status')
    comments = request.form.getlist('comments')
    
    # Combine the results with the test cases
    test_cases = request.form.get('test_cases')
    submitted_case = {
        "test_case": test_cases,
        "status": statuses[0],
        "comments": comments[0]
    }
    
    return render_template('final_output.html', submitted_case=submitted_case)

if __name__ == '__main__':
    app.run(debug=True)
