import requests
import json

# Test the API endpoint
try:
    response = requests.get('http://localhost:8000/api/ipos')
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API is working! Found {len(data)} IPOs")
        if data:
            print("\n📊 Sample IPO data:")
            sample = data[0]
            for key, value in sample.items():
                print(f"  {key}: {value}")
        else:
            print("❌ No IPO data found in database")
    else:
        print(f"❌ API returned status code: {response.status_code}")
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to server. Server may not be running.")
    print("💡 Start the server with: python main.py")
except Exception as e:
    print(f"❌ Error testing API: {e}")