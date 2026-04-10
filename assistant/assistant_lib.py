from policia.settings import IA_LLM_URL
from policia.commons import get_or_none, get_param, show_exc
from gestion.models import Employee, Report, ReportAudio, ReportMsg
from .llmendpoints import IA_LLM_ENDPOINTS
from .common_lib import *

import requests, random


'''
    ASSISTANT METHOD
'''
def manage_audios(report, headers):
    audios = report.audios.all()
    transcriptions = []
    audios_to_upoload = []
    for audio in audios:
        log2file(f"Audio ID: {audio.id}, processed: {audio.processed}, upload_id: {audio.upload_id}, text length: {len(audio.text)}")
        if audio.processed and len(audio.upload_id) < 5:
            transcriptions.append(audio.text)
            audios_to_upoload.append(audio)

    transcriptions = list(reversed(transcriptions))
    vector_store_id = report.vector_id
    if transcriptions != []:
        tmp_file_path = f"/tmp/{report.uuid}_{audios.first().id}_transcriptions.txt"
        with open(tmp_file_path, "w") as f:
            f.writelines(transcriptions)
        with open(tmp_file_path, "rb") as f:
            # upload_url = IA_LLM_URL + IA_LLM_ENDPOINTS["upload_expte"].format(uuid=report.uuid)
            upload_url = IA_LLM_URL + IA_LLM_ENDPOINTS["openai-upload-expte"].format(uuid=report.uuid)
            # requests with Bearer token if needed

            response = requests.post(upload_url,files={'file':f},data={'name':report.uuid},headers=headers,verify=False,timeout=120)
            vector_store_id = response.json().get("vector_store_id", None)
            report.vector_id = vector_store_id
            # report.file_id = response.json().get("file_id", None)
            upload_id = response.json().get("file_id", "")
            for audio in audios_to_upoload:
                audio.upload_id = upload_id
                audio.save()
            report.save()

            if response.status_code != 200:
                return f"Error uploading data to microservicio: {response.text}"
                #return JsonResponse({'error': f"Error uploading data to microservicio: {response.text}"}, status=response.status_code)
        
        if response.status_code != 200:
            return f"Error uploading data to microservicio: {response.text}"
            #return JsonResponse({'error': f"Error uploading data to microservicio: {response.text}"}, status=response.status_code)
    return ""

#def get_current_report(user, report_id):
def get_current_report(user, mode):
    #report = get_or_none(Report, report_id)
    #if report is None:
    #current_report = Report.get_today_by_emp(user.employee)
    current_report = Report.get_current_by_mode(user.employee, mode)
    report = Report.objects.create(employee=user.employee, mode=mode) if current_report == None else current_report
    return report

def response_to_context(datas): 
    #try:
    return {
        'message': datas.get("answer", random.choice(ERRORS_ANSWER)), 
        'priority': datas.get("priority", "low"), 
        'advice': datas.get("summary", ""), 
        'citations': datas.get("citations", ""), 
        'intensity': datas.get("intensity", ""), 
        'critical_state': datas.get("critical_state", ""), 
        'structural_framework': datas.get("structural_framework", ""), 
        'structural_question': datas.get("structural_question", ""), 
        'decision': datas.get("decision", ""), 
        'posible_action': datas.get("posible_action", ""), 
        'basis_for_action': datas.get("basis_for_action", ""), 
        'factual_reason': datas.get("factual_reason", ""), 
        'facts_list': datas.get("facts_list", ""), 
        'code': datas.get("code", ""), 
        'mode': datas.get("mode", ""), 
        'status': 'success'
    }
    #except Exception as e:
    #    log2file(f"Error in response_to_context: {show_exc(e)}")
    #    return {'message': random.choice(ERRORS_ANSWER), 'status': 'success'}

def get_report_messages_ia(report):
    import json 

    msg_list = []
    if report.conversation_id != "":
        chat_url = IA_LLM_URL + IA_LLM_ENDPOINTS["openai-chat-conversation"].format(uuid=report.conversation_id)
        params = {}
        headers = { "Authorization": f"Bearer aaaa-bbbb-cccc-dddd" }
        response = requests.get(chat_url, params=params, headers=headers, verify=False, timeout=1200)

        datas = json.loads(response.json())
        for msg in datas:
            for item in msg['content']:
                text = item['text']
                try:
                    parsed = json.loads(text)
                    m = response_to_context(parsed)
                    msg_list.append({'type': "system", 'msg':m})
                except json.JSONDecodeError:
                    msg_list.append({'type': "user", 'msg':text})
    #print(msg_list)
    return msg_list

def get_report_messages(report):
    import json 
    print("--3--")

    msg_list = []
    for msg in report.messages.all():
        try:
            parsed = json.loads(msg.text.replace("'", "\""))
            m = response_to_context(parsed)
            message = m
        except json.JSONDecodeError as e:
            message = msg.text
        msg_list.append({'message':message})
    return msg_list
 
