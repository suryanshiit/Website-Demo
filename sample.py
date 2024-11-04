from pymongo import MongoClient

mongo_uri = 'mongodb+srv://suryanshkgp:m3$JviM$d*X32cB@cluster0.lgvfa.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
try:
    client = MongoClient(mongo_uri)
    db = client['sensor_data']
    collection = db['readings']
    data = list(collection.find())
    print("Data retrieved successfully:", data[:5])  # Print the first entry for verification
    client.close()
except Exception as e:
    print("Failed to connect to MongoDB:", e)
