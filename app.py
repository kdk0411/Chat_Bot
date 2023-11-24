from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import ObjectId
from Bot import exit_conditions, help
from BotLib_fc.Main_Text_Classification_Model import Text_Classification as tc
import json

mongo_connect = "mongodb+srv://hongpc0099:hoz26064247@worklog.dxlbirn.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(mongo_connect)
db = client["WorkLog"]
collection = db["Info"]


app = Flask(__name__)

Corpus_File = "chat.txt"

text = "6월 34일, 서울시 강남구 서초동 30-5, 36,000원."
sub = "기타 내용."

Update_Data = {
            "time": None,
            "date": None,
            "address": None,
            "pay": None
            }    

# 프로젝트 주요 텍스트 분류 코드
@app.route('/classify_text', methods=['POST'])
def classify_text():
    try:
        data = request.get_json()
        text = data.get('text')

        if not text:
            return jsonify({"message": "Text is empty"}), 400
        
        elif text in exit_conditions:
            if text == "q":
                print(f"{text}? Ok, I understand. Program exit")
            else:
                print(f"{text}합니다.")
        elif text.lower() == 'help':
            help()
        else:
            classifier = tc(text, None)
            time = classifier.Time_Pattern()
            date = classifier.Date_Pattern()
            address = classifier.Address_Pattern()
            pay = classifier.Pay_Pattern()
        
            if time is not None:
                Update_Data["time"] = time
            if date is not None:
                Update_Data["date"] = date
            if address is not None:
                Update_Data["address"] = address
            if pay is not None:
                Update_Data["pay"] = pay

            if time is not None or date is not None or address is not None or pay is not None:
                print("당신이 작성한 내용이 이것이 맞습니까?:", Update_Data)
                
                collection.insert_one(Update_Data)
                
                # Initialize Update_Data to an empty state
                Update_Data = {
                    "time": None,
                    "date": None,
                    "address": None,
                    "pay": None
                }
                return jsonify({"message": "데이터가 성공적으로 MongoDB에 저장되었습니다."}), 201  

    except Exception as e:
        return jsonify({"message": f"데이터를 MongoDB에 저장하는 중 오류 발생: {e}"}), 500

        
@app.errorhandler(Exception)
def handle_error(error):
    # 오류 발생 시 서버가 종료되지 않도록 처리
    app.logger.error(f"An error occurred: {str(error)}")
    return jsonify({"message": "서버에서 오류가 발생했습니다."}), 500
        
@app.route('/insert', methods=['POST'])
def insert_Info():
    try:
        data = request.get_json()
        if data:
            year = data.pop("year", None)  # "year" 키를 삭제하고 해당 값을 변수에 저장
            month = data.pop("month", None)  # "month" 키를 삭제하고 해당 값을 변수에 저장
            day = data.pop("day", None)  # "day" 키를 삭제하고 해당 값을 변수에 저장
            hour = data.pop("hour", None)  # "hour" 키를 삭제하고 해당 값을 변수에 저장
            minute = data.pop("minute", None)  # "minute" 키를 삭제하고 해당 값을 변수에 저장
            date_time = datetime(year, month, day, hour, minute)
            data["date_time"] = date_time 
            # 중복 데이터 확인: name, age, address 모두 동일한 경우 중복으로 처리
            # existing_data = collection.find_one({"name": data["name"], "age": data["age"], "address": data["address"], "cost": data["cost"]})
            # if existing_data:
            #     print("중복 데이터를 입력하였습니다.")
            #     return jsonify({"message": "이미 저장된 데이터 입니다."}), 400
            # else:
            collection.insert_one(data)
            return jsonify({"message": "데이터가 성공적으로 MongoDB에 저장되었습니다."}), 201
        else:
            print("JSON 형식 데이터가 제공되지 않았습니다.")
            return jsonify({"message": "유효한 JSON 데이터가 제공되지 않았습니다."}), 400
    except Exception as e:
        return jsonify({"message": f"데이터를 MongoDB에 저장하는 중 오류 발생: {e}"}), 500
    

