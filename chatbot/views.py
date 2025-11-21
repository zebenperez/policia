from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from agents.llmendpoints import IA_LLM_ENDPOINTS
import requests
from policia.settings import IA_LLM_URL

@csrf_exempt
@require_POST
def chatbot_api(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        session_key = request.session.session_key
        
        # Aquí tu lógica del chatbot
        bot_response = generate_response(user_message)
        
        # Guardar en base de datos si quieres persistencia
        # save_conversation(session_key, user_message, bot_response)
        return JsonResponse({
            'response': bot_response,
            'status': 'success'
        })
        
    except Exception as e:
        return JsonResponse({
            'response': 'Lo siento, ha ocurrido un error.',
            'status': 'error'
        })

def generate_response(user_message):
    # Lógica simple de respuesta - puedes expandir esto
    user_message = user_message.lower()
    
    responses = {
        'hola': '¡Hola! ¿En qué puedo ayudarte hoy?',
        'adiós': '¡Hasta luego! Que tengas un buen día.',
        'gracias': '¡De nada! Estoy aquí para ayudarte.',
        'servicios': 'Ofrecemos desarrollo web, apps móviles y consultoría.',
        'precios': 'Puedes contactarnos para una cotización personalizada.',
        'contacto': 'Puedes escribirnos a info@empresa.com o llamar al +1234567890.'
    }
    
    for keyword, response in responses.items():
        if keyword in user_message:
            return response
    
    return "No estoy seguro de entender. ¿Podrías reformular tu pregunta?"

def chatbot_view(request):
    return render(request, 'chatbot/chatbot.html')

@csrf_exempt
@require_POST
def upload_file(request):
    try:
        uploaded_file = request.FILES['file']
        report_id = request.POST.get('report_id', '')
        upload_url = IA_LLM_URL + IA_LLM_ENDPOINTS["upload_expte"].format(uuid=report_id)
        # requests with Bearer token if needed
        headers = {
            "Authorization": f"Bearer aaaa-bbbb-cccc-dddd"  # Replace with actual token if needed
        }
        response = requests.post(upload_url, files={'file': uploaded_file}, data={'name': report_id}, headers=headers, verify=False, timeout=120)
        
        # Aquí tu lógica para manejar el archivo
        
        return JsonResponse({
            'status': 'success'
        })
        
    except Exception as e:
        return JsonResponse({
            'file_url': '',
            'status': 'error'
        })


