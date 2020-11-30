from seleniumwire import webdriver  # Import from seleniumwire
import time
import requests
import json

from user import *
import settings
import parse_json
import dataPy

# pre-setup for dev
# if devFlag set import login creds from credentials.py
# ADD "credentials.py" to gitignore
# Never upload raw id and pwd to repository
if settings.devFlag == True:
    import credentials

    user = User(credentials.sid, credentials.id, credentials.pw)
else:
    user = User(settings.sid, settings.id, settings.pw)


# login
def login(i):
    driver.get("https://icampus.skku.edu/login")
    driver.find_element_by_css_selector("#userid").send_keys(credentials.id[i])
    driver.find_element_by_css_selector(
        "#password").send_keys(credentials.pw[i])
    driver.find_element_by_css_selector("#btnLoginBtn").click()
    time.sleep(1)


# function for extracting user auth token should be written
def getToken(driver):
    pass


# function for automatically loading user's attending classes and canvas UID should be written
def getClassesAndUid(user):
    
    """
    load classes and canvas uid
    
    By analysis canvas API we found out that favorites classes[this semester class]
    Can be aquired by GET /api/v1/ysers/self/favorites/courses
    The server returns JSON in a while loop therefore stripping loop is necessary res.text[9:]
    
    코로나로 인해 전체 온라인 강의가 되면서 현재 학기에 수강하는 과목들만 추출해 내는 부분이 고민이었다.
    이전에는 그래서 해당하는 교과목 아이디(학수번호랑 다름)을 직접 사용자가 넣어야 불필요한 강의를 받지 않았다.(시간 감소 측면에서 아니면 너무 오래걸림)
    그런데 학교 측에서 "즐겨찾기" 목록을 이번학기에 수강하는 목록으로 바꿔줘서 canvas가 즐겨 찾기를 불러오는 방법을 분석하여 재현했다.

    canvas REST API는 static page에서 추가 설명할 예정..
    """
    
    url = 'https://canvas.skku.edu/api/v1/users/self/favorites/courses'
    # no bearer only normandy
    res = requests.get(url, cookies=user.cookies)
    result = json.loads(res.text[9:])

    classes = []
    classDatas = {}
    uid = result[0]["enrollments"][0]["user_id"]
    for cls in result:
        """
        기능 개선1 part 받지 않을 강의 선택 이곳에 기능 구현 바람
        """
        if (cls["id"] in settings.banlist):
            continue
        classes.append(cls["id"])
        name = cls["name"]
        classDatas[cls["id"]] = {
            "code": name[name.find("_") + 1:name.find("(")].replace("_", "-"),
            "name": name[:name.find("_")],
            "prof": name[name.rfind("(") + 1:name.rfind(")")]
        }

    return uid, classes, classDatas

# function for integrating selenium with getToken() and getClassesAndUid() for loading User data should be written
# This function will act as program entry point
def loadUser(driver, user):
    # 1.login with selenium
    
    # 2.extract auth token

    # 3.load classes and canvas uid
    user.uid, user.classes, user.classDatas = getClassesAndUid(user)
    pass

# After getClassesAndUid() is implemented, previous loadClass() function will be deprecated
def loadClass():
    driver.get("https://canvas.skku.edu/courses")
    classList = driver.find_element_by_css_selector(
        "#my_courses_table > tbody")
    classTags = driver.find_elements_by_tag_name("a")
    lists = []
    for cl in classTags:
        if (cl.get_attribute("title") and ("안전교육" not in cl.get_attribute("title"))):
            lists.append(cl.get_attribute("href").split("/")[-1])

    return lists


def getDB(classNum):
    url = "https://canvas.skku.edu/courses/" + classNum + "/external_tools/1"
    del driver.requests
    driver.get(url)
    classCode = driver.find_element_by_css_selector(
        "#breadcrumbs > ul > li:nth-child(2) > a > span").text
    classC = classCode[classCode.find(
        "_") + 1:classCode.find("(")].replace("_", "-")
    classN = classCode[:classCode.find("_")]
    classT = classCode[classCode.rfind("(") + 1:classCode.rfind(")")]
    print("")
    print(classC, classN, classT)
    db = driver.wait_for_request("allcomponents_db?").response.body
    week_data = driver.wait_for_request("sections_db?").response.body
    parse_json.parseClass(db.decode("utf-8"),
                          week_data.decode("utf-8"), classC, classN, classT)
    # print(parsed_db)


parse_json.loadCompleted()

# Create a new instance of the Firefox driver
driver = webdriver.Chrome()

login(0)
classList1 = loadClass()
# upper codes will be replaced by loadUser() after fully implemented

for cl in classList1:
    getDB(cl)

parse_json.writeCompleted()