@app.route('/select', methods=['POST'])
def select_Info():
    try:
        data = request.get_json()
        
        query = {"$and": []}

        if data.get("name"):
            query["$and"].append({"name": data["name"]})
        if data.get("age"):
            query["$and"].append({"age": data["age"]})
        if data.get("address"):
            query["$and"].append({"address": data["address"]})
        if data.get("start_date") and data.get("end_date"):
            start_date = datetime.strptime(data["start_date"], "%Y-%m-%d")
            end_date = datetime.strptime(data["end_date"], "%Y-%m-%d") + timedelta(days=1)
            query["$and"].append({"date_time": {"$gte": start_date, "$lte": end_date}})

        if not query["$and"]:
            return jsonify({"message": "적어도 하나의 검색 조건을 제공해야 합니다."}), 400
        
        # 입력한 데이터 중 하나라도 일치하는 데이터 DB에 있는지 확인
        result = collection.find(query)
        
        count = collection.count_documents(query)
        #입력한 데이터 DB에 있는지 확인
        if count > 0:
            result_list = list(result)
            for item in result_list:
            # ObjectId를 문자열로 변환
                item['_id'] = str(item['_id'])
                
                # date_time 필드를 원하는 형식으로 포맷
                item['date_time'] = item['date_time'].strftime("%a, %d %b %Y %H:%M")
                #보여주지 않아도 되는 데이터 제거
                # item.pop('_id', None)
                # item.pop('cost', None)
            print(result_list)
            print("데이터를 찾아서 전송했습니다.")
            return jsonify(result_list)
        else:
            return jsonify({"message": "해당 데이터가 존재하지 않습니다."}), 400
    except Exception as e:
        return jsonify({"message": f"데이터를 MongoDB에 읽어오던 중 오류 발생: {e}"}), 500
    

@app.route('/delete', methods=['DELETE'])
def delete_Info():
    try:
        data = request.get_json()
        if "id" in data:
            # year = data.pop("year", None)  # "year" 키를 삭제하고 해당 값을 변수에 저장
            # month = data.pop("month", None)  # "month" 키를 삭제하고 해당 값을 변수에 저장
            # day = data.pop("day", None)  # "day" 키를 삭제하고 해당 값을 변수에 저장
            # hour = data.pop("hour", None)  # "hour" 키를 삭제하고 해당 값을 변수에 저장
            # minute = data.pop("minute", None)  # "minute" 키를 삭제하고 해당 값을 변수에 저장
            # date_time = datetime.datetime(year, month, day, hour, minute)
            # data["date_time"] = date_time
            # existing_data = collection.count_documents({"date_time": data["date_time"], "name": data["name"], "age": data["age"], "cost": data["cost"]})
            document_id = ObjectId(data["id"])
            existing_data = collection.count_documents({"_id": document_id})
            if existing_data > 0:
                # collection.delete_one({"date_time": data["date_time"], "name": data["name"], "age": data["age"], "cost": data["cost"]})
                collection.delete_one({"_id": document_id})
                print("DB에서 데이터를 삭제하였습니다.")
                return jsonify({"message": "성공적으로 삭제되었습니다."})
            else:
                print("존재하지 않는 데이터입니다.")
                return jsonify({"message": "존재하지 않는 데이터 입니다."}), 400
    except Exception as e:
        return jsonify({"message": f"데이터를 삭제하던 중 오류 발생: {e}"}), 500
    

@app.route('/update', methods=['POST'])
def update_Info():
    try:
        data = request.get_json()
        if "id" in data:
            document_id = ObjectId(data["id"])
            existing_data = collection.count_documents({"_id": document_id})
            if existing_data > 0:
                update_data = data.get("update_data", {})
                if update_data:
                    # $set 오퍼레이터를 사용하여 필드를 업데이트
                    collection.update_one({"_id": document_id}, {"$set": update_data})
                    print("DB에서 데이터를 업데이트하였습니다.")
                    return jsonify({"message": "성공적으로 업데이트되었습니다."})
                else:
                    return jsonify({"message": "업데이트할 데이터가 제공되지 않았습니다."}), 400
            else:
                print("존재하지 않는 데이터입니다.")
                return jsonify({"message": "존재하지 않는 데이터 입니다."}), 400
    except Exception as e:
        return jsonify({"message": f"데이터를 수정하던 중 오류 발생: {e}"}), 500
    
if __name__ == '__main__':
    app.run(debug=True)