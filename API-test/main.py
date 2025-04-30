from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

API_KEY = "xxx"
MANAGER_IO_API_BASE = "xxx"
REQUIRED_FIELDS = ['name', 'email', 'address', 'phone']

HEADERS = {
    "Content-Type": "application/json",
    "X-API-KEY": API_KEY
}


# -- Making sure the customer has inputted correct data --

def validate_required_fields(data):
    missing_fields = [field for field in REQUIRED_FIELDS if field not in data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")


# -- Creating a customer --
def create_customer(data):
    customer_payload = {
        "name": data.get("name"),
        "email": data.get("email"),
        "billing_address": data.get("address"),
        "phone": data.get("phone")
    }

    response = requests.post(f"{MANAGER_IO_API_BASE}/customers", json=customer_payload, headers=HEADERS)

    if response.status_code == 201:
        return response.json().get("id")  # Returns the specific ID for the created customer
    else:
        raise Exception(f"Customer creation failed: {response.status_code} - {response.text}")


# -- Creating a sales quote --
def create_sales_quote(customer_id, data):
    quote_info = {
        "customer_id": customer_id,
        "date": "2025-04-30",
        "due_date": "2025-05-15",
        "items": [
            {
                "description": "Climbing Membership",
                "quantity": 1,
                "unit_price": 50.00
            }
        ],
        "notes": "Auto-generated quotation from Fluent Forms"
    }

    response = requests.post(f"{MANAGER_IO_API_BASE}/sales-quotes", json=quote_info, headers=HEADERS)

    if response.status_code == 201:
        return response.json().get("id")  # Returns the specific ID for the created sales quote
    else:
        raise Exception(f"Sales quote creation failed: {response.status_code} - {response.text}")


# -- Sending email to customer --

def send_sales_quote_email(quote_id, recipient_email):
    email_payload = {
        "sales_quote_id": quote_id,
        "to": recipient_email,
        "subject": "Your Sales Quote from Just Climb",
        "body": "Dear Customer,\n\nPlease find your sales quote attached.\n\nBest regards,\nJust Climb"
    }

    response = requests.post(f"{MANAGER_IO_API_BASE}/email-template-for-sales-quote", json=email_payload,
                             headers=HEADERS)

    if response.status_code == 200:
        return True
    else:
        raise Exception(f"Failed to send sales quote email: {response.status_code} - {response.text}")


# -- Running the functions --

@app.route("/webhook", methods=["POST"])
def handle_webhook():
    print("🚀 Webhook hit!")  # Confirms communication between Fluent Forms & Flask
    try:
        data = request.get_json()
        if not data:
            raise ValueError("No JSON data received")

        validate_required_fields(data)

        customer_id = create_customer(data)
        quote_id = create_sales_quote(customer_id, data)

        send_sales_quote_email(
            quote_id=quote_id,
            recipient_email=data['email']
        )

        return jsonify({"status": "success", "quote_id": quote_id}), 200

    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
