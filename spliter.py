import sys
import re
from moviepy.editor import *
import json
import os
import requests
import boto3

#test

movieId = sys.argv[1]
movieFileName = sys.argv[2]
subFileName = sys.argv[3]
bucketName = sys.argv[4]
aws_access_key_id = sys.argv[5]
aws_secret_access_key = sys.argv[6]
serverUrl = sys.argv[7]

ec2Number = os.environ.get("EMP_NO")

try :
    telegram_chat_url = f"https://api.telegram.org/bot6370445519:AAETeQENUJGL1Lg9jws2rtCeJ-SsUwjdudI/sendMessage?chat_id=6507981466&text={movieId}_{movieFileName}_담당직원{ec2Number}호: 프로세스 시작"
    telegram_chat_url_RES = requests.post(telegram_chat_url)

    print("movieId: ",movieId)
    print("movieFileName: ",movieFileName)
    print("subFileName: ",subFileName)
    print("bucketName: ",bucketName)
    print("aws_access_key_id: ",aws_access_key_id)
    print("aws_secret_access_key: ",aws_secret_access_key)
    print("serverUrl: ",serverUrl)


    if not os.path.exists("movie"):
        os.mkdir("movie")
    if not os.path.exists("sub"):
        os.mkdir("sub")
    if not os.path.exists("splited-movie"):
        os.mkdir("splited-movie")
    if not os.path.exists("splited-subtitles"):
        os.mkdir("splited-subtitles")

    # S3 클라이언트 생성
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

    # S3에 저장된 자막 파일을 다운로드
    s3.download_file(bucketName, subFileName, f"sub/{subFileName}")

    with open(f"sub/{subFileName}", "r", encoding='UTF-8') as f:
            sub = f.readlines()

    for i in range(len(sub)):
        if "\n" in sub[i]:
            sub[i] = sub[i].strip()

    result = []

    item = []
    for i in range(len(sub)):
        if sub[i] == "":
            result.append(item)
            item = []
        elif '[' in sub[i]:
            continue
        else:
            subItem = re.sub(r'\([^)]*\)', '', sub[i])
            item.append(subItem)

    for i in range(len(result)):
        result[i].pop(0)

    result = [[i[0], ' '.join(i[1:])] for i in result]

    for i in reversed(range(len(result))):
        if result[i][1] == "":
            result.remove(result[i])

    subtitleList = []

    for i in range(len(result)):
        first_element = result[i][0].split(" --> ")[0]
        first_element = first_element.split(":")
        first_hour = int(first_element[0])
        first_minute = int(first_element[1])
        first_second, first_millisecond = map(int, first_element[2].split(","))
        first_total_seconds = first_hour * 3600 + first_minute * 60 + first_second + first_millisecond / 1000

        second_element = result[i][0].split(" --> ")[1]
        second_element = second_element.split(":")
        second_hour = int(second_element[0])
        second_minute = int(second_element[1])
        second_second, second_millisecond = map(int, second_element[2].split(","))
        second_total_seconds = second_hour * 3600 + second_minute * 60 + second_second + second_millisecond / 1000

        subtitleList.append([first_total_seconds, second_total_seconds, result[i][1]])

    for i in range(len(subtitleList)):
        subtitleList[i].insert(0, i+1)

    with open(f"splited-subtitles/{subFileName}.json", "w", encoding='UTF-8') as f:
        # f.write(str(subtitleList))
        json.dump(subtitleList, f, ensure_ascii=False, indent=4)

    # S3에 저장된 영화파일을 다운로드
    s3.download_file(bucketName, movieFileName, f"movie/{movieFileName}")

    with open(f"splited-subtitles/{subFileName}.json", "r", encoding='UTF-8') as f:
            sub = f.read()

    sub = json.loads(sub)

    print(type(sub))

    clip = VideoFileClip(f"movie/{movieFileName}")
    print("clip")
    telegram_chat_url = f"https://api.telegram.org/bot6370445519:AAETeQENUJGL1Lg9jws2rtCeJ-SsUwjdudI/sendMessage?chat_id=6507981466&text={movieId}_{movieFileName}_담당직원{ec2Number}호: 분할 시작"
    telegram_chat_url_RES = requests.post(telegram_chat_url)
    for ii, e in enumerate(sub):
        print("split start")
        line_url = f"{serverUrl}/line?movieId={movieId}&lineOrder={e[0]}"
        line_url_res = requests.get(line_url)
        print(line_url_res)
        lineResJson =  json.loads(line_url_res.text)
        suffix = lineResJson["fileSuffix"]
        temp = clip.subclip(e[1], e[2])
        temp.write_videofile(
            f"splited-movie/{suffix}.mp4", fps=24)
        
        # 업로드할 파일 경로와 S3 버킷 이름 설정
        local_file_path = f"splited-movie/{suffix}.mp4"
        s3_bucket_name = "every-lines-movies" # 버킷 이름
        s3_object_key = f'public/{suffix}.mp4'  # S3 버킷 내에서 파일의 경로와 이름

        # 파일 업로드
        s3.upload_file(local_file_path, s3_bucket_name, s3_object_key, ExtraArgs={"ACL":"public-read"})
        try:
            os.remove(local_file_path)
        except:
            raise Exception("업로드 실패")
            
        print(movieId, ii+1)
except Exception as e:
    telegram_chat_url = f"https://api.telegram.org/bot6370445519:AAETeQENUJGL1Lg9jws2rtCeJ-SsUwjdudI/sendMessage?chat_id=6507981466&text={movieId}_{movieFileName}_담당직원{ec2Number}호: 오류 발생"
    telegram_chat_url_RES = requests.post(telegram_chat_url)
    print(e)
finally:
    telegram_chat_url = f"https://api.telegram.org/bot6370445519:AAETeQENUJGL1Lg9jws2rtCeJ-SsUwjdudI/sendMessage?chat_id=6507981466&text={movieId}_{movieFileName}_담당직원{ec2Number}호: 완료"
    telegram_chat_url_RES = requests.post(telegram_chat_url)