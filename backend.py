import boto3, os, json
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

load_dotenv("/Users/a1436985/Documents/POCs/14 - Reciept Settlement/.env")
client = boto3.client("bedrock-runtime", aws_access_key_id=os.getenv("aws_access_key"), aws_secret_access_key=os.getenv("aws_secret_access_key"), region_name="us-east-1")
memory = MemorySaver()
model = ChatBedrock(
    model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    client=client
)

def extraction(image: str):
    """Extract Entities in the image which will be related to hotel receipt"""
    with open(f"Receipts_images/{image}", 'rb') as file:
        image_bytes = file.read()
    messages = [
        {
            "role": "user",
            "content": [
                {"text": "Extract the information as entities from the image provided."},
                {"image": {"format": "png", "source": {"bytes": image_bytes}}}
            ]
        }
    ]

    response = client.converse(
        modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        messages=messages,
    )
    response_text = response["output"]["message"]["content"][0]["text"]
    return json.dumps({"image_entities": response_text})

def validate_with_form(context: str, form_data: str):
    """Validate the form_data with the extracted_data and the details will be related to hotel"""
    messages = [
        {
            "role": "user",
            "content": [
                {"text":f"Check this context with form data and give me a summarized response"},
                {"text": f"Extracted_data: {context}"},
                {"text": f"Form_data: {form_data}"}
            ]
        }
    ]

    response = client.converse(
        modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        messages=messages,
    )
    response_text = response["output"]["message"]["content"][0]["text"]
    # return json.dumps({"image_entities": response_text})
    return response_text

def validate_with_contract(summary: str):
    """Validate the summary against the contract and tell me whether the claim can be valid or not according to the contract only if the claim_type is Hotel."""
    with open("contract.txt", "rb") as file:
        content = file.read()
    messages = [
        {
            "role": "user",
            "content": [
                {"text": f"Summary: {summary}"},
                {"text": f"Contract: {content}"}
            ]
        }
    ]

    response = client.converse(
        modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        messages=messages,
    )
    response_text = response["output"]["message"]["content"][0]["text"]
    # return json.dumps({"image_entities": response_text})
    return response_text

@app.route("/Form-data", methods=["POST"])
def receive_form_data():
    if request.method == "POST":
        try:
            name = request.form["name"]
            claim_type = request.form["claim_type"]
            claim_amount = request.form["claim_amt"]
            file = request.files["receipt"].filename

            print(name, claim_type, claim_amount, file)      
            context = extraction(file)   
            form_data = {"name":name, "claim_type":claim_type, "claim_amount":claim_amount}
            summary = validate_with_form(context, form_data)
            validation = validate_with_contract(summary)


            to_display = f" **Name**: {name} \n **Claims Type**: {claim_type} \n **Amount**: {claim_amount}"
            
            # return {"Under_Review":summary, "Under_Processing": validation, "Claim_Submitted":to_display}

            return {"Under_Review":summary, "Under_Processing": validation, "Claim_Submitted":to_display}
        
        except Exception as e:
            return jsonify(
                {
                    "status": f"Bad request - {e}",
                    "response": 400
                }
            )
        
if __name__ == "__main__":
    app.run(debug=True,port=5050)