from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_cors import CORS
from openai import OpenAI
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# In-memory storage
conversation_logs = []

# Load customer configurations
def load_customers():
    try:
        with open('customers.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "demo": {
                "name": "AI Chatbot Demo",
                "color": "#6366f1",
                "bot_name": "Eric"
            }
        }

CUSTOMERS = load_customers()

def simulate_api_call(action):
    """Simulate API integrations for demo purposes"""
    if "order" in action.lower() or "status" in action.lower():
        return {
            "type": "order_status",
            "order_id": "DEMO-2024-5678",
            "status": "Shipped",
            "tracking": "TRK987654321",
            "estimated_delivery": "2-4 business days"
        }
    elif "product" in action.lower() or "price" in action.lower():
        return {
            "type": "product_info",
            "products": [
                {"name": "Product Alpha", "price": "$49.99", "stock": "In stock"},
                {"name": "Product Beta", "price": "$79.99", "stock": "Low stock"},
                {"name": "Product Gamma", "price": "$129.99", "stock": "Pre-order"}
            ]
        }
    elif "booking" in action.lower() or "appointment" in action.lower():
        return {
            "type": "booking",
            "available_slots": ["10:00 AM", "2:00 PM", "4:30 PM"],
            "date": "Tomorrow"
        }
    return None

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    try:
        data = request.json
        customer_id = data.get('customer_id', 'demo')
        user_message = data.get('message', '')
        conversation_history = data.get('history', [])
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Get customer config
        customer = CUSTOMERS.get(customer_id, CUSTOMERS['demo'])
        bot_name = customer.get('bot_name', 'Eric')
        
        # Check if message is a file upload
        if "uploaded a file" in user_message.lower() or "📎" in user_message:
            file_response = """Great! I can see you uploaded a file! 📎

In a DEMO, I'm showing file upload capability. In a real implementation:

• I would analyze images with AI vision
• Extract text from PDFs automatically  
• Process documents and data files
• Store files securely in cloud storage

This feature is perfect for:
• Support tickets with screenshots
• Document verification
• Invoice processing
• Image-based product searches

What else would you like to test?"""
            
            conversation_logs.append({
                "customer_id": customer_id,
                "timestamp": datetime.now().isoformat(),
                "user": user_message,
                "bot": file_response
            })
            
            return jsonify({
                'message': file_response,
                'success': True
            })
        
        # Check if message triggers API simulation
        api_response = simulate_api_call(user_message)
        api_context = ""
        if api_response:
            api_context = f"\n\n[SIMULATED API RESPONSE - Include this in your answer naturally]:\n{json.dumps(api_response, indent=2)}\n"
        
        # System prompt for PURE DEMO bot
        system_prompt = f"""You are {bot_name}, an AI chatbot DEMO/SHOWCASE.

CRITICAL: You are a TECHNOLOGY DEMONSTRATION. You show what AI chatbots can do, NOT a real business bot.

YOUR PURPOSE:
Show potential clients what an AI chatbot can do for THEIR business by demonstrating features with dummy/fake data.

DEMO FEATURES TO SHOWCASE:
1. **Multi-language support** - Respond in the SAME language the user uses (English, Norwegian, Spanish, etc.)
2. **Good formatting** - Use bullets, line breaks, clear structure
3. **API Integration simulation** - Show how bots connect to real systems
4. **Smart conversations** - Context-aware, helpful, professional

DEMO SCENARIOS:

**If asked about products/prices:**
"I'm a DEMO bot showing AI chatbot capabilities! 🤖

In a real implementation, I would fetch live data from your product database. Here's an example:

• Product Alpha: $49.99 (In stock)
• Product Beta: $79.99 (Low stock)  
• Product Gamma: $129.99 (Pre-order)

Which product interests you?"

**If asked about order status:**
"Let me demonstrate an API integration... ✨

📦 [Simulated order check]
Order: DEMO-2024-5678
Status: Shipped
Tracking: TRK987654321
Delivery: 2-4 business days

In production, this would connect to YOUR actual order system!"

**If asked about booking/appointments:**
"I can show appointment booking! 📅

Available times (demo data):
• 10:00 AM
• 2:00 PM
• 4:30 PM

In a real system, I'd check your calendar and book instantly!"

**If asked what you can do:**
"I'm a chatbot DEMO showing what's possible! 

I can demonstrate:
• Customer support automation
• Product recommendations
• Order tracking
• Appointment booking
• Multi-language support (try asking in another language!)
• File uploads
• System integrations

What would you like to test?"

RULES:
- ALWAYS make it clear this is DEMO/simulated data
- Respond in the user's language automatically
- Keep responses SHORT (2-4 paragraphs max)
- Use good formatting (bullets, emojis, line breaks)
- Show enthusiasm about the technology
- NEVER mention specific companies or websites
- Focus on CAPABILITIES, not specific business info

{api_context}
"""

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        for msg in conversation_history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})
        
        # Call OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=400
        )
        
        bot_message = response.choices[0].message.content
        
        # Log conversation
        conversation_logs.append({
            "customer_id": customer_id,
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "bot": bot_message
        })
        
        return jsonify({
            'message': bot_message,
            'success': True
        })
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/config/<customer_id>', methods=['GET'])
def get_config(customer_id):
    """Get customer configuration"""
    customer = CUSTOMERS.get(customer_id, CUSTOMERS['demo'])
    return jsonify({
        'name': customer['name'],
        'color': customer['color'],
        'bot_name': customer['bot_name'],
        'welcome_message': f"👋 Hi! I'm {customer['bot_name']} - an AI chatbot DEMO.\n\nI showcase what chatbots can do:\n\n• 24/7 customer support\n• Product information\n• Order tracking\n• Multi-language support\n• API integrations\n\nWhat would you like to test?"
    })

@app.route('/admin', methods=['GET'])
def admin_panel():
    """Simple admin panel"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chatbot Admin</title>
        <style>
            body { font-family: sans-serif; padding: 40px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            h1 { color: #6366f1; }
            .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }
            .stat-card { background: #6366f1; color: white; padding: 20px; border-radius: 8px; text-align: center; }
            .stat-card h3 { margin: 0; font-size: 36px; }
            .stat-card p { margin: 10px 0 0 0; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #f0f0f0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 AI Chatbot Admin Panel</h1>
            
            <div class="stats">
                <div class="stat-card">
                    <h3>""" + str(len(conversation_logs)) + """</h3>
                    <p>Demo Conversations</p>
                </div>
                <div class="stat-card">
                    <h3>100%</h3>
                    <p>Uptime</p>
                </div>
                <div class="stat-card">
                    <h3>DEMO</h3>
                    <p>Mode</p>
                </div>
            </div>
            
            <h2>Recent Demo Interactions</h2>
            <table>
                <tr>
                    <th>Time</th>
                    <th>User Message</th>
                    <th>Bot Response</th>
                </tr>
                """ + "".join([f"""
                <tr>
                    <td>{log['timestamp'][:19]}</td>
                    <td>{log['user'][:60]}...</td>
                    <td>{log['bot'][:60]}...</td>
                </tr>
                """ for log in conversation_logs[-10:][::-1]]) + """
            </table>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'mode': 'demo'})

@app.route('/')
def home():
    return send_from_directory('../frontend', 'landing.html')

@app.route('/widget.html')
def widget():
    return send_from_directory('../frontend', 'widget.html')

@app.route('/intake')
def intake_form():
    return send_from_directory('../frontend', 'intake-form.html')

@app.route('/submit-intake', methods=['POST'])
def submit_intake():
    """Handle intake form submission and send email"""
    try:
        data = request.json
        
        # Format email content
        email_content = f"""
NEW CHATBOT INQUIRY
===================

BUSINESS INFORMATION:
- Company: {data.get('companyName', 'N/A')}
- Business Type: {data.get('businessType', 'N/A')}
- Website: {data.get('website', 'N/A')}
- Company Size: {data.get('companySize', 'N/A')}
- Monthly Visitors: {data.get('monthlyVisitors', 'N/A')}

CONTACT INFORMATION:
- Name: {data.get('contactName', 'N/A')}
- Email: {data.get('email', 'N/A')}
- Phone: {data.get('phone', 'N/A')}
- Role: {data.get('role', 'N/A')}

CHATBOT REQUIREMENTS:
- Use Cases: {', '.join(data.get('useCases', [])) if data.get('useCases') else 'N/A'}
- Languages: {data.get('languages', 'N/A')}
- Integrations: {', '.join(data.get('integrations', [])) if data.get('integrations') else 'N/A'}
- Specific Features: {data.get('specificFeatures', 'N/A')}

CURRENT SITUATION:
- Current Solution: {data.get('currentSolution', 'N/A')}
- Pain Points: {data.get('painPoints', 'N/A')}
- Budget: {data.get('budget', 'N/A')}
- Timeline: {data.get('timeline', 'N/A')}

ADDITIONAL:
- Additional Info: {data.get('additionalInfo', 'N/A')}
- Heard About Us: {data.get('hearAbout', 'N/A')}
"""
        
        # Send email via SendGrid
        message = Mail(
            from_email='erico.andersen@outlook.com',
            to_emails='eric.andersen.ai@outlook.com',
            subject=f'New Chatbot Inquiry - {data.get("companyName", "Unknown Company")}',
            plain_text_content=email_content
        )
        
        try:
            sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
            response = sg.send(message)
            print(f"Email sent! Status code: {response.status_code}")
        except Exception as e:
            print(f"Error sending email: {e}")
            # Still save to file as backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(f'intake_submission_{timestamp}.txt', 'w', encoding='utf-8') as f:
                f.write(email_content)
        
        return jsonify({
            'success': True,
            'message': 'Form submitted successfully!'
        })
        
    except Exception as e:
        print(f"Error processing intake form: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)